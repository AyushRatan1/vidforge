"""world3d: low-poly 3D "watch it get built" backgrounds.

A spec may carry a top-level `world3d` describing one continuous diorama (terrain with animated digs, walls that rise
course by course, stairs that drop in step by step, pillared halls, water, trees, villagers) and a camera path.
Scenes whose background is {"type": "world3d"} show that world at their own slice of the timeline, so the build reads
as one continuous shot under the narration, captions and labels that the 2D engine draws on top.

Times inside the world can be absolute seconds or references to scenes, resolved here once scene lengths are known:
    {"scene": "dig", "t": 0.5}            half way through scene "dig" (id or 1-based index)
    {"scene": "dig", "at": 1.2}           1.2 s into the scene
    {"scene": "dig", "word": "water"}     when the narrator says "water" (plus optional "offset")

Rendering runs the three.js runtime in engine/world3d_runtime inside headless Chromium (Playwright, software WebGL),
streams JPEG frames into ffmpeg and hands each scene a prepared clip, exactly like stock footage. If anything fails
the scenes fall back to a drawn background, so a video is never lost to the 3D step.
"""
from __future__ import annotations

import base64
import copy
import functools
import hashlib
import http.server
import json
import logging
import os
import subprocess
import threading

log = logging.getLogger("vidforge.world3d")
HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.join(HERE, "world3d_runtime")
FALLBACK = {"type": "sunburst", "colors": ["#e7d5b5", "#d4b98c"]}
TIME_KEYS = {"at", "from", "to", "rope_start", "rope_end"}
KIT = {"box", "slab", "cylinder", "cone", "pyramid", "dome", "sphere", "mound", "wall", "stairs", "pillar", "pavilion",
       "spire", "arch", "water", "tree", "trees", "grass", "rocks", "house", "ladder", "well", "person", "people"}
MACROS = {"stepwell"}
STYLES = {"desert", "golden", "green", "overcast", "night"}


def runtime_version() -> str:
    h = hashlib.sha1()
    for name in sorted(os.listdir(RUNTIME)):
        p = os.path.join(RUNTIME, name)
        if os.path.isfile(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:10]


