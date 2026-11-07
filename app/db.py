"""SQLite storage: settings (secrets encrypted at rest), channels, ideas, jobs, publishes."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid

from cryptography.fernet import Fernet

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DATA, "vidforge.db")
KEY_PATH = os.path.join(DATA, "secret.key")
SECRET_KEYS = {"anthropic_api_key", "youtube_api_key", "nasa_api_key"}

_lock = threading.RLock()


def _fernet() -> Fernet:
    os.makedirs(DATA, exist_ok=True)
    if not os.path.exists(KEY_PATH):
        with open(KEY_PATH, "wb") as f:
            f.write(Fernet.generate_key())
        os.chmod(KEY_PATH, 0o600)
    return Fernet(open(KEY_PATH, "rb").read())


def enc(s: str) -> str:
    return _fernet().encrypt(s.encode()).decode() if s else ""


def dec(s: str) -> str:
    try:
        return _fernet().decrypt(s.encode()).decode() if s else ""
    except Exception:
        return ""


def conn():
    os.makedirs(DATA, exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init():
    with _lock, conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS channels (id TEXT PRIMARY KEY, data TEXT, secrets TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS ideas (id TEXT PRIMARY KEY, channel_id TEXT, data TEXT, status TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, channel_id TEXT, idea_id TEXT, status TEXT, stage TEXT,
            progress REAL, data TEXT, error TEXT, created REAL, updated REAL);
        CREATE TABLE IF NOT EXISTS publishes (id TEXT PRIMARY KEY, job_id TEXT, platform TEXT, remote_id TEXT,
            url TEXT, status TEXT, created REAL);
        """)


# ---------------------------------------------------------------- settings
ENV_FALLBACK = {"anthropic_api_key": "ANTHROPIC_API_KEY", "youtube_api_key": "YOUTUBE_API_KEY", "nasa_api_key": "NASA_API_KEY"}


def get_setting(key: str, default=None):
    with _lock, conn() as c:
        r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    if r is not None:
        v = json.loads(r["value"])
        v = dec(v) if key in SECRET_KEYS else v
        if v not in ("", None):
            return v
    if key in ENV_FALLBACK and os.environ.get(ENV_FALLBACK[key]):
        return os.environ[ENV_FALLBACK[key]]
    return default


def set_setting(key: str, value):
    v = enc(value) if key in SECRET_KEYS and value else value
    with _lock, conn() as c:
        c.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (key, json.dumps(v)))


def public_settings() -> dict:
    with _lock, conn() as c:
        rows = c.execute("SELECT key, value FROM settings").fetchall()
    out = {}
    for r in rows:
        v = json.loads(r["value"])
        if r["key"] in SECRET_KEYS:
            plain = dec(v) or os.environ.get(ENV_FALLBACK.get(r["key"], ""), "")
            out[r["key"]] = ("••••" + plain[-4:]) if plain else ""
        else:
            out[r["key"]] = v
    for k, env in ENV_FALLBACK.items():
        if not out.get(k) and os.environ.get(env):
            out[k] = "••••" + os.environ[env][-4:] + " (env)"
    return out


# ---------------------------------------------------------------- channels
def save_channel(data: dict, secrets: dict | None = None) -> dict:
    cid = data.get("id") or uuid.uuid4().hex[:8]
    data["id"] = cid
    with _lock, conn() as c:
        old = c.execute("SELECT secrets FROM channels WHERE id=?", (cid,)).fetchone()
        sec = json.loads(dec(old["secrets"])) if old and old["secrets"] else {}
        if secrets:
            sec.update({k: v for k, v in secrets.items() if v is not None})
        c.execute("INSERT OR REPLACE INTO channels(id, data, secrets, created) VALUES (?, ?, ?, COALESCE((SELECT created FROM channels WHERE id=?), ?))",
                  (cid, json.dumps(data, ensure_ascii=False), enc(json.dumps(sec)), cid, time.time()))
    return data


def channel(cid: str) -> dict | None:
    with _lock, conn() as c:
        r = c.execute("SELECT data FROM channels WHERE id=?", (cid,)).fetchone()
    return json.loads(r["data"]) if r else None


def channel_secrets(cid: str) -> dict:
    with _lock, conn() as c:
        r = c.execute("SELECT secrets FROM channels WHERE id=?", (cid,)).fetchone()
    return json.loads(dec(r["secrets"])) if r and r["secrets"] else {}


