"""Real stock footage for scene backgrounds: search Pexels (and Pixabay), pick a clip, download it, and cut it
to the canvas size and scene length with ffmpeg. Everything here degrades to "no footage" instead of raising:
no key, no network, no results or a broken download all return [] / None so the renderer can fall back.

Env: PEXELS_API_KEY (https://www.pexels.com/api/), PIXABAY_API_KEY (optional, https://pixabay.com/api/docs/).
Clips are cached in models/footage (override with VIDFORGE_FOOTAGE_DIR) so repeat renders do not re-download.
"""
from __future__ import annotations

import hashlib
import logging
import os
import random
import subprocess

import requests

log = logging.getLogger("vidforge.footage")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.environ.get("VIDFORGE_FOOTAGE_DIR") or os.path.join(ROOT, "models", "footage")
TIMEOUT = 20
PEXELS_URL = "https://api.pexels.com/videos/search"
PIXABAY_URL = "https://pixabay.com/api/videos/"
MAX_WIDTH = {"portrait": 1080, "landscape": 1920, "square": 1080}
DEFAULT_FALLBACK = {"type": "sunburst", "colors": ["#1d2742", "#121a2e"], "speed": 3}


# ---------------------------------------------------------------- search
def search(query: str, orientation: str = "portrait", per_page: int = 15) -> list[dict]:
    """Normalized clips from every provider that has a key. Never raises for network errors."""
    query = (query or "").strip()
    if not query:
        return []
    out: list[dict] = []
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    pixabay_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    limit = MAX_WIDTH.get(orientation, 1080)
    if pexels_key:
        try:
            r = requests.get(PEXELS_URL, headers={"Authorization": pexels_key},
                             params={"query": query, "orientation": orientation, "size": "medium", "per_page": per_page},
                             timeout=TIMEOUT)
            if r.status_code == 200:
                out += [c for c in (_norm_pexels(v, limit) for v in r.json().get("videos", [])) if c]
            else:
                log.warning("Pexels search %r failed: HTTP %s", query, r.status_code)
        except Exception as e:  # network, JSON, anything: footage is optional
            log.warning("Pexels search %r failed: %s", query, e)
    if pixabay_key:
        try:
            r = requests.get(PIXABAY_URL, params={"key": pixabay_key, "q": query, "video_type": "film",
                                                  "per_page": max(3, min(per_page, 200)), "safesearch": "true"},
                             timeout=TIMEOUT)
            if r.status_code == 200:
                out += [c for c in (_norm_pixabay(h, limit) for h in r.json().get("hits", [])) if c]
            else:
                log.warning("Pixabay search %r failed: HTTP %s", query, r.status_code)
        except Exception as e:
            log.warning("Pixabay search %r failed: %s", query, e)
    return out


def _norm_pexels(v: dict, limit: int) -> dict | None:
    files = [f for f in v.get("video_files") or [] if str(f.get("file_type", "")).endswith("mp4") and f.get("link")]
    if not files:
        return None
    fitting = [f for f in files if int(f.get("width") or 0) <= limit]
    pool = fitting or sorted(files, key=lambda f: int(f.get("width") or 0))[:1]
    # prefer hd, then the largest that fits
    pool.sort(key=lambda f: (f.get("quality") == "hd", int(f.get("width") or 0)), reverse=True)
    best = pool[0]
    user = (v.get("user") or {}).get("name") or "Pexels"
    return {"id": str(v.get("id")), "provider": "pexels", "url": best["link"],
            "width": int(best.get("width") or 0), "height": int(best.get("height") or 0),
            "duration": float(v.get("duration") or 0), "page_url": v.get("url", ""), "credit": user}


def _norm_pixabay(h: dict, limit: int) -> dict | None:
    vids = h.get("videos") or {}
    cands = [(k, d) for k, d in vids.items() if isinstance(d, dict) and d.get("url")]
    if not cands:
        return None
    fitting = [(k, d) for k, d in cands if int(d.get("width") or 0) <= limit]
    pool = fitting or sorted(cands, key=lambda kd: int(kd[1].get("width") or 0))[:1]
    pool.sort(key=lambda kd: int(kd[1].get("width") or 0), reverse=True)
    k, d = pool[0]
    return {"id": str(h.get("id")), "provider": "pixabay", "url": d["url"],
            "width": int(d.get("width") or 0), "height": int(d.get("height") or 0),
            "duration": float(h.get("duration") or 0), "page_url": h.get("pageURL", ""),
            "credit": h.get("user") or "Pixabay"}