# ------------------------------------------------------------------ macros
def stepwell(m: dict) -> tuple[list, list]:
    """Expand a stepwell (vav) into a dig and primitives: a long trench lined with stone, flights of steps going down
    from the back towards the deep end at the front, a pillared pavilion on every landing and water at the bottom.
    Returns (digs, objects). Phase windows: dig, walls, stairs, halls, water, each {"from", "to"}."""
    x0, x1 = float(m.get("x0", -4)), float(m.get("x1", 4))
    zf = float(m.get("z_front", 0))
    length = float(m.get("length", 22))
    zb = zf - length
    depth = float(m.get("depth", 10))
    levels = max(2, int(m.get("levels", 5)))
    color = m.get("color", "#e3d6bf")
    ph = m.get("phases", {})
    digs = [{"x0": x0, "x1": x1, "z0": zb, "z1": zf, "depth": depth + 0.4, **({"from": ph["dig"]["from"], "to": ph["dig"]["to"]} if ph.get("dig") else {})}]
    objs: list = []
    wall_t = 0.7
    for xs in (x0 + wall_t / 2, x1 - wall_t / 2):
        objs.append({"type": "wall", "from": [xs, zb], "to": [xs, zf], "pos": [0, -depth - 0.4, 0], "h": depth + 0.4,
                     "thickness": wall_t, "color": color, "build": {"op": "stagger", **ph.get("walls", {})}})
    objs.append({"type": "wall", "from": [x0, zb + wall_t / 2], "to": [x1, zb + wall_t / 2], "pos": [0, -depth - 0.4, 0],
                 "h": depth + 0.4, "thickness": wall_t, "color": color, "build": {"op": "stagger", **ph.get("walls", {})}})
    inner_w = (x1 - x0) - 2 * wall_t
    run_total = length * 0.78
    step_drop = depth / levels
    flight_run = run_total / levels * 0.62
    landing = run_total / levels * 0.38
    z = zb + wall_t
    y = 0.0
    stairs_ph = ph.get("stairs", {})
    halls_ph = ph.get("halls", {})
    for k in range(levels):
        win = _sub(stairs_ph, k, levels)
        objs.append({"type": "stairs", "from": [(x0 + x1) / 2, y, z], "to": [(x0 + x1) / 2, y - step_drop, z + flight_run],
                     "width": inner_w * 0.42, "steps": max(6, int(step_drop / 0.22)), "color": color,
                     "build": {"op": "stagger", **win}})
        z += flight_run
        y -= step_drop
        objs.append({"type": "slab", "pos": [(x0 + x1) / 2, y - 0.3, z + landing / 2], "w": inner_w, "h": 0.3, "d": landing,
                     "color": color, "texture": "stone", "build": {"op": "rise", **win}})
        if k < levels - 1:
            hh = min(step_drop * 0.95, 3.2)
            objs.append({"type": "pavilion", "pos": [(x0 + x1) / 2, y, z + landing / 2], "w": inner_w - 0.4, "d": max(0.8, landing - 0.4),
                         "h": hh, "cols": 4, "rows": 2, "color": color, "build": {"op": "stagger", **_sub(halls_ph, k, levels - 1)}})
        z += landing
    # the deep end: a well shaft area at the front with water
    if ph.get("water") is not None or m.get("water", True):
        w = ph.get("water", {})
        objs.append({"type": "water", "x0": x0 + wall_t, "x1": x1 - wall_t, "z0": z - landing, "z1": zf,
                     "y_bottom": -depth - 0.4, "level_from": -depth - 0.4, "level": -depth + 1.2, **w})
    return digs, objs


def _sub(window: dict, k: int, n: int) -> dict:
    """The k-th of n equal slices of a {from, to} window (times are already numeric when this runs)."""
    if not window or "from" not in window:
        return {}
    a, b = float(window["from"]), float(window.get("to", float(window["from"]) + 1))
    return {"from": a + (b - a) * k / n, "to": a + (b - a) * (k + 1) / n}


def expand(world: dict) -> dict:
    w = copy.deepcopy(world)
    terrain = w.setdefault("terrain", {}) if w.get("terrain") is not False else None
    objs = []
    for o in w.get("objects", []):
        if o.get("type") == "stepwell":
            digs, more = stepwell(o)
            if terrain is not None:
                terrain.setdefault("digs", []).extend(digs)
            objs.extend(more)
        else:
            objs.append(o)
    w["objects"] = objs
    return w


# ------------------------------------------------------------------ time references
def scene_index(spec: dict) -> dict:
    idx = {}
    for i, sc in enumerate(spec["scenes"]):
        idx[str(i + 1)] = i
        if sc.get("id"):
            idx[str(sc["id"])] = i
    return idx


def resolve_time(ref, spec: dict, tl: list, idx: dict) -> float:
    if isinstance(ref, (int, float)):
        return float(ref)
    if not isinstance(ref, dict) or "scene" not in ref:
        raise ValueError(f"bad time reference {ref!r}")
    key = str(ref["scene"])
    if key not in idx:
        raise ValueError(f"time reference to unknown scene {ref['scene']!r}")
    i = idx[key]
    seg = tl[i]
    if ref.get("word"):
        from .pipeline import word_time
        t = word_time(spec["scenes"][i].get("narration", ""), str(ref["word"]), seg["voice_start"], seg["voice_dur"])
        base = seg["start"] + (t if t is not None else 0.0)
    elif "at" in ref:
        base = seg["start"] + float(ref["at"])
    else:
        base = seg["start"] + seg["dur"] * float(ref.get("t", 0))
    return round(base + float(ref.get("offset", 0)), 4)


