"""Instagram Reels via the Instagram API with Instagram Login (professional account, resumable upload)."""
from __future__ import annotations

import os
import time

import requests

API = "v26.0"
GRAPH = f"https://graph.instagram.com/{API}"
RUPLOAD = f"https://rupload.facebook.com/ig-api-upload/{API}"


def _check(r: requests.Response) -> dict:
    try:
        j = r.json()
    except ValueError:
        r.raise_for_status()
        raise
    if r.status_code >= 400 or "error" in j:
        err = j.get("error", {})
        raise RuntimeError(f"Instagram API error {r.status_code}: {err.get('message', j)}")
    return j


def account(token: str) -> dict:
    return _check(requests.get(f"{GRAPH}/me", params={"fields": "user_id,username,account_type", "access_token": token}, timeout=30))


def publishing_limit(ig_user_id: str, token: str) -> dict:
    return _check(requests.get(f"{GRAPH}/{ig_user_id}/content_publishing_limit",
                               params={"fields": "config,quota_usage", "access_token": token}, timeout=30))


def refresh_token(token: str) -> dict:
    """Long-lived tokens last ~60 days; refresh them before they expire."""
    return _check(requests.get("https://graph.instagram.com/refresh_access_token",
                               params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30))


def build_caption(spec: dict) -> str:
    title = spec.get("title", "").replace("#Shorts", "").replace("#shorts", "").strip()
    tags = " ".join("#" + "".join(ch for ch in t if ch.isalnum()) for t in (spec.get("tags") or [])[:8] if t)
    desc = (spec.get("description") or "").split("\n\n")[0]
    return f"{title}\n\n{desc}\n\n{tags}".strip()[:2150]


def publish_reel(ig_user_id: str, token: str, video_path: str, caption: str, share_to_feed: bool = True,
                 thumb_offset_ms: int = 1500, progress=None) -> dict:
    # 1. container
    c = _check(requests.post(f"{GRAPH}/{ig_user_id}/media", data={
        "media_type": "REELS", "upload_type": "resumable", "caption": caption,
        "share_to_feed": "true" if share_to_feed else "false", "thumb_offset": thumb_offset_ms,
        "access_token": token}, timeout=60))
    cid = c["id"]
    # 2. upload bytes
    size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        _check(requests.post(f"{RUPLOAD}/{cid}", headers={
            "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}, data=f, timeout=600))
    if progress:
        progress(0.5)
    # 3. wait for processing
    for _ in range(60):
        st = _check(requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code,status", "access_token": token}, timeout=30))
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram processing failed: {st.get('status')}")
        time.sleep(5)
    else:
        raise RuntimeError("Instagram processing timed out")
    # 4. publish
    m = _check(requests.post(f"{GRAPH}/{ig_user_id}/media_publish", data={"creation_id": cid, "access_token": token}, timeout=60))
    link = _check(requests.get(f"{GRAPH}/{m['id']}", params={"fields": "permalink", "access_token": token}, timeout=30))
    if progress:
        progress(1.0)
    return {"id": m["id"], "url": link.get("permalink")}
