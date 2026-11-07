"""YouTube upload via the official Data API v3 (OAuth, resumable upload, AI + kids flags)."""
from __future__ import annotations

import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
CATEGORY_IDS = {"film": "1", "music": "10", "pets": "15", "sports": "17", "gaming": "20", "people": "22",
                "comedy": "23", "entertainment": "24", "news": "25", "howto": "26", "education": "27", "science": "28"}

# Plain-HTTP redirects are only acceptable on localhost; hosted installs set PUBLIC_URL=https://...
if not os.environ.get("PUBLIC_URL", "").startswith("https://"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def auth_url(client_secret_file: str, redirect_uri: str, state: str):
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(client_secret_file, scopes=SCOPES, redirect_uri=redirect_uri, state=state)
    url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
    return url, getattr(flow, "code_verifier", None)


def exchange(client_secret_file: str, redirect_uri: str, state: str, authorization_response: str,
             code_verifier: str | None = None) -> str:
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_secrets_file(client_secret_file, scopes=SCOPES, redirect_uri=redirect_uri, state=state)
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(authorization_response=authorization_response)
    return flow.credentials.to_json()


def _service(creds_json: str):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_info(json.loads(creds_json), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds, cache_discovery=False), creds.to_json()


def channel_info(creds_json: str) -> dict:
    yt, _ = _service(creds_json)
    items = yt.channels().list(part="snippet,statistics", mine=True).execute().get("items", [])
    if not items:
        return {}
    it = items[0]
    return {"id": it["id"], "title": it["snippet"]["title"], "subscribers": it["statistics"].get("subscriberCount")}


def upload(creds_json: str, video_path: str, spec: dict, privacy: str = "private", publish_at: str | None = None,
           thumbnail: str | None = None, progress=None) -> dict:
    """Upload a rendered video. privacy: private | unlisted | public. publish_at: RFC3339 (forces private until then).

    Note: until your Google Cloud project passes the YouTube API compliance audit, YouTube locks every
    API upload to private regardless of `privacy`.
    """
    from googleapiclient.http import MediaFileUpload
    yt, refreshed = _service(creds_json)
    title = (spec.get("title") or "Untitled")[:100]
    desc = (spec.get("description") or "")[:4900]
    is_short = spec.get("aspect", "9:16") == "9:16"
    if is_short and "#shorts" not in (title + desc).lower():
        desc += "\n\n#Shorts"
    lang = {"hi": "hi", "hinglish": "hi", "en": "en"}.get(spec.get("language", "hi"), "hi")
    body = {
        "snippet": {
            "title": title,
            "description": desc,
            "tags": [t[:30] for t in (spec.get("tags") or [])][:15],
            "categoryId": CATEGORY_IDS.get(spec.get("category", "education"), "27"),
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": {
            "privacyStatus": "private" if publish_at else privacy,
            "selfDeclaredMadeForKids": bool(spec.get("made_for_kids", False)),
            "containsSyntheticMedia": True,
            "embeddable": True,
        },
    }
    if publish_at:
        body["status"]["publishAt"] = publish_at
    media = MediaFileUpload(video_path, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=True)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status and progress:
            progress(status.progress())
    vid = resp["id"]
    if thumbnail and os.path.exists(thumbnail) and not is_short:
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumbnail)).execute()
        except Exception:
            pass  # needs a verified channel; not fatal
    return {"id": vid, "url": f"https://youtu.be/{vid}", "privacy": resp["status"].get("privacyStatus"),
            "refreshed_credentials": refreshed}


def video_stats(creds_json: str, video_ids: list[str]) -> list[dict]:
    yt, _ = _service(creds_json)
    out = []
    for i in range(0, len(video_ids), 50):
        r = yt.videos().list(part="statistics,snippet", id=",".join(video_ids[i:i + 50])).execute()
        for it in r.get("items", []):
            out.append({"id": it["id"], "title": it["snippet"]["title"], **it.get("statistics", {})})
    return out