def resolve(obj, spec: dict, tl: list, idx: dict):
    if isinstance(obj, list):
        return [resolve(x, spec, tl, idx) for x in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in TIME_KEYS and (isinstance(v, dict) and "scene" in v):
                out[k] = resolve_time(v, spec, tl, idx)
            else:
                out[k] = resolve(v, spec, tl, idx)
        return out
    return obj


def prepare_world(spec: dict, tl: list) -> dict:
    """Resolve scene references to seconds, then expand macros (macros slice numeric phase windows)."""
    idx = scene_index(spec)
    w = resolve(spec["world3d"], spec, tl, idx)
    return expand(w)


# ------------------------------------------------------------------ validation
def validate_world(world, scene_ids: set) -> tuple[list, list]:
    errs, warns = [], []
    if not isinstance(world, dict):
        return ["world3d must be an object"], warns
    if world.get("style") and world["style"] not in STYLES:
        warns.append(f"world3d style {world['style']!r} unknown, using desert (choose from {sorted(STYLES)})")
    objs = world.get("objects", [])
    if not isinstance(objs, list) or not objs:
        errs.append("world3d.objects must be a non-empty list")
        objs = []
    for k, o in enumerate(objs):
        t = (o or {}).get("type")
        if t not in KIT and t not in MACROS:
            errs.append(f"world3d object {k + 1}: unknown type {t!r} (use {sorted(KIT | MACROS)})")
    cam = world.get("camera", [])
    if not isinstance(cam, list) or not cam:
        warns.append("world3d.camera has no keys; a default three-quarter view will be used")

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in TIME_KEYS and isinstance(v, dict) and "scene" in v and str(v["scene"]) not in scene_ids:
                    errs.append(f"world3d {path}.{k}: unknown scene {v['scene']!r}")
                walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
    walk(world, "world3d")
    return errs, warns


# ------------------------------------------------------------------ browser renderer
class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class World3DRenderer:
    """One headless browser session. Use as a context manager."""

    def __init__(self, W: int, H: int, scale: float | None = None, quality: float = 0.9):
        self.W, self.H = W, H
        self.scale = float(scale or os.environ.get("VIDFORGE_3D_SCALE", 0.75))
        self.rw, self.rh = int(round(W * self.scale / 2) * 2), int(round(H * self.scale / 2) * 2)
        self.quality = quality

    def __enter__(self):
        handler = functools.partial(_Quiet, directory=RUNTIME)
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = self._launch()
        self.page = self.browser.new_page(viewport={"width": 400, "height": 400})
        errors = []
        self.page.on("pageerror", lambda e: errors.append(str(e)))
        self.page.on("console", lambda m: m.type in ("error", "warning") and log.warning("world3d: %s", m.text))
        self.page.goto(f"http://127.0.0.1:{self.httpd.server_address[1]}/index.html")
        try:
            self.page.wait_for_function("window.VF_READY === true", timeout=30000)
        except Exception:
            raise RuntimeError(f"world3d runtime did not start: {errors}")
        return self

    def _launch(self):
        args = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-dev-shm-usage"]
        last = None
        for kw in ({}, {"channel": "chrome"}, {"channel": "chromium"}):
            try:
                return self._pw.chromium.launch(args=args, **kw)
            except Exception as e:  # browser binary missing: try the next option
                last = e
        try:  # last resort on a fresh runner: download Playwright's Chromium
            subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True, capture_output=True, timeout=600)
            return self._pw.chromium.launch(args=args)
        except Exception as e:
            raise RuntimeError(f"no Chromium for world3d: {last} / {e}")

    def __exit__(self, *exc):
        try:
            self.browser.close()
            self._pw.stop()
        finally:
            self.httpd.shutdown()

    def setup(self, world: dict):
        return self.page.evaluate("([w, o]) => window.VF.setup(w, o)",
                                  [world, {"width": self.rw, "height": self.rh, "quality": self.quality}])

    def frame_jpeg(self, t: float) -> bytes:
        url = self.page.evaluate("(t) => window.VF.frame(t)", t)
        return base64.b64decode(url.split(",", 1)[1])

    def still(self, t: float, path: str) -> str:
        data = self.frame_jpeg(t)
        tmp = path + ".part.jpg"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-i", "-",
               "-vf", f"scale={self.W}:{self.H}:flags=lanczos", "-q:v", "2", tmp]
        subprocess.run(cmd, input=data, check=True)
        os.replace(tmp, path)
        return path

    def render_range(self, t0: float, dur: float, fps: float, dst: str) -> str:
        n = max(1, int(round(dur * fps)))
        tmp = dst[:-4] + ".part.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
               "-vf", f"scale={self.W}:{self.H}:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "18", "-r", str(fps), "-an", "-movflags", "+faststart", tmp]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for k in range(n):
                proc.stdin.write(self.frame_jpeg(t0 + k / fps))
        finally:
            proc.stdin.close()
            rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg failed while encoding world3d clip (exit {rc})")
        os.replace(tmp, dst)
        return dst


