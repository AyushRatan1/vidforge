"""FastAPI backend + dashboard. Run: python run.py serve  (binds to 127.0.0.1 only)."""
from __future__ import annotations

import base64
import json
import os
import secrets as pysecrets

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response

from agents.formats import FORMATS
from agents.llm import DEFAULT_ROLES, MODELS
from engine.audio import VOICES
from engine.validate import validate
from publish import instagram, youtube

from . import db, jobs

app = FastAPI(title="VidForge")
HERE = os.path.dirname(os.path.abspath(__file__))
PASSWORD = os.environ.get("VIDFORGE_PASSWORD", "")
USER = os.environ.get("VIDFORGE_USER", "admin")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")


@app.middleware("http")
async def basic_auth(request: Request, call_next):
    """HTTP Basic auth for every route when VIDFORGE_PASSWORD is set (required when hosted)."""
    if PASSWORD and request.url.path != "/healthz":
        ok = False
        hdr = request.headers.get("authorization", "")
        if hdr.lower().startswith("basic "):
            try:
                u, _, pw = base64.b64decode(hdr[6:]).decode().partition(":")
                ok = pysecrets.compare_digest(u, USER) and pysecrets.compare_digest(pw, PASSWORD)
            except Exception:
                ok = False
        if not ok:
            return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="VidForge"'})
    return await call_next(request)


@app.get("/healthz")
def healthz():
    return {"ok": True}


def _redirect_uri(request: Request) -> str:
    return f"{PUBLIC_URL}/oauth/youtube/callback" if PUBLIC_URL else str(request.url_for("yt_callback"))
CLIENT_SECRET = os.path.join(db.DATA, "google_client_secret.json")
_oauth_state: dict[str, dict] = {}
sched = BackgroundScheduler(timezone="Asia/Kolkata")


@app.on_event("startup")
def _startup():
    db.init()
    reschedule()
    sched.start()


def reschedule():
    for jb in sched.get_jobs():
        jb.remove()
    for ch in db.channels():
        if ch.get("schedule_enabled") and ch.get("schedule_time"):
            hh, mm = (ch["schedule_time"].split(":") + ["0"])[:2]
            sched.add_job(jobs.autopilot, "cron", args=[ch["id"]], hour=int(hh), minute=int(mm),
                          id=f"auto_{ch['id']}", replace_existing=True)


@app.get("/", response_class=HTMLResponse)
def index():
    return open(os.path.join(HERE, "static", "index.html"), encoding="utf-8").read()


# ---------------------------------------------------------------- meta + settings
@app.get("/api/meta")
def meta():
    return {"models": MODELS, "default_roles": DEFAULT_ROLES, "formats": {k: v["name"] for k, v in FORMATS.items()},
            "voices": sorted(VOICES), "niches": ["space", "science", "tech", "stories", "mythology", "kids", "news", "sports", "general"],
            "google_client_secret": os.path.exists(CLIENT_SECRET)}


@app.get("/api/settings")
def get_settings():
    return db.public_settings()


@app.post("/api/settings")
def post_settings(body: dict = Body(...)):
    for k, v in body.items():
        if k in db.SECRET_KEYS and (v is None or str(v).startswith("••••")):
            continue  # untouched masked secret
        db.set_setting(k, v)
    return db.public_settings()


