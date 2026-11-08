"""Daily stats pull: per-video and whole-channel numbers from YouTube and Instagram into Supabase.

    python tools/stats.py          (or: python run.py stats)

YouTube: videos.list part=statistics for every library video with a youtube_id (OAuth creds from the settings
table or YOUTUBE_API_KEY), channels.list mine=true for the channel row, and, when the refresh token carries the
yt-analytics.readonly scope, estimatedMinutesWatched and shares per video from YouTube Analytics.
Instagram (Instagram API with Instagram Login): /{media_id}/insights per Reel and /me for the account.

One platform failing never stops the other; the exit code is 1 only when both failed.
Rows: stats (video_id, platform, day) and channel_stats (platform, day); day is today in IST.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import store  # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")
IG_GRAPH = "https://graph.instagram.com/v26.0"
IG_METRICS = ["views", "likes", "comments", "shares", "saved", "reach"]


def today_ist() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone(IST).date().isoformat()


def _int(v) -> int:
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


# ----------------------------------------------------------------------------- YouTube
def _yt_service():
    from publish.youtube import creds_from_env
    from googleapiclient.discovery import build
    creds_json = creds_from_env()
    if creds_json:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_info(json.loads(creds_json))
        creds.refresh(Request())
        return build("youtube", "v3", credentials=creds, cache_discovery=False), creds
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        return build("youtube", "v3", developerKey=key, cache_discovery=False), None
    raise RuntimeError("YouTube not connected (no OAuth refresh token and no YOUTUBE_API_KEY)")


def _yt_analytics(creds, ids: list[str], day: str) -> dict:
    """{youtube_id: {"watch_time_s": .., "shares": ..}} or {} when Analytics is not reachable (optional)."""
    if creds is None or not ids:
        return {}
    from googleapiclient.discovery import build
    ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    out = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        r = ya.reports().query(ids="channel==MINE", startDate="2000-01-01", endDate=day,
                               metrics="estimatedMinutesWatched,shares", dimensions="video",
                               filters="video==" + ",".join(chunk), maxResults=200).execute()
        cols = [c["name"] for c in r.get("columnHeaders", [])]
        for row in r.get("rows", []):
            d = dict(zip(cols, row))
            out[d.get("video")] = {"watch_time_s": _int(float(d.get("estimatedMinutesWatched") or 0) * 60),
                                   "shares": _int(d.get("shares"))}
    return out


def pull_youtube(videos: list[dict], day: str) -> str:
    vids = [v for v in videos if v.get("youtube_id")]
    yt, creds = _yt_service()
    by_yt = {v["youtube_id"]: v["id"] for v in vids}
    ids = list(by_yt)
    rows = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute()
        for it in r.get("items", []):
            s = it.get("statistics", {})
            rows.append({"video_id": by_yt[it["id"]], "platform": "youtube", "day": day,
                         "views": _int(s.get("viewCount")), "likes": _int(s.get("likeCount")),
                         "comments": _int(s.get("commentCount")), "_yt": it["id"]})
    try:
        extra = _yt_analytics(creds, ids, day)
        for row in rows:
            row.update(extra.get(row["_yt"], {}))
    except Exception as e:  # analytics scope missing or API disabled: not fatal
        print(f"   youtube analytics skipped: {type(e).__name__}: {str(e)[:160]}")
    for row in rows:
        row.pop("_yt", None)
        store.upsert("stats", row, on_conflict="video_id,platform,day")
    channel = ""
    if creds is not None:
        r = yt.channels().list(part="statistics", mine=True).execute()
        items = r.get("items", [])
        if items:
            s = items[0].get("statistics", {})
            store.upsert("channel_stats", {"platform": "youtube", "day": day, "followers": _int(s.get("subscriberCount")),
                                           "views": _int(s.get("viewCount")), "videos": _int(s.get("videoCount"))},
                         on_conflict="platform,day")
            channel = f", channel {s.get('subscriberCount')} subs"
    return f"youtube: {len(rows)} videos{channel}"


# ----------------------------------------------------------------------------- Instagram
def _ig_get(path: str, token: str, **params) -> dict:
    import requests
    r = requests.get(f"{IG_GRAPH}/{path}", params={**params, "access_token": token}, timeout=30)
    try:
        j = r.json()
    except ValueError:
        r.raise_for_status()
        raise
    if r.status_code >= 400 or "error" in j:
        raise RuntimeError((j.get("error") or {}).get("message") or f"HTTP {r.status_code}")
    return j


def ig_insights(media_id: str, token: str, metrics: list[str] | None = None) -> dict:
    """Insights for one Reel; a metric the API rejects is dropped and the call retried."""
    metrics = list(metrics or IG_METRICS)
    while metrics:
        try:
            j = _ig_get(f"{media_id}/insights", token, metric=",".join(metrics))
        except RuntimeError as e:
            msg = str(e).lower()
            bad = [m for m in metrics if m in msg]
            if not bad:
                raise
            metrics = [m for m in metrics if m not in bad]
            continue
        out = {}
        for item in j.get("data", []):
            vals = item.get("values") or []
            v = (vals[0] if vals else {}).get("value")
            if v is None:
                v = (item.get("total_value") or {}).get("value")
            out[item.get("name")] = _int(v)
        return out
    return {}


def pull_instagram(videos: list[dict], day: str) -> str:
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("Instagram not connected (IG_ACCESS_TOKEN)")
    vids = [v for v in videos if v.get("instagram_id")]
    n, errors = 0, 0
    for v in vids:
        try:
            m = ig_insights(v["instagram_id"], token)
        except Exception as e:
            errors += 1
            print(f"   instagram {v['instagram_id']}: {str(e)[:120]}")
            continue
        store.upsert("stats", {"video_id": v["id"], "platform": "instagram", "day": day,
                               "views": m.get("views", 0), "likes": m.get("likes", 0), "comments": m.get("comments", 0),
                               "shares": m.get("shares", 0), "saves": m.get("saved", 0), "reach": m.get("reach", 0)},
                     on_conflict="video_id,platform,day")
        n += 1
    me = _ig_get("me", token, fields="followers_count,media_count")
    store.upsert("channel_stats", {"platform": "instagram", "day": day, "followers": _int(me.get("followers_count")),
                                   "videos": _int(me.get("media_count"))}, on_conflict="platform,day")
    if vids and errors == len(vids):
        raise RuntimeError("every Instagram insights call failed")
    return f"instagram: {n} reels ({errors} errors), account {me.get('followers_count')} followers"


# ----------------------------------------------------------------------------- main
def run() -> int:
    store.load_settings_into_env()
    if not store.enabled():
        print("stats: Supabase not configured, nothing to do")
        return 0
    day = today_ist()
    videos = store.select("videos", select="id,youtube_id,instagram_id", limit=1000,
                          **{"or": "(youtube_id.not.is.null,instagram_id.not.is.null)"})
    results, failed = [], []
    for name, fn in (("youtube", pull_youtube), ("instagram", pull_instagram)):
        try:
            results.append(fn(videos, day))
        except Exception as e:
            failed.append(name)
            results.append(f"{name}: failed ({type(e).__name__}: {str(e)[:160]})")
    results.append(refresh_instagram_token())
    print(f"stats {day}: " + "; ".join(r for r in results if r))
    return 1 if len(failed) == 2 else 0


def refresh_instagram_token() -> str:
    """Instagram long-lived tokens expire after 60 days unless refreshed. Refresh at most once every 7 days (the
    API needs the token to be at least 24 h old) and save the new one, so nobody has to paste a token again."""
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token or not store.enabled():
        return ""
    import datetime as dt
    row = store.one("settings", key="eq.ig_access_token", select="value,updated_at")
    if row.get("value") != token:
        return ""                      # the token came from a GitHub secret, not Settings: leave it alone
    try:
        age = dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(str(row.get("updated_at")).replace("Z", "+00:00"))
    except ValueError:
        age = dt.timedelta(days=30)
    if age < dt.timedelta(days=7):
        return ""
    try:
        from publish import instagram as ig
        new = ig.refresh_token(token).get("access_token")
        if new:
            store.set_setting("ig_access_token", new)
            return "instagram token renewed for 60 days"
        return "instagram token: refresh returned no token"
    except Exception as e:
        return f"instagram token refresh failed ({type(e).__name__}: {str(e)[:120]})"


if __name__ == "__main__":
    sys.exit(run())
