#!/usr/bin/env python3
"""VidForge command line.

  python run.py setup                      download the free voice model and fonts
  python run.py serve [--port 8000]        start the dashboard on http://127.0.0.1:8000
  python run.py render SPEC.json [--out DIR] [--preview]
  python run.py stills SPEC.json           render QA stills only (fast)
  python run.py validate SPEC.json
  python run.py trends [--niche space]     print raw India trend signals (no Claude)
  python run.py e2e [--language en]        live end-to-end test with your Claude key
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

DOWNLOADS = {
    "models/kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "models/voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
    "assets/fonts/Mukta-ExtraBold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/mukta/Mukta-ExtraBold.ttf",
    "assets/fonts/Mukta-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/mukta/Mukta-Bold.ttf",
    "assets/fonts/Baloo2.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/baloo2/Baloo2%5Bwght%5D.ttf",
    "assets/fonts/NotoSansDevanagari.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth,wght%5D.ttf",
    "assets/fonts/Poppins-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf",
    "assets/fonts/NotoColorEmoji.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/notocoloremoji/NotoColorEmoji-Regular.ttf",
}


def setup(fonts_only: bool = False):
    import shutil
    import urllib.request
    for rel, url in DOWNLOADS.items():
        if fonts_only and not rel.startswith("assets/fonts"):
            continue
        if rel.endswith("NotoColorEmoji.ttf") and os.path.exists("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"):
            continue  # system emoji font is enough
        path = os.path.join(ROOT, rel)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            print("ok  ", rel)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print("get ", rel)
        urllib.request.urlretrieve(url, path)
    if not shutil.which("ffmpeg") or subprocess.run(["ffmpeg", "-version"], capture_output=True).returncode != 0:
        print("\nInstall ffmpeg: brew install ffmpeg | sudo apt install ffmpeg | winget install ffmpeg")
    print("\nDone. Next: python run.py serve")


def youtube_auth(client_secret: str):
    """Opens a browser to sign in to the YouTube channel, then prints the three values to save as GitHub secrets."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    from publish.youtube import SCOPES
    flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    print("\nSave these as repository secrets (Settings > Secrets and variables > Actions), or paste them in the web UI:\n")
    print(f"YOUTUBE_CLIENT_ID={creds.client_id}")
    print(f"YOUTUBE_CLIENT_SECRET={creds.client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}")


def main():
    ap = argparse.ArgumentParser(description="VidForge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    su = sub.add_parser("setup")
    su.add_argument("--fonts-only", action="store_true")
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    s.add_argument("--host", default=os.environ.get("VIDFORGE_HOST", "127.0.0.1"))
    e = sub.add_parser("e2e", help="live end-to-end test with your Claude key: trends -> scout -> research -> write -> QA -> render")
    e.add_argument("--options", default="{}", help="JSON options (see tools/e2e.py); flags below override it")
    e.add_argument("--niche", default="")
    e.add_argument("--language", default="", help="en, hi, hinglish, es, fr, it, pt or any language")
    e.add_argument("--topic", default="", help="skip scouting and use this topic")
    e.add_argument("--format", default="")
    e.add_argument("--writer", default="", help="override writer model, e.g. claude-fable-5-1")
    e.add_argument("--stage", default="all", choices=["all", "scout", "research", "write", "qa", "render", "package", "publish"])
    e.add_argument("--out", default="", help="working folder (needed when running single stages)")
    for name in ("render", "stills", "validate"):
        p = sub.add_parser(name)
        p.add_argument("spec")
        p.add_argument("--out")
        p.add_argument("--preview", action="store_true", help="half resolution, faster")
    pv = sub.add_parser("publish-video", help="post a rendered folder to YouTube/Instagram using env credentials")
    pv.add_argument("out")
    pv.add_argument("--youtube", action="store_true")
    pv.add_argument("--instagram", action="store_true")
    pv.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    pv.add_argument("--publish-at", default="")
    pv.add_argument("--overrides", default="{}", help='JSON {"youtube": {"title":..}, "instagram": {"caption":..}}')
    ya = sub.add_parser("youtube-auth", help="one-time: get a YouTube refresh token for the GitHub secrets")
    ya.add_argument("client_secret", help="OAuth client JSON (type: Desktop app) from Google Cloud Console")
    t = sub.add_parser("trends")
    t.add_argument("--niche", default="general")
    a = ap.parse_args()

    if a.cmd == "setup":
        return setup(a.fonts_only)
    if a.cmd == "serve":
        import uvicorn
        if a.host not in ("127.0.0.1", "localhost") and not os.environ.get("VIDFORGE_PASSWORD"):
            sys.exit("Refusing to listen on a public interface without VIDFORGE_PASSWORD set.")
        print(f"VidForge Studio on http://{a.host}:{a.port}")
        uvicorn.run("app.server:app", host=a.host, port=a.port, log_level="warning", proxy_headers=True)
        return
    if a.cmd == "e2e":
        from tools.e2e import run_e2e
        run_e2e(a.niche, a.language, a.topic, a.format, a.writer, a.stage, a.out, a.options)
        return
    if a.cmd == "publish-video":
        from tools.publish import publish
        publish(a.out, a.youtube, a.instagram, a.privacy, a.publish_at or None, json.loads(a.overrides or "{}"))
        return
    if a.cmd == "youtube-auth":
        return youtube_auth(a.client_secret)
    if a.cmd == "trends":
        from app import db
        from trends.sources import gather
        db.init()
        for it in gather(a.niche, db.get_setting("youtube_api_key", "")):
            print(json.dumps(it, ensure_ascii=False))
        return

    spec = json.load(open(a.spec, encoding="utf-8"))
    if a.cmd == "validate":
        from engine.validate import validate
        errs, warns = validate(spec)
        for e in errs:
            print("ERROR  ", e)
        for w in warns:
            print("warning", w)
        print("OK" if not errs else "FAILED")
        sys.exit(1 if errs else 0)
    from engine.pipeline import render_episode
    if a.preview:
        spec["preview"] = True
    out = a.out or os.path.join(ROOT, "data", "out", os.path.splitext(os.path.basename(a.spec))[0])
    res = render_episode(spec, out, progress=lambda st, f: print(f"\r{st:<9} {f * 100:5.1f}%", end="", flush=True),
                         stills_only=(a.cmd == "stills"))
    print()
    print(json.dumps({k: v for k, v in res.items() if k != "timeline"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
