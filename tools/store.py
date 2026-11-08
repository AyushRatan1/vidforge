"""Supabase store used by GitHub Actions (service-role key) and the CLI.

Plain PostgREST over HTTPS, no SDK. Two env vars switch it on: SUPABASE_URL and SUPABASE_SERVICE_KEY.
When they are missing every call is a no-op that returns None/{} so local runs keep working.

    from tools import store
    store.load_settings_into_env()          # anthropic_api_key -> ANTHROPIC_API_KEY, etc.
    store.upsert("videos", {"id": rid, "status": "making"})
    store.job_update(job_id, status="running", stage="Research")
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.parse
import urllib.request

# settings.key -> environment variable the rest of the code reads
SETTING_ENV = {
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "youtube_api_key": "YOUTUBE_API_KEY",
    "youtube_client_id": "YOUTUBE_CLIENT_ID",
    "youtube_client_secret": "YOUTUBE_CLIENT_SECRET",
    "youtube_refresh_token": "YOUTUBE_REFRESH_TOKEN",
    "ig_access_token": "IG_ACCESS_TOKEN",
    "ig_user_id": "IG_USER_ID",
    "pexels_api_key": "PEXELS_API_KEY",
    "pixabay_api_key": "PIXABAY_API_KEY",
    "github_token": "VF_GITHUB_TOKEN",
    "github_repo": "VF_GITHUB_REPO",
    "runner": "VF_RUNNER",
    "models": "VF_MODELS",                # JSON {"writer": "claude-opus-5-5", ...}
    "brand_name": "VF_BRAND_NAME",        # channel name for series badges
    "brand_handle": "VF_HANDLE",          # @handle printed on every frame
    "brand_hashtag": "VF_BRAND_TAG",      # one brand hashtag added to every post
}


def enabled() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"))


def _req(method: str, table: str, params: dict | None = None, body=None, prefer: str = "") -> list | dict | None:
    if not enabled():
        return None
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/" + table
    if params:
        url += "?" + urllib.parse.urlencode(params, safe="*,().:")
    key = os.environ["SUPABASE_SERVICE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "Accept": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else []
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise RuntimeError(f"Supabase {method} {table} failed: {e.code} {detail}") from None


def select(table: str, **filters) -> list:
    """select("videos", status="eq.ready", order="created_at.desc", limit=10)"""
    return _req("GET", table, {"select": filters.pop("select", "*"), **filters}) or []


def one(table: str, **filters) -> dict:
    rows = select(table, limit=1, **filters)
    return rows[0] if rows else {}


def upsert(table: str, row: dict, on_conflict: str = "id") -> dict:
    out = _req("POST", table, {"on_conflict": on_conflict}, row, prefer="resolution=merge-duplicates,return=representation")
    return out[0] if out else {}


def update(table: str, match: dict, patch: dict) -> list:
    params = {k: f"eq.{v}" for k, v in match.items()}
    return _req("PATCH", table, params, patch, prefer="return=representation") or []


def insert(table: str, rows: list[dict]) -> list:
    return _req("POST", table, None, rows, prefer="return=representation") or []


# ----------------------------------------------------------------------------- settings
def settings() -> dict:
    return {r["key"]: r["value"] for r in select("settings")}


def load_settings_into_env(override: bool = False) -> dict:
    """Put every saved key into the environment so the rest of the code just reads env vars.
    GitHub secrets already in the environment win unless override=True."""
    s = settings()
    for k, env in SETTING_ENV.items():
        v = s.get(k)
        if v and (override or not os.environ.get(env)):
            os.environ[env] = v
    return s


def set_setting(key: str, value: str) -> None:
    upsert("settings", {"key": key, "value": value}, on_conflict="key")


# ----------------------------------------------------------------------------- videos and jobs
def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def video_upsert(rid: str, **fields) -> dict:
    return upsert("videos", {"id": rid, **fields})


def video_update(rid: str, **fields) -> None:
    update("videos", {"id": rid}, fields)


def job_update(job_id: str | None, **fields) -> None:
    if job_id:
        update("jobs", {"id": job_id}, fields)


def job_create(job_id: str, kind: str = "make", options: dict | None = None, video_id: str | None = None, **fields) -> dict:
    row = {"id": job_id, "kind": kind, "status": "queued", "options": options or {}, **fields}
    if video_id:
        row["video_id"] = video_id
    return upsert("jobs", row)


def run_url() -> str | None:
    """Link to the current GitHub Actions run, or None outside Actions."""
    repo, rid = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_RUN_ID")
    if repo and rid:
        return f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{rid}"
    return None


def release_urls(rid: str, repo: str | None = None) -> dict:
    """GitHub release page and asset download links for a library video (tag video-<rid>)."""
    repo = repo or os.environ.get("GITHUB_REPOSITORY") or os.environ.get("VF_GITHUB_REPO")
    if not repo:
        return {}
    base = f"https://github.com/{repo}/releases"
    return {"release_url": f"{base}/tag/video-{rid}",
            "video_url": f"{base}/download/video-{rid}/final.mp4",
            "thumb_url": f"{base}/download/video-{rid}/thumbnail.jpg"}


def mark_failed(rid: str | None, job_id: str | None, message: str) -> None:
    """Called by the workflow's failure step: video and job become 'failed' with the error text."""
    message = (message or "failed")[:500]
    if rid:
        try:
            video_upsert(rid, status="failed", error=message)
        except Exception as e:  # never let bookkeeping hide the real failure
            print(f"store: could not mark video {rid} failed: {e}")
    if job_id:
        try:
            job_update(job_id, status="failed", error=message, stage="failed")
        except Exception as e:
            print(f"store: could not mark job {job_id} failed: {e}")