# ---------------------------------------------------------------- choose
def pick(results: list[dict], duration: float, exclude=None, query: str = "") -> dict | None:
    """Deterministic choice (seeded by the query hash): a clip at least `duration` s long if any, else the
    longest; ids in `exclude` are avoided so consecutive scenes differ."""
    exclude = set(exclude or ())
    pool = [c for c in results if c.get("id") not in exclude] or list(results)
    if not pool:
        return None
    seed_src = query or ",".join(sorted(str(c.get("id")) for c in pool))
    rnd = random.Random(int(hashlib.sha1(seed_src.encode("utf-8")).hexdigest()[:8], 16))
    long_enough = [c for c in pool if float(c.get("duration") or 0) >= duration]
    if long_enough:
        return rnd.choice(sorted(long_enough, key=lambda c: str(c["id"])))
    return max(pool, key=lambda c: (float(c.get("duration") or 0), str(c["id"])))


# ---------------------------------------------------------------- download
def fetch(clip: dict, cache_dir: str | None = None) -> str | None:
    """Download the clip to cache_dir/<provider>_<id>.mp4 (streamed to .part then renamed). None on failure."""
    cache_dir = cache_dir or CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)
    dst = os.path.join(cache_dir, f"{clip['provider']}_{clip['id']}.mp4")
    if os.path.exists(dst) and os.path.getsize(dst) > 10_000:
        return dst
    part = dst + ".part"
    try:
        with requests.get(clip["url"], stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(part, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    if chunk:
                        f.write(chunk)
        if os.path.getsize(part) < 10_000:
            raise RuntimeError("download too small")
        os.replace(part, dst)
        return dst
    except Exception as e:
        log.warning("footage download failed for %s %s: %s", clip.get("provider"), clip.get("id"), e)
        try:
            os.remove(part)
        except OSError:
            pass
        return None


# ---------------------------------------------------------------- cut to size
def prepare(src: str, dst: str, W: int, H: int, duration: float, fps: int, start: float = 0.0, speed: float = 1.0) -> str:
    """Crop/scale `src` to exactly WxH (scale to cover, centre crop), loop if shorter, trim to `duration`,
    strip audio, encode h264 at `fps`. Raises RuntimeError when ffmpeg fails."""
    part = dst + ".part.mp4"
    vf = []
    if speed and abs(float(speed) - 1.0) > 1e-3:
        vf.append(f"setpts=PTS/{float(speed):.4f}")
    vf += [f"scale={W}:{H}:force_original_aspect_ratio=increase", f"crop={W}:{H}", f"fps={fps}", "format=yuv420p"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1"]
    if start and start > 0:
        cmd += ["-ss", f"{float(start):.3f}"]
    cmd += ["-i", src, "-t", f"{float(duration):.3f}", "-an", "-vf", ",".join(vf),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-movflags", "+faststart", part]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        try:
            os.remove(part)
        except OSError:
            pass
        raise RuntimeError(f"ffmpeg prepare failed: {r.stderr[-800:]}")
    os.replace(part, dst)
    return dst


def extract_frame(src: str, t: float, dst: str) -> str | None:
    """One PNG frame at time t (clamped inside the clip). None on failure."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0.0, float(t)):.3f}", "-i", src,
           "-frames:v", "1", "-update", "1", dst]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(dst):
        # near the end of a clip a seek can land past the last frame; retry at the start
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-frames:v", "1", "-update", "1", dst],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(dst):
            return None
    return dst


def probe_duration(path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


# ---------------------------------------------------------------- credits
def credits(spec_or_list) -> list[str]:
    """'Video: <credit> / Pexels' lines for the description. Accepts the render result's footage list, or a
    dict holding one under "footage" (the render manifest or a spec)."""
    items = spec_or_list
    if isinstance(spec_or_list, dict):
        items = spec_or_list.get("footage") or []
    seen, out = set(), []
    for f in items or []:
        if not isinstance(f, dict) or not f.get("id"):
            continue
        prov = {"pexels": "Pexels", "pixabay": "Pixabay"}.get(f.get("provider"), str(f.get("provider") or "").title())
        line = f"Video: {f.get('credit') or prov} / {prov}"
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out


def providers_used(footage: list[dict]) -> list[str]:
    names = []
    for f in footage or []:
        p = {"pexels": "Pexels", "pixabay": "Pixabay"}.get((f or {}).get("provider"))
        if p and p not in names:
            names.append(p)
    return names