def channels() -> list[dict]:
    with _lock, conn() as c:
        rows = c.execute("SELECT id, data FROM channels ORDER BY created").fetchall()
    out = []
    for r in rows:
        d = json.loads(r["data"])
        s = channel_secrets(r["id"])
        d["connected"] = {"youtube": bool(s.get("youtube_creds")), "instagram": bool(s.get("ig_token") and s.get("ig_user_id"))}
        d["youtube_account"] = s.get("youtube_account")
        d["instagram_account"] = s.get("ig_username")
        out.append(d)
    return out


def delete_channel(cid: str):
    with _lock, conn() as c:
        c.execute("DELETE FROM channels WHERE id=?", (cid,))


# ---------------------------------------------------------------- ideas
def add_ideas(cid: str, ideas: list[dict]) -> list[dict]:
    out = []
    with _lock, conn() as c:
        for i in ideas:
            iid = uuid.uuid4().hex[:10]
            i["id"] = iid
            c.execute("INSERT INTO ideas(id, channel_id, data, status, created) VALUES (?, ?, ?, 'new', ?)",
                      (iid, cid, json.dumps(i, ensure_ascii=False), time.time()))
            out.append(i)
    return out


def ideas(cid: str, limit=40) -> list[dict]:
    with _lock, conn() as c:
        rows = c.execute("SELECT id, data, status, created FROM ideas WHERE channel_id=? ORDER BY created DESC LIMIT ?",
                         (cid, limit)).fetchall()
    return [{**json.loads(r["data"]), "id": r["id"], "status": r["status"], "created": r["created"]} for r in rows]


def idea(iid: str) -> dict | None:
    with _lock, conn() as c:
        r = c.execute("SELECT data, status FROM ideas WHERE id=?", (iid,)).fetchone()
    return {**json.loads(r["data"]), "id": iid, "status": r["status"]} if r else None


def set_idea_status(iid: str, status: str):
    with _lock, conn() as c:
        c.execute("UPDATE ideas SET status=? WHERE id=?", (status, iid))


# ---------------------------------------------------------------- jobs
def new_job(cid: str, idea_id: str | None, data: dict) -> str:
    jid = uuid.uuid4().hex[:10]
    now = time.time()
    with _lock, conn() as c:
        c.execute("INSERT INTO jobs(id, channel_id, idea_id, status, stage, progress, data, error, created, updated) "
                  "VALUES (?, ?, ?, 'queued', 'queued', 0, ?, NULL, ?, ?)",
                  (jid, cid, idea_id, json.dumps(data, ensure_ascii=False), now, now))
    return jid


def update_job(jid: str, **kw):
    data = kw.pop("data", None)
    with _lock, conn() as c:
        if data is not None:
            row = c.execute("SELECT data FROM jobs WHERE id=?", (jid,)).fetchone()
            cur = json.loads(row["data"]) if row else {}
            cur.update(data)
            kw["data"] = json.dumps(cur, ensure_ascii=False)
        kw["updated"] = time.time()
        cols = ", ".join(f"{k}=?" for k in kw)
        c.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*kw.values(), jid))


def job(jid: str) -> dict | None:
    with _lock, conn() as c:
        r = c.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if not r:
            return None
        pubs = c.execute("SELECT * FROM publishes WHERE job_id=? ORDER BY created", (jid,)).fetchall()
    d = dict(r)
    d["data"] = json.loads(d["data"] or "{}")
    d["publishes"] = [dict(p) for p in pubs]
    return d


def jobs(limit=60) -> list[dict]:
    with _lock, conn() as c:
        rows = c.execute("SELECT id, channel_id, status, stage, progress, data, error, created, updated FROM jobs "
                         "ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = json.loads(r["data"] or "{}")
        out.append({"id": r["id"], "channel_id": r["channel_id"], "status": r["status"], "stage": r["stage"],
                    "progress": r["progress"], "error": r["error"], "created": r["created"], "updated": r["updated"],
                    "title": (d.get("spec") or {}).get("title") or (d.get("idea") or {}).get("title") or (d.get("idea") or {}).get("topic"),
                    "thumbnail": bool((d.get("render") or {}).get("thumbnail")),
                    "qa_score": (d.get("qa") or {}).get("score")})
    return out


def add_publish(jid: str, platform: str, remote_id: str, url: str, status: str):
    with _lock, conn() as c:
        c.execute("INSERT INTO publishes(id, job_id, platform, remote_id, url, status, created) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (uuid.uuid4().hex[:10], jid, platform, remote_id, url, status, time.time()))


def published_ids(platform: str) -> list[tuple[str, str]]:
    with _lock, conn() as c:
        rows = c.execute("SELECT j.channel_id, p.remote_id FROM publishes p JOIN jobs j ON j.id=p.job_id WHERE p.platform=?",
                         (platform,)).fetchall()
    return [(r[0], r[1]) for r in rows]