def mark_done(rid: str | None, job_id: str | None) -> None:
    if job_id:
        try:
            job_update(job_id, status="done", stage="done", video_id=rid)
        except Exception as e:
            print(f"store: could not mark job {job_id} done: {e}")


def video_from_folder(out: str, rid: str, options: dict | None = None) -> dict:
    """Build the videos row from a finished output folder (summary.json, meta.json, facts.json, qa.json)."""
    def load(name, default):
        p = os.path.join(out, name)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default
    s, meta, pub = load("summary.json", {}), load("meta.json", {}), load("published.json", {})
    facts = [f for f in load("facts.json", {}).get("facts", []) if isinstance(f, dict)]
    qa, spec = load("qa.json", {}), load("spec.json", {})
    row = {"id": rid, "title": s.get("title") or spec.get("title"), "language": s.get("language") or spec.get("language"),
           "format": s.get("format"), "aspect": spec.get("aspect"), "duration": s.get("duration"),
           "qa_score": s.get("qa_score"), "usd": s.get("usd"), "meta": meta,
           "sources": [{"claim": f.get("claim"), "url": f.get("source_url"), "title": f.get("source_title")} for f in facts[:12]],
           "qa": {"score": qa.get("score"), "pass": qa.get("pass"),
                  "issues": [i.get("problem") for i in qa.get("issues", []) if i.get("severity") != "minor"][:6]}}
    if options:
        row["options"] = options
        row["topic"] = options.get("topic") or None
        row["niche"] = options.get("niche")
    if pub:
        row["published"] = pub
        yt, ig = pub.get("youtube") or {}, pub.get("instagram") or {}
        row.update({"youtube_id": yt.get("id"), "youtube_url": yt.get("url"),
                    "instagram_id": ig.get("id"), "instagram_url": ig.get("url")})
        if yt.get("url") or ig.get("url"):
            row["status"] = "posted"
    return {k: v for k, v in row.items() if v is not None}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1:2]
    if cmd == ["settings"]:
        print(json.dumps({k: (v[:6] + "..." if v else "") for k, v in settings().items()}, indent=1))
    elif cmd == ["env"]:
        s = load_settings_into_env()
        print(f"loaded {len(s)} settings into the environment")
    elif cmd == ["fail"]:
        # python tools/store.py fail <rid> <job_id> "<message>"   (empty strings are allowed)
        args = sys.argv[2:] + ["", "", ""]
        if not enabled():
            print("store: Supabase not configured, nothing to mark")
        else:
            mark_failed(args[0] or None, args[1] or None, args[2] or "failed")
            print(f"marked failed: video={args[0] or '-'} job={args[1] or '-'}")
    elif cmd == ["done"]:
        # python tools/store.py done <rid> <job_id>
        args = sys.argv[2:] + ["", ""]
        if enabled():
            mark_done(args[0] or None, args[1] or None)
        print(f"marked done: job={args[1] or '-'}")
    elif cmd == ["video-status"]:
        # python tools/store.py video-status <rid> <status> [json fields]
        args = sys.argv[2:]
        if enabled() and len(args) >= 2:
            extra = json.loads(args[2]) if len(args) > 2 else {}
            video_upsert(args[0], status=args[1], **extra)
        print(f"video {args[0] if args else '-'} -> {args[1] if len(args) > 1 else '-'}")
    else:
        print("usage: python tools/store.py settings | env | fail <rid> <job_id> <message> | done <rid> <job_id> | "
              "video-status <rid> <status> [json]")
