"""Post a finished video folder to YouTube and/or Instagram using credentials from environment variables
(GitHub Actions secrets). Writes/merges published.json in the folder.

    YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN   -> YouTube
    IG_ACCESS_TOKEN (+ optional IG_USER_ID)                          -> Instagram Reels
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

from publish import instagram as ig_api
from publish import youtube as yt_api


def _load(out, name, default=None):
    p = os.path.join(out, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def publish(out: str, youtube=False, instagram=False, privacy="public", publish_at=None, overrides=None) -> dict:
    youtube_on, instagram_on = bool(youtube), bool(instagram)
    spec = _load(out, "spec.json", {})
    meta = _load(out, "meta.json", {}) or {}
    ov = overrides or {}
    if ov.get("youtube"):
        meta.setdefault("youtube", {}).update({k: v for k, v in ov["youtube"].items() if v})
    if ov.get("instagram"):
        meta.setdefault("instagram", {}).update({k: v for k, v in ov["instagram"].items() if v})
    video = os.path.join(out, "final.mp4")
    if not os.path.exists(video):
        raise SystemExit(f"no final.mp4 in {out}")
    result = _load(out, "published.json", {}) or {}
    failed = []
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    if youtube_on:
        creds = yt_api.creds_from_env()
        if not creds:
            result["youtube"] = {"error": "YouTube not connected (YOUTUBE_CLIENT_ID / _CLIENT_SECRET / _REFRESH_TOKEN secrets)"}
            failed.append("youtube")
        else:
            try:
                r = yt_api.upload(creds, video, spec, privacy=privacy, publish_at=publish_at,
                                 thumbnail=os.path.join(out, "thumbnail.jpg"), meta=meta.get("youtube"))
                result["youtube"] = {"id": r["id"], "url": r["url"], "privacy": r.get("privacy"),
                                     "publish_at": publish_at, "at": now}
                print(f"   YouTube: {r['url']} ({r.get('privacy')})")
                if r.get("privacy") == "private" and privacy != "private" and not publish_at:
                    print("   note: YouTube locks API uploads to private until your Google project passes the API audit")
            except Exception as e:
                result["youtube"] = {"error": f"{type(e).__name__}: {e}"}
                failed.append("youtube")

    if instagram_on:
        token = os.environ.get("IG_ACCESS_TOKEN", "")
        if not token:
            result["instagram"] = {"error": "Instagram not connected (IG_ACCESS_TOKEN secret)"}
            failed.append("instagram")
        else:
            try:
                uid = os.environ.get("IG_USER_ID") or ig_api.account(token).get("user_id")
                cap = (meta.get("instagram") or {}).get("caption") or ig_api.build_caption(spec)
                r = ig_api.publish_reel(uid, token, video, cap)
                result["instagram"] = {"id": r["id"], "url": r.get("url"), "at": now}
                print(f"   Instagram: {r.get('url')}")
            except Exception as e:
                result["instagram"] = {"error": f"{type(e).__name__}: {e}"}
                failed.append("instagram")

    with open(os.path.join(out, "published.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    for k in failed:
        print(f"   {k} failed: {result[k]['error']}", file=sys.stderr)
    if failed:
        raise SystemExit(1)
    return result