@app.post("/api/settings/google-client")
async def upload_client_secret(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        j = json.loads(raw)
        assert "web" in j or "installed" in j
    except Exception:
        raise HTTPException(400, "Upload the OAuth client JSON downloaded from Google Cloud Console")
    os.makedirs(db.DATA, exist_ok=True)
    with open(CLIENT_SECRET, "wb") as f:
        f.write(raw)
    os.chmod(CLIENT_SECRET, 0o600)
    return {"ok": True}


@app.get("/api/usage")
def usage():
    tot = {"input_tokens": 0, "output_tokens": 0, "web_searches": 0, "usd": 0.0, "videos": 0}
    for j in db.jobs(500):
        d = (db.job(j["id"]) or {}).get("data", {})
        u = d.get("usage") or {}
        for k in ("input_tokens", "output_tokens", "web_searches", "usd"):
            tot[k] += u.get(k, 0)
        tot["videos"] += 1 if d.get("render") else 0
    tot["usd"] = round(tot["usd"], 2)
    return tot


# ---------------------------------------------------------------- channels
@app.get("/api/channels")
def list_channels():
    return db.channels()


@app.post("/api/channels")
def save_channel(body: dict = Body(...)):
    sec = body.pop("_secrets", None) or {}
    for k in ("connected", "youtube_account", "instagram_account"):
        body.pop(k, None)
    if sec.get("ig_token"):
        try:
            acct = instagram.account(sec["ig_token"])
            sec["ig_user_id"] = sec.get("ig_user_id") or acct.get("user_id")
            sec["ig_username"] = acct.get("username")
        except Exception as e:
            raise HTTPException(400, f"Instagram token check failed: {e}")
    ch = db.save_channel(body, sec)
    reschedule()
    return ch


@app.delete("/api/channels/{cid}")
def delete_channel(cid: str):
    db.delete_channel(cid)
    reschedule()
    return {"ok": True}


# ---------------------------------------------------------------- YouTube OAuth
@app.get("/oauth/youtube/start")
def yt_start(channel_id: str, request: Request):
    if not os.path.exists(CLIENT_SECRET):
        raise HTTPException(400, "Upload your Google OAuth client JSON in Settings first")
    state = pysecrets.token_urlsafe(16)
    redirect = _redirect_uri(request)
    url, verifier = youtube.auth_url(CLIENT_SECRET, redirect, state)
    _oauth_state[state] = {"channel_id": channel_id, "verifier": verifier, "redirect": redirect}
    return RedirectResponse(url)


@app.get("/oauth/youtube/callback", name="yt_callback")
def yt_callback(request: Request, state: str):
    st = _oauth_state.pop(state, None)
    if not st:
        raise HTTPException(400, "OAuth state expired; start again")
    callback = f"{PUBLIC_URL}{request.url.path}?{request.url.query}" if PUBLIC_URL else str(request.url)
    creds = youtube.exchange(CLIENT_SECRET, st["redirect"], state, callback, st["verifier"])
    info = {}
    try:
        info = youtube.channel_info(creds)
    except Exception:
        pass
    ch = db.channel(st["channel_id"])
    db.save_channel(ch, {"youtube_creds": creds, "youtube_account": info.get("title")})
    return RedirectResponse("/#channels")


# ---------------------------------------------------------------- trends + ideas
@app.post("/api/channels/{cid}/scout")
def scout(cid: str, body: dict = Body(default={})):
    try:
        return jobs.run_scout(cid, body.get("notes", ""), int(body.get("n", 8)))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/channels/{cid}/ideas")
def ideas(cid: str):
    return db.ideas(cid)


# ---------------------------------------------------------------- jobs
@app.get("/api/jobs")
def list_jobs():
    return db.jobs()


@app.get("/api/jobs/{jid}")
def get_job(jid: str):
    j = db.job(jid)
    if not j:
        raise HTTPException(404)
    return j


@app.post("/api/jobs")
def create_job(body: dict = Body(...)):
    cid = body["channel_id"]
    if not db.channel(cid):
        raise HTTPException(404, "channel not found")
    spec = body.get("spec")
    if spec:
        errs, _ = validate(spec)
        if errs:
            raise HTTPException(400, "; ".join(errs))
    if not spec and not db.get_setting("anthropic_api_key", ""):
        raise HTTPException(400, "Add your Anthropic API key in Settings first")
    idea = db.idea(body["idea_id"]) if body.get("idea_id") else None
    return {"id": jobs.start_job(cid, idea, body.get("topic", ""), body.get("notes", ""), spec)}


@app.post("/api/jobs/{jid}/revise")
def revise(jid: str, body: dict = Body(...)):
    jobs.revise_job(jid, body["instructions"])
    return {"ok": True}


@app.post("/api/jobs/{jid}/spec")
def put_spec(jid: str, body: dict = Body(...)):
    errs, warns = validate(body)
    if errs:
        raise HTTPException(400, "; ".join(errs))
    db.update_job(jid, data={"spec": body})
    jobs.rerender(jid)
    return {"ok": True, "warnings": warns}


@app.post("/api/jobs/{jid}/rerender")
def rerender(jid: str):
    jobs.rerender(jid)
    return {"ok": True}


@app.post("/api/jobs/{jid}/publish")
def publish(jid: str, body: dict = Body(...)):
    try:
        return jobs.publish(jid, body.get("platforms", ["youtube"]), body.get("privacy", "public"), body.get("publish_at"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"{type(e).__name__}: {e}")


@app.get("/media/{jid}/{name}")
def media(jid: str, name: str):
    if "/" in name or ".." in name:
        raise HTTPException(400)
    path = os.path.join(jobs.OUT, jid, name)
    if not os.path.exists(path):
        raise HTTPException(404)
    return FileResponse(path)