# ------------------------------------------------------------------ pipeline hook
def resolve_world3d(spec: dict, tl: list, out_dir: str, stills_only: bool = False, progress=None) -> dict | None:
    """Render the world for every scene that shows it and turn those backgrounds into prepared clips.
    Returns a small record for the manifest, or None when the spec has no world."""
    world_spec = spec.get("world3d")
    if not world_spec:
        return None
    show = []
    for i, sc in enumerate(spec["scenes"]):
        bg = sc.get("background")
        if not bg:
            sc["background"] = bg = {"type": "world3d"}
        if bg.get("type") == "world3d":
            show.append(i)
    if not show:
        return None
    fps = 4 if stills_only else spec["fps"]
    W, H = spec["_W"], spec["_H"]
    t_start = __import__("time").time()
    try:
        world = prepare_world(spec, tl)
        key_base = hashlib.sha1(json.dumps([world, W, H, runtime_version(),
                                            os.environ.get("VIDFORGE_3D_SCALE", "0.75")], sort_keys=True).encode()).hexdigest()[:10]
        work = os.path.join(out_dir, "work")
        os.makedirs(work, exist_ok=True)
        from .footage import extract_frame
        with World3DRenderer(W, H) as r:
            r.setup(world)
            for n, i in enumerate(show):
                seg = tl[i]
                bg = spec["scenes"][i]["background"]
                dst = os.path.join(work, f"world_{i + 1:02d}_{key_base}_{fps}_{seg['start']:.2f}_{seg['dur']:.2f}.mp4")
                if not os.path.exists(dst):
                    if progress:
                        progress("world3d", n / len(show))
                    r.render_range(seg["start"], seg["dur"] + 0.5, fps, dst)
                spec["scenes"][i]["background"] = {
                    "type": "footage", "_file": dst, "_clip": f"world3d_{key_base}_{i}",
                    "_last_frame": extract_frame(dst, max(0.0, seg["dur"] - 1.0 / fps), dst[:-4] + "_last.png"),
                    "dim": float(bg.get("dim", 0)), "tint": bg.get("tint", "#000000"),
                    "fallback": bg.get("fallback") or dict(FALLBACK),
                }
        return {"scenes": len(show), "fps": fps, "seconds": round(__import__("time").time() - t_start, 1)}
    except Exception as e:
        log.warning("world3d render failed, using drawn fallback: %s", e)
        print(f"   world3d failed ({type(e).__name__}: {e}); using drawn backgrounds", flush=True)
        for i in show:
            bg = spec["scenes"][i].get("background") or {}
            spec["scenes"][i]["background"] = bg.get("fallback") or dict(FALLBACK)
        return {"error": f"{type(e).__name__}: {e}"}
