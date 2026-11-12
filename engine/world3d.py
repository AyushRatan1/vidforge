"""world3d: low-poly 3D "watch it get built" backgrounds.

A spec may carry a top-level `world3d` describing one continuous diorama (terrain with animated digs, walls that rise
course by course, stairs that drop in step by step, pillared halls, water, trees, villagers) and a camera path.
Scenes whose background is {"type": "world3d"} show that world at their own slice of the timeline, so the build reads
as one continuous shot under the narration, captions and labels that the 2D engine draws on top.

Times inside the world can be absolute seconds or references to scenes, resolved here once scene lengths are known:
    {"scene": "dig", "t": 0.5}            half way through scene "dig" (id or 1-based index)
    {"scene": "dig", "at": 1.2}           1.2 s into the scene
    {"scene": "dig", "word": "water"}     when the narrator says "water" (plus optional "offset")

Macros (stepwell, pyramid, fort, temple) expand here into kit primitives and terrain digs, deterministically, and
register named anchors (centre and size) that camera shots can target. Camera keys may be shots
({"shot": "wide", "target": "fort.gate", "angle": 30}); they are turned into pos/look/fov here, framed for the
spec's aspect so the subject sits in the upper middle of the frame and the caption band stays readable.

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
import math
import os
import random
import subprocess
import threading

log = logging.getLogger("vidforge.world3d")
HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.join(HERE, "world3d_runtime")
FALLBACK = {"type": "sunburst", "colors": ["#e7d5b5", "#d4b98c"]}
TIME_KEYS = {"at", "from", "to", "rope_start", "rope_end", "until"}
KIT = {"box", "slab", "cylinder", "cone", "pyramid", "dome", "sphere", "mound", "wall", "stairs", "pillar", "pavilion",
       "spire", "arch", "water", "tree", "trees", "grass", "rocks", "house", "ladder", "well", "person", "people",
       "hill", "cliff", "ramp", "blocks", "sledge", "minaret", "tomb", "bastion", "palace", "boat", "flag", "gate", "town",
       "frustum", "airliner", "ocean", "clouds", "cumulus", "streaks", "splash", "debris", "ship", "seabed", "wreck", "tanker", "mine", "missile", "blast", "stars", "earth", "towers", "crowd",
       "recorder", "auv"}
MACROS = {"stepwell", "pyramid", "fort", "temple"}
STYLES = {"desert", "golden", "green", "overcast", "night"}
FOG = {"desert": (40, 120), "golden": (35, 110), "green": (45, 130), "overcast": (35, 110), "night": (30, 90)}

# Camera shots. pitch: degrees above the target; fill: how much of the frame WIDTH the target's projected width takes
# (above 1 crops in); fov: vertical field of view. The target centre lands at SUBJECT_Y of the frame height (from the
# top), so the caption band near y=0.6 stays clear, and its top stays inside the frame.
SHOTS = {
    "wide": {"pitch": 24, "fill": 1.0, "vmax": 0.58, "fov": 38},
    "medium": {"pitch": 18, "fill": 1.35, "vmax": 0.72, "fov": 36},
    "close": {"pitch": 13, "fill": 2.1, "vmax": 1.0, "fov": 34},
    "top": {"pitch": 64, "fill": 1.0, "vmax": 0.8, "fov": 38},
    "low": {"pitch": 5, "fill": 0.8, "vmax": 0.75, "fov": 42},
    "orbit": {"pitch": 22, "fill": 1.05, "vmax": 0.62, "fov": 38},
    "inside": {"pitch": 10, "fill": 1.0, "vmax": 1.0, "fov": 52},
}
SUBJECT_Y = 0.40       # vmax: the target's half height as a share of the frame from its centre (y=0.4) to the top edge


def runtime_version() -> str:
    h = hashlib.sha1()
    for name in sorted(os.listdir(RUNTIME)):
        p = os.path.join(RUNTIME, name)
        if os.path.isfile(p):
            h.update(open(p, "rb").read())
    return h.hexdigest()[:10]


# ------------------------------------------------------------------ small helpers
def _num(v, d=None):
    if isinstance(v, bool):
        return d
    try:
        f = float(v)
    except (TypeError, ValueError):
        return d
    return f if math.isfinite(f) else d


def _r(v, n=3):
    return round(float(v), n)


def _shade(hex_color: str, f: float) -> str:
    h = str(hex_color).lstrip("#")
    if len(h) != 6:
        return hex_color
    try:
        rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    except ValueError:
        return hex_color
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c * f))) for c in rgb)


def _window(win):
    """(start, end) of a numeric {from, to} window, or None when it is missing or not resolved to seconds yet."""
    if not isinstance(win, dict):
        return None
    a = _num(win.get("from"))
    if a is None:
        return None
    b = _num(win.get("to"), a + 1.0)
    return a, max(b, a + 0.05)


def _slice(win, k: int, n: int, spread: float = 1.0, lo: float = 0.0, hi: float = 1.0) -> dict:
    """The k-th of n equal slices of the part [lo, hi] of a {from, to} window; spread > 1 lets slices overlap."""
    w = _window(win)
    if not w:
        return {}
    a, b = w[0] + (w[1] - w[0]) * lo, w[0] + (w[1] - w[0]) * hi
    step = (b - a) / max(1, n)
    s = a + step * k
    e = min(b, s + step * spread) if spread > 1 else s + step
    return {"from": round(s, 4), "to": round(max(e, s + 0.05), 4)}


_sub = _slice     # older name


def _frame(m: dict):
    """Local -> world mapping for a macro placed at pos and turned by rot degrees (local +z is its front)."""
    p = m.get("pos")
    if isinstance(p, (list, tuple)) and len(p) >= 3:
        cx, cy, cz = _num(p[0], 0.0), _num(p[1], 0.0), _num(p[2], 0.0)
    elif isinstance(p, (list, tuple)) and len(p) == 2:
        cx, cy, cz = _num(p[0], 0.0), 0.0, _num(p[1], 0.0)
    else:
        cx, cy, cz = _num(m.get("x"), 0.0), _num(m.get("y"), 0.0), _num(m.get("z"), 0.0)
    rot = _num(m.get("rot"), 0.0)
    ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(x, y, z):
        return [_r(cx + x * ca + z * sa), _r(cy + y), _r(cz - x * sa + z * ca)]
    return P, rot, (cx, cy, cz)


def _anchor(center, size) -> dict:
    return {"center": [_r(c) for c in center], "size": [_r(max(0.5, abs(s))) for s in size]}


# ------------------------------------------------------------------ hills and cliffs
def _outline(w: float, d: float, sides: int, irregular: float, seed: int) -> list:
    """An irregular (but star-shaped) footprint polygon around (0, 0), w wide (x) and d deep (z)."""
    rnd = random.Random(seed)
    sides = max(5, int(sides))
    p1, p2 = rnd.uniform(0, 2 * math.pi), rnd.uniform(0, 2 * math.pi)
    pts = []
    for i in range(sides):
        a = 2 * math.pi * i / sides + rnd.uniform(-0.25, 0.25) * (2 * math.pi / sides)
        f = 1 + irregular * (0.35 * math.sin(2 * a + p1) + 0.25 * math.sin(3 * a + p2) + rnd.uniform(-0.3, 0.3))
        pts.append([_r(math.sin(a) * w / 2 * f), _r(math.cos(a) * d / 2 * f)])
    return pts


def _ray(outline: list, a: float) -> float:
    """Distance from the centre to the outline along the direction of angle a (0 = +z, 90 degrees = +x)."""
    dx, dz = math.sin(a), math.cos(a)
    best = 0.0
    for i in range(len(outline)):
        x1, z1 = outline[i]
        x2, z2 = outline[(i + 1) % len(outline)]
        ex, ez = x2 - x1, z2 - z1
        den = dx * ez - dz * ex
        if abs(den) < 1e-9:
            continue
        s = (x1 * ez - z1 * ex) / den
        t = (x1 * dz - z1 * dx) / den
        if s > 0 and -1e-9 <= t <= 1 + 1e-9:
            best = max(best, s)
    return best or 1.0


def _inset(p, d: float) -> list:
    L = math.hypot(p[0], p[1]) or 1.0
    f = max(0.1, 1 - d / L)
    return [_r(p[0] * f), _r(p[1] * f)]


def _inside(poly, x: float, z: float) -> bool:
    c = False
    for i in range(len(poly)):
        x1, z1 = poly[i]
        x2, z2 = poly[i - 1]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / ((z2 - z1) or 1e-9) + x1:
            c = not c
    return c


def _hill_path(outline: list, h: float, batter: float, cfg, talus: float = 0.12) -> tuple[dict, list, float]:
    """A road that climbs the cliff in legs (switchbacks), hugging the face, then turns in over the rim.
    Returns (road for the hill kit, the climbing centre line, the angle where it reaches the top)."""
    cfg = cfg if isinstance(cfg, dict) else {}
    w = _num(cfg.get("width"), 1.6)
    a0 = math.radians(_num(cfg.get("from"), -60.0))
    span = math.radians(_num(cfg.get("span"), 120.0))
    legs = max(1, int(_num(cfg.get("turns"), 1)) + 1)
    th = h * 0.15     # height of the talus apron at the foot

    def scale(y):
        s = 1 + batter * max(0.0, 1 - y / h) ** 1.3
        return s + (talus * 1.2 * (1 - y / th) if y < th else 0.0)

    def at(a, y):
        rr = _ray(outline, a) * scale(y) + w / 2 + 0.15
        return [_r(math.sin(a) * rr), _r(y), _r(math.cos(a) * rr)]

    verts = [math.atan2(x, z) for x, z in outline]
    ribbons, pads, line = [], [], []
    ab = a0
    for k in range(legs):
        y0, y1 = h * k / legs, h * (k + 1) / legs
        aa, ab = (a0, a0 + span) if k % 2 == 0 else (a0 + span, a0)
        n = max(6, math.ceil(abs(span) / math.radians(6)))
        angs = {aa + (ab - aa) * i / n for i in range(n + 1)}
        lo, hi = min(aa, ab), max(aa, ab)
        for v in verts:
            for vv in (v - 2 * math.pi, v, v + 2 * math.pi):
                if lo < vv < hi:
                    angs.add(vv)
        pts = [at(a, y0 + (y1 - y0) * (a - aa) / ((ab - aa) or 1)) for a in sorted(angs, reverse=ab < aa)]
        ribbons.append({"pts": pts})
        line.extend(pts if not line else pts[1:])
        if k < legs - 1:
            pads.append(at(ab, y1))
    rim = _ray(outline, ab)
    p_end = at(ab, h)
    p_end[1] = _r(h + 0.04)
    p_in = [_r(math.sin(ab) * (rim - 2.8)), _r(h + 0.04), _r(math.cos(ab) * (rim - 2.8))]
    ribbons.append({"pts": [p_end, p_in], "bleed": False})
    return {"width": w, "ribbons": ribbons, "pads": pads}, line, ab


def _prepare_hill(o: dict) -> dict:
    """Fill in a hill/cliff's outline (seeded) and its road, so walls and gates can follow them exactly."""
    o = dict(o)
    cliff = o.get("type") == "cliff"
    h = _num(o.get("h"), 8.0)
    if not (isinstance(o.get("outline"), list) and len(o["outline"]) >= 3):
        r = _num(o.get("r"), 9.0)
        o["outline"] = _outline(_num(o.get("w"), 2 * r), _num(o.get("d"), 2 * r), int(_num(o.get("sides"), 10)),
                                _num(o.get("irregular"), 0.22), int(_num(o.get("seed"), 5)))
    o["h"] = h
    o["batter"] = _num(o.get("batter"), 0.06 if cliff else 0.14)
    o["talus"] = _num(o.get("talus"), 0.08 if cliff else 0.12)
    if o.get("path") and not (isinstance(o["path"], dict) and "ribbons" in o["path"]):
        o["path"] = _hill_path(o["outline"], h, o["batter"], o["path"], o["talus"])[0]
    return o


def _place_rects(poly: list, sizes: list, gap: float = 0.6) -> list:
    """Greedy placement of (w, d) rectangles inside a polygon, preferring the back (-z) and the middle."""
    xs, zs = [p[0] for p in poly], [p[1] for p in poly]
    out = []
    for w, d in sizes:
        best = None
        for shrink in (1.0, 0.85, 0.7, 0.55):
            ww, dd = w * shrink, d * shrink
            z = min(zs) + dd / 2
            while z <= max(zs) - dd / 2:
                x = min(xs) + ww / 2
                while x <= max(xs) - ww / 2:
                    pts = [(x + sx * ww / 2, z + sz * dd / 2) for sx in (-1, 0, 1) for sz in (-1, 0, 1)]
                    if all(_inside(poly, px, pz) for px, pz in pts) and not any(
                            abs(x - q[0]) < (ww + q[2]) / 2 + gap and abs(z - q[1]) < (dd + q[3]) / 2 + gap for q in out if q):
                        score = z + 0.35 * abs(x)
                        if best is None or score < best[0]:
                            best = (score, x, z, ww, dd)
                    x += 0.5
                z += 0.5
            if best:
                break
        out.append((_r(best[1]), _r(best[2]), _r(best[3]), _r(best[4])) if best else None)
    return out


# ------------------------------------------------------------------ macros
def stepwell(m: dict) -> tuple[list, list, dict]:
    """Expand a stepwell (vav) into a dig and primitives: a long trench lined with stone, flights of steps going down
    from the back towards the deep end at the front, a pillared pavilion on every landing and water at the bottom.
    Returns (digs, objects, anchors). Phase windows: dig, walls, stairs, halls, water, each {"from", "to"}."""
    x0, x1 = _num(m.get("x0"), -4.0), _num(m.get("x1"), 4.0)
    zf = _num(m.get("z_front"), 0.0)
    length = _num(m.get("length"), 22.0)
    zb = zf - length
    depth = _num(m.get("depth"), 10.0)
    levels = max(2, int(_num(m.get("levels"), 5)))
    color = m.get("color", "#e3d6bf")
    ph = m.get("phases") or {}
    digs = [{"x0": x0, "x1": x1, "z0": zb, "z1": zf, "depth": depth + 0.4, **({"from": ph["dig"]["from"], "to": ph["dig"]["to"]} if isinstance(ph.get("dig"), dict) and "from" in ph["dig"] else {})}]
    objs: list = []
    wall_t = 0.7
    for xs in (x0 + wall_t / 2, x1 - wall_t / 2):
        objs.append({"type": "wall", "from": [xs, zb], "to": [xs, zf], "pos": [0, -depth - 0.4, 0], "h": depth + 0.4,
                     "thickness": wall_t, "color": color, "build": {"op": "stagger", **(ph.get("walls") or {})}})
    objs.append({"type": "wall", "from": [x0, zb + wall_t / 2], "to": [x1, zb + wall_t / 2], "pos": [0, -depth - 0.4, 0],
                 "h": depth + 0.4, "thickness": wall_t, "color": color, "build": {"op": "stagger", **(ph.get("walls") or {})}})
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
        win = _slice(stairs_ph, k, levels)
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
                         "h": hh, "cols": 4, "rows": 2, "color": color, "build": {"op": "stagger", **_slice(halls_ph, k, levels - 1)}})
        z += landing
    # the deep end: a well shaft area at the front with water
    if ph.get("water") is not None or m.get("water", True):
        w = ph.get("water") or {}
        objs.append({"type": "water", "x0": x0 + wall_t, "x1": x1 - wall_t, "z0": z - landing, "z1": zf,
                     "y_bottom": -depth - 0.4, "level_from": -depth - 0.4, "level": -depth + 1.2, **w})
    name = str(m.get("id") or "stepwell")
    cx = (x0 + x1) / 2
    anchors = {name: _anchor([cx, -depth / 2, zf - length / 2], [x1 - x0, depth, length]),
               name + ".bottom": _anchor([cx, -depth * 0.8, zf - length * 0.2], [x1 - x0, depth * 0.4, length * 0.4])}
    return digs, objs, anchors


def pyramid(m: dict) -> tuple[list, list, dict]:
    """A stepped core built course by course, a ramp raised and lengthened as it grows (one theory, shown on one side),
    teams hauling blocks up it, a smooth casing laid from the top down while the ramp comes away, and a capstone that
    sits exactly on the top course. Phases: courses, ramp (defaults to courses), casing, capstone."""
    P, rot, (cx, cy, cz) = _frame(m)
    name = str(m.get("id") or "pyramid")
    b = _num(m.get("base"), 20.0)
    H = _num(m.get("height"), b * 0.636)
    N = max(3, int(_num(m.get("courses"), 12)))
    ph = m.get("phases") or {}
    hcap = H / (N + 1)
    hc = (H - hcap) / N
    core = m.get("color", "#d6b98a")
    casing_c = m.get("casing_color", "#efe3c8")
    objs: list = []
    for k in range(N):
        wk = b * (1 - (k + 1) * hc / H)     # each course's top edge lies on the casing plane
        o = {"type": "box", "pos": P(0, k * hc, 0), "rot": rot, "w": _r(wk), "h": _r(hc), "d": _r(wk),
             "color": core if k % 2 == 0 else _shade(core, 0.95), "texture": "stone", "block": [_r(max(0.9, hc * 1.5)), _r(hc)]}
        win = _slice(ph.get("courses"), k, N, 2.2)
        if win:
            o["build"] = {"op": "rise", **win}
        objs.append(o)
    anchors = {name: _anchor(P(0, H / 2, 0), [b, H, b]),
               name + ".top": _anchor(P(0, H - hcap * 0.9, 0), [b * 0.28, hcap * 3, b * 0.28]),
               name + ".base": _anchor(P(0, H * 0.16, b * 0.25), [b * 0.8, H * 0.32, b * 0.5])}
    side = m.get("ramp", "right")
    side = "right" if side is True else side
    dirs = {"right": (1, 0), "left": (-1, 0), "front": (0, 1), "back": (0, -1)}
    casing = m.get("casing", True) is not False
    cwin = _window(ph.get("casing")) if casing else None
    if side in dirs:
        dx, dz = dirs[side]
        slope = _num(m.get("ramp_slope"), 0.5)
        rw = _num(m.get("ramp_width"), max(2.2, min(4.5, b * 0.18)))
        rwin = ph.get("ramp") or ph.get("courses")
        S = max(2, min(4, N // 3))
        team_cloth = ["#f3efe6", "#e7d9b8", "#f3efe6"]
        for k in range(S):
            yk = (round((k + 1) * N / S)) * hc
            top_d = max(0.3, b * (1 - yk / H) / 2 - 0.35)
            foot_d = top_d + yk / slope
            o = {"type": "ramp", "from": P(dx * foot_d, 0, dz * foot_d), "to": P(dx * top_d, yk, dz * top_d), "width": _r(rw),
                 "color": "#c4a075" if k % 2 == 0 else "#b8956a"}
            stage = _slice(rwin, k, S, 1.0, 0.0, 1.0)
            if stage:
                s0, s1 = stage["from"], stage["to"]
                o["build"] = {"op": "rise", "from": s0, "to": round(s0 + (s1 - s0) * 0.4, 4)}
                if m.get("workers", True) is not False:     # a team hauls a block up this stage once it stands
                    t0, t1 = round(s0 + (s1 - s0) * 0.45, 4), round(s1 - 0.02, 4)
                    L = foot_d - top_d

                    def on(u, ahead=0.0, lat=0.0):
                        d = foot_d - u * L - ahead
                        return P(dx * d - dz * lat, max(0.0, yk * (foot_d - d) / L), dz * d + dx * lat)
                    objs.append({"type": "sledge", "path": [on(-0.15), on(0.82)], "from": t0, "to": t1, "pitch": True,
                                 "color": core, "build": {"op": "grow", "from": t0 - 0.3, "to": t0},
                                 "hide": {"at": t1, "dur": 0.25}})
                    for j, (ahead, lat) in enumerate(((1.5, -0.35), (2.2, 0.35))):
                        objs.append({"type": "person", "action": "pull", "path": [on(-0.15, ahead, lat), on(0.82, ahead, lat)],
                                     "from": t0, "to": t1, "cloth": team_cloth[j], "turban": False,
                                     "build": {"op": "grow", "from": t0 - 0.3, "to": t0}, "hide": {"at": t1, "dur": 0.25}})
            if cwin:     # the ramp comes away from the top down while the casing goes on
                step = (cwin[1] - cwin[0]) / S
                o["hide"] = {"at": round(cwin[0] + (S - 1 - k) * step, 4), "op": "lower", "dur": round(step, 4)}
            objs.append(o)
            if k == S - 1:
                mid = (foot_d + top_d) / 2
                anchors[name + ".ramp"] = _anchor(P(dx * mid, yk / 2, dz * mid), [abs(dx) * (foot_d - top_d) + abs(dz) * rw + 1,
                                                                                yk, abs(dz) * (foot_d - top_d) + abs(dx) * rw + 1])
    if casing:
        M = 4
        for j in range(M):
            ya, yb = j * (H - hcap) / M, (j + 1) * (H - hcap) / M
            o = {"type": "frustum", "pos": P(0, ya, 0), "rot": rot, "h": _r(yb - ya), "w": _r(b * (1 - ya / H) * 1.006),
                 "w_top": _r(b * (1 - yb / H) * 1.006), "color": casing_c, "cap": False}
            win = _slice(ph.get("casing"), M - 1 - j, M, 1.4)
            if win:
                o["build"] = {"op": "rise", **win}
            objs.append(o)
    if m.get("capstone", True) is not False:
        wc = b * hcap / H
        o = {"type": "frustum", "pos": P(0, H - hcap, 0), "rot": rot, "w": _r(wc * 1.006), "w_top": 0, "h": _r(hcap),
             "color": m.get("capstone_color", casing_c)}
        if _window(ph.get("capstone")):
            o["build"] = {"op": "drop", "height": 6, **_slice(ph["capstone"], 0, 1)}
        objs.append(o)
    return [], objs, anchors


def fort(m: dict) -> tuple[list, list, dict]:
    """A rocky hill with a road winding up through gates, ramparts with merlons along the rim, round bastions at the
    corners, a main gate where the road arrives and palaces inside the walls. Phases: hill, walls, bastions, gate,
    palaces. Anchors: <id>, .hill, .walls, .top, .path, .gate (main), .gate1... (lower gates, from the bottom), .palaces."""
    P, rot, (cx, cy, cz) = _frame(m)
    name = str(m.get("id") or "fort")
    seed = int(_num(m.get("seed"), 7))
    r = _num(m.get("r"), 10.0)
    W, D = _num(m.get("w"), 2 * r * 0.9), _num(m.get("d"), 2 * r * 1.1)
    h = _num(m.get("h"), 9.0)
    outline = m.get("outline") if isinstance(m.get("outline"), list) and len(m["outline"]) >= 3 else \
        _outline(W, D, int(_num(m.get("sides"), 10)), _num(m.get("irregular"), 0.2), seed)
    batter, talus = _num(m.get("batter"), 0.1), _num(m.get("talus"), 0.12)
    ph = m.get("phases") or {}
    wall_c = m.get("color", "#c8915c")
    wall_h, wt = _num(m.get("wall_h"), 3.0), _num(m.get("wall_t"), 0.9)
    pw = _num(m.get("path_width"), 1.4)
    road, line, a_end = _hill_path(outline, h, batter, {"width": pw, "from": _num(m.get("path_from"), -55.0),
                                                        "span": _num(m.get("path_span"), 115.0), "turns": _num(m.get("path_turns"), 1)}, talus)
    hill = {"type": "hill", "pos": [_r(cx), _r(cy), _r(cz)], "rot": rot, "outline": outline, "h": h, "batter": batter,
            "talus": talus, "seed": seed, "path": road}
    if m.get("rock_colors"):
        hill["colors"] = m["rock_colors"]
    if m.get("top_color"):
        hill["top"] = m["top_color"]
    if _window(ph.get("hill")):
        hill["build"] = {"op": "rise", **_slice(ph["hill"], 0, 1)}
    objs = [hill]
    inset, sink = wt / 2 + 0.12, 0.6
    V = [_inset(p, inset) for p in outline]
    gx, gz = math.sin(a_end) * (_ray(outline, a_end) - inset), math.cos(a_end) * (_ray(outline, a_end) - inset)
    ww = _window(ph.get("walls"))
    for i in range(len(V)):
        a, bb = V[i], V[(i + 1) % len(V)]
        ex, ez = bb[0] - a[0], bb[1] - a[1]
        L = math.hypot(ex, ez) or 1.0
        e = wt * 0.5
        o = {"type": "wall", "pos": [_r(cx), _r(cy + h - sink), _r(cz)], "rot": rot,
             "from": [_r(a[0] - ex / L * e), _r(a[1] - ez / L * e)], "to": [_r(bb[0] + ex / L * e), _r(bb[1] + ez / L * e)],
             "h": _r(wall_h + sink), "thickness": wt, "courses": max(3, round((wall_h + sink) / 0.6)), "crenels": True, "color": wall_c}
        if ww:
            s = ww[0] + (ww[1] - ww[0]) * 0.3 * i / len(V)
            o["build"] = {"op": "stagger", "from": round(s, 4), "to": round(s + (ww[1] - ww[0]) * 0.7, 4)}
        objs.append(o)
    bv = []      # bastions on the corners, kept apart and clear of the main gate
    for v in sorted(V, key=lambda q: -abs(math.atan2(q[0], q[1]))):
        if math.hypot(v[0] - gx, v[1] - gz) > 3.0 and all(math.dist(v, q) > _num(m.get("bastion_gap"), 5.0) for q in bv):
            bv.append(v)
    bv.sort(key=lambda q: math.atan2(q[0], q[1]))
    br = _num(m.get("bastion_r"), max(1.1, wt * 1.45))
    for i, v in enumerate(bv):
        o = {"type": "bastion", "pos": P(v[0], h - 1.2, v[1]), "r": _r(br), "h": _r(wall_h + 1.2 + 0.45), "color": _shade(wall_c, 1.03)}
        win = _slice(ph.get("bastions"), i, len(bv), 2.5)
        if win:
            o["build"] = {"op": "stagger", **win}
        objs.append(o)
    # gates: lower ones along the road (from the bottom), the main gate where the road meets the wall
    G = max(1, int(_num(m.get("gates"), 3)))
    acc = [0.0]
    for i in range(1, len(line)):
        acc.append(acc[-1] + math.dist(line[i - 1], line[i]))
    anchors = {}
    for g in range(G - 1):
        d = acc[-1] * (g + 1) / G * 0.96
        i = max(1, next((j for j in range(1, len(acc)) if acc[j] >= d), len(acc) - 1))
        p0, p1 = line[i - 1], line[i]
        u = (d - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
        x, y, z = (p0[k] + (p1[k] - p0[k]) * u for k in range(3))
        o = {"type": "gate", "pos": P(x, y, z), "rot": _r(rot + math.degrees(math.atan2(p1[0] - p0[0], p1[2] - p0[2]))),
             "w": _r(pw + 0.9), "h": 1.9, "d": 0.9, "drop": 1.4, "towers": False, "color": wall_c}
        win = _slice(ph.get("gate"), g, G, 1.6)
        if win:
            o["build"] = {"op": "stagger", **win}
        objs.append(o)
        anchors[f"{name}.gate{g + 1}"] = _anchor(P(x, y + 1.0, z), [6, 3.5, 6])
    nw = int(_num(m.get("walkers"), 0))
    wwin = _window(ph.get("gate")) or _window(ph.get("walls"))
    for j in range(nw):          # people climbing the road, one after another
        o = {"type": "person", "action": "walk", "path": [P(*q) for q in line[::2] + line[-1:]], "cloth": ["#f3efe6", "#d9774b", "#e7c36b"][j % 3]}
        if wwin:
            a0, a1 = wwin[0] - 1.0 + j * 1.2, wwin[1] + 6.0 + j * 1.2
            o.update({"from": round(a0, 4), "to": round(a1, 4)})
        objs.append(o)
    o = {"type": "gate", "pos": P(gx, h - sink, gz), "rot": _r(rot + math.degrees(a_end)), "w": 3.6, "h": _r(wall_h + sink + 0.8),
         "d": _r(wt + 1.4), "color": wall_c}
    win = _slice(ph.get("gate"), G - 1, G, 1.6)
    if win:
        o["build"] = {"op": "stagger", **win}
    objs.append(o)
    anchors[f"{name}.gate"] = _anchor(P(gx, h + 1.6, gz), [6, 5, 6])
    # palaces inside the walls, tallest at the back
    xs, zs = [p[0] for p in outline], [p[1] for p in outline]
    sx, sz = max(xs) - min(xs), max(zs) - min(zs)
    spec = m.get("palaces", 3)
    if isinstance(spec, (int, float)) and not isinstance(spec, bool):
        base_list = [{"w": 0.36 * sx, "d": 0.2 * sz, "h": 5.4, "domes": 3}, {"w": 0.3 * sx, "d": 0.18 * sz, "h": 4.3, "domes": 2},
                     {"w": 0.26 * sx, "d": 0.17 * sz, "h": 3.6, "domes": 2}, {"w": 0.22 * sx, "d": 0.16 * sz, "h": 3.0, "domes": 1}]
        spec = base_list[:max(0, min(4, int(spec)))]
    spec = [p for p in spec if isinstance(p, dict)] if isinstance(spec, list) else []
    inner = [_inset(p, inset + wt / 2 + 1.0) for p in outline]
    spots = _place_rects(inner, [(_num(p.get("w"), 5.0), _num(p.get("d"), 3.5)) for p in spec])
    pal_c = m.get("palace_colors") or ["#d39a62", "#c98b55", "#dcaa72", "#c7854f"]
    placed = []
    for i, (p, spot) in enumerate(zip(spec, spots)):
        if not spot:
            continue
        x, z, pw_, pd = spot
        ph_ = _num(p.get("h"), 4.5)
        o = {"type": "palace", "pos": P(x, h, z), "rot": rot, "w": pw_, "d": pd, "h": _r(ph_),
             "domes": int(_num(p.get("domes"), 2)), "color": p.get("color") or pal_c[i % len(pal_c)], "seed": i}
        if p.get("dome"):
            o["dome"] = True
        win = _slice(ph.get("palaces"), i, len(spec), 1.5)
        if win:
            o["build"] = {"op": "stagger", **win}
        objs.append(o)
        placed.append((x, z, pw_, pd, ph_))
        if p.get("id"):
            anchors[str(p["id"])] = _anchor(P(x, h + ph_ / 2, z), [pw_, ph_, pd])
    if placed and m.get("flag", True) is not False:
        x, z, pw_, pd, ph_ = max(placed, key=lambda q: q[4])
        o = {"type": "flag", "pos": P(x + pw_ * 0.3, h + ph_ + 0.36, z - pd * 0.25), "h": 2.2, "color": m.get("flag_color", "#d9772b")}
        pw0 = _window(ph.get("palaces"))
        if pw0:
            o["build"] = {"op": "grow", "from": round(pw0[1] - 0.5, 4), "to": round(pw0[1], 4)}
        objs.append(o)
    top_h = max([q[4] for q in placed] or [wall_h])
    anchors.update({
        name: _anchor(P(0, (h + top_h) * 0.5, 0), [sx * 1.05, h + top_h, sz * 1.05]),
        f"{name}.hill": _anchor(P(0, h / 2, 0), [sx, h, sz]),
        f"{name}.walls": _anchor(P(0, h + wall_h / 2, 0), [sx, wall_h + 1.5, sz]),
        f"{name}.top": _anchor(P(0, h + 2.0, 0), [sx * 0.8, 4.0, sz * 0.8]),
    })
    if line:
        lx, ly, lz = ([p[k] for p in line] for k in range(3))
        anchors[f"{name}.path"] = _anchor(P((max(lx) + min(lx)) / 2, h * 0.45, (max(lz) + min(lz)) / 2),
                                          [max(lx) - min(lx) + 2, h, max(lz) - min(lz) + 2])
    if placed:
        px = [q[0] for q in placed]
        pz = [q[1] for q in placed]
        anchors[f"{name}.palaces"] = _anchor(P((max(px) + min(px)) / 2, h + top_h / 2, (max(pz) + min(pz)) / 2),
                                             [max(px) - min(px) + max(q[2] for q in placed), top_h + 1, max(pz) - min(pz) + max(q[3] for q in placed)])
    return [], objs, anchors


def temple(m: dict) -> tuple[list, list, dict]:
    """A two-tier plinth with front steps, a pillared mandapa (hall) in front, the sanctum behind it and a shikhara
    spire rising over the sanctum. Phases: plinth, hall, spire. Anchors: <id>, .hall, .spire."""
    P, rot, _ = _frame(m)
    name = str(m.get("id") or "temple")
    w = _num(m.get("w"), 10.0)
    d = _num(m.get("d"), w * 1.4)
    sh = _num(m.get("h"), w * 0.9)
    c = m.get("color", "#d9c3a0")
    ph = m.get("phases") or {}
    p1, p2 = 0.8, 0.7
    base = p1 + p2
    sw, sanc_h = w * 0.42, 3.2
    hall_w, hall_d, hall_h = w * 0.62, d * 0.34, 2.6
    objs = [
        {"type": "box", "pos": P(0, 0, 0), "rot": rot, "w": w, "h": p1, "d": d, "color": _shade(c, 0.92), "texture": "stone"},
        {"type": "box", "pos": P(0, p1, 0), "rot": rot, "w": w - 1.2, "h": p2, "d": d - 1.2, "color": c, "texture": "stone"},
        {"type": "stairs", "from": P(0, base, d / 2 - 0.7), "to": P(0, 0, d / 2 + 1.9), "width": 2.4, "steps": 7, "color": c},
        {"type": "pavilion", "pos": P(0, base, d * 0.17), "rot": rot, "w": _r(hall_w), "d": _r(hall_d), "h": hall_h,
         "cols": 4, "rows": 3, "color": c},
        {"type": "box", "pos": P(0, base + hall_h + 0.35, d * 0.17), "rot": rot, "w": _r(hall_w * 0.8), "h": 0.45,
         "d": _r(hall_d * 0.8), "color": _shade(c, 0.95), "texture": "stone"},
        {"type": "box", "pos": P(0, base + hall_h + 0.8, d * 0.17), "rot": rot, "w": _r(hall_w * 0.55), "h": 0.4,
         "d": _r(hall_d * 0.55), "color": _shade(c, 0.9), "texture": "stone"},
        {"type": "box", "pos": P(0, base, -d * 0.2), "rot": rot, "w": _r(sw), "h": sanc_h, "d": _r(sw), "color": c, "texture": "stone"},
        {"type": "box", "pos": P(0, base, -d * 0.2 + sw / 2 + 0.03), "rot": rot, "w": 0.9, "h": 1.9, "d": 0.08, "color": "#3a2a20"},
        {"type": "spire", "pos": P(0, base + sanc_h, -d * 0.2), "rot": rot, "w": _r(sw), "h": _r(sh), "tiers": 7, "color": c},
    ]
    builds = [("plinth", 0, 2, "rise"), ("plinth", 1, 2, "rise"), ("plinth", 1, 2, "stagger"), ("hall", 1, 3, "stagger"),
              ("hall", 2, 3, "rise"), ("hall", 2, 3, "rise"), ("hall", 0, 3, "rise"), ("hall", 0, 3, "rise"), ("spire", 0, 1, "stagger")]
    for o, (key, k, n, op) in zip(objs, builds):
        win = _slice(ph.get(key), k, n, 1.3)
        if win:
            o["build"] = {"op": op, **win}
    top = base + sanc_h + sh
    anchors = {name: _anchor(P(0, top * 0.45, 0), [w, top, d]),
               name + ".hall": _anchor(P(0, base + 1.5, d * 0.17), [hall_w, 3.5, hall_d]),
               name + ".spire": _anchor(P(0, base + sanc_h + sh / 2, -d * 0.2), [sw * 1.6, sh + 2, sw * 1.6])}
    return [], objs, anchors


MACRO_FUNCS = {"stepwell": stepwell, "pyramid": pyramid, "fort": fort, "temple": temple}


def _pyramid_primitive(o: dict) -> bool:
    """Older specs used "pyramid" for a plain four-sided cone {r, h}; keep reading those as a cone."""
    return o.get("type") == "pyramid" and "r" in o and not any(
        k in o for k in ("base", "height", "courses", "phases", "casing", "ramp", "capstone"))


# ------------------------------------------------------------------ anchors for objects with an id
def _object_anchor(o: dict) -> dict:
    t = o.get("type")
    p = o.get("pos") if isinstance(o.get("pos"), (list, tuple)) and len(o["pos"]) >= 3 else [o.get("x", 0), o.get("y", 0), o.get("z", 0)]
    x, y, z = (_num(v, 0.0) for v in p[:3])
    g = lambda k, d: _num(o.get(k), d)   # noqa: E731
    if t in ("hill", "cliff"):
        ol = o.get("outline") or [[-9, -9], [9, 9]]
        xs, zs = [q[0] for q in ol], [q[1] for q in ol]
        return _anchor([x + (max(xs) + min(xs)) / 2, y + g("h", 8) / 2, z + (max(zs) + min(zs)) / 2], [max(xs) - min(xs), g("h", 8), max(zs) - min(zs)])
    if t in ("wall", "stairs", "ramp"):
        def xyz(q, dflt):
            if not isinstance(q, (list, tuple)):
                return dflt
            return [_num(q[0], 0.0), 0.0, _num(q[1], 0.0)] if len(q) == 2 else [_num(q[0], 0.0), _num(q[1], 0.0), _num(q[2], 0.0)]
        a, b = xyz(o.get("from"), [0, 0, 0]), xyz(o.get("to"), [4, 0, 0])
        hh = g("h", 3) if t == "wall" else abs(a[1] - b[1]) + 1
        return _anchor([x + (a[0] + b[0]) / 2, y + min(a[1], b[1]) + hh / 2, z + (a[2] + b[2]) / 2],
                       [abs(a[0] - b[0]) + 2, hh, abs(a[2] - b[2]) + 2])
    if t in ("trees", "grass", "rocks", "town", "people"):
        ar = o.get("area") or [-3, -3, 3, 3]
        return _anchor([(ar[0] + ar[2]) / 2, g("y", 0) + 1.5, (ar[1] + ar[3]) / 2], [abs(ar[2] - ar[0]), 3, abs(ar[3] - ar[1])])
    if t == "water":
        return _anchor([(g("x0", -2) + g("x1", 2)) / 2, g("level", 0), (g("z0", -2) + g("z1", 2)) / 2],
                       [abs(g("x1", 2) - g("x0", -2)), 2, abs(g("z1", 2) - g("z0", -2))])
    if t in ("cylinder", "cone", "pyramid", "bastion", "mound", "dome", "sphere"):
        r, hh = g("r", 1.2), g("h", g("r", 1.2) * (2 if t == "sphere" else 1))
        return _anchor([x, y + hh / 2, z], [2 * r, hh, 2 * r])
    if t == "minaret":
        return _anchor([x, y + g("h", 10) / 2, z], [2.5, g("h", 10), 2.5])
    if t == "tomb":
        w = g("w", 8)
        hh = g("h", w * 0.72) + w * 0.16 + w * 0.65
        return _anchor([x, y + hh / 2, z], [g("plinth_w", w * 1.8), hh, g("plinth_w", w * 1.8)])
    if t == "boat":
        return _anchor([x, y + 1, z], [g("w", 2.2) + 1, 2.5, g("length", 7)])
    if t in ("person", "flag"):
        hh = g("h", 3) if t == "flag" else 1.5
        return _anchor([x, y + hh / 2, z], [2, hh, 2])
    if t == "blocks":
        sz = o.get("size") if isinstance(o.get("size"), list) else [1.2, 0.8, 0.9]
        cols, rows, layers = g("cols", g("count", 4)), g("rows", 2), g("layers", 1)
        return _anchor([x, y + layers * _num(sz[1], 0.8) / 2, z], [cols * (_num(sz[0], 1.2) + 0.14), layers * _num(sz[1], 0.8), rows * (_num(sz[2], 0.9) + 0.14)])
    dflt = {"palace": (6, 5, 4), "pavilion": (6, 3, 3), "spire": (3, 6, 3), "gate": (4, 3.4, 2), "house": (2.4, 2.8, 2.4),
            "tree": (2, 3.5, 2), "well": (3.2, 3, 1), "arch": (3, 4, 1), "pillar": (0.6, 3, 0.6), "sledge": (1.2, 1, 2)}
    w0, h0, d0 = dflt.get(t, (2, 2, 2))
    w, hh, d = g("w", w0), g("h", h0), g("d", w0 if t == "spire" else d0)
    return _anchor([x, y + hh / 2, z], [w, hh, d])


# ------------------------------------------------------------------ camera shots
def _aim(pos, target, fov: float) -> list:
    """A look point that puts `target` at SUBJECT_Y of the frame height (upper middle), seen from `pos`."""
    d = [target[i] - pos[i] for i in range(3)]
    dist = math.sqrt(sum(v * v for v in d)) or 1.0
    f = [v / dist for v in d]
    rx, rz = -f[2], f[0]                     # right = f x up, flattened
    rl = math.hypot(rx, rz)
    if rl < 1e-6:
        return [_r(v) for v in target]
    rx, rz = rx / rl, rz / rl
    up = [-rz * f[1], rz * f[0] - rx * f[2], rx * f[1]]     # camera up = right x f
    alpha = math.atan((1 - 2 * SUBJECT_Y) * math.tan(math.radians(fov) / 2))
    look = [f[i] * math.cos(alpha) - up[i] * math.sin(alpha) for i in range(3)]
    return [_r(pos[i] + look[i] * dist) for i in range(3)]


def _shot_key(shot: str, anc: dict, angle: float, k: dict, aspect: float, bounds=None) -> dict:
    S = SHOTS[shot]
    (cx, cy, cz), (sx, sy, sz) = anc["center"], anc["size"]
    fov = _num(k.get("fov"), S["fov"])
    vt = math.tan(math.radians(fov) / 2)
    ht = vt * aspect
    a, pitch = math.radians(angle), math.radians(S["pitch"])
    Wp = abs(sx * math.cos(a)) + abs(sz * math.sin(a))
    Dp = abs(sx * math.sin(a)) + abs(sz * math.cos(a))
    Hp = sy * math.cos(pitch) + Dp * math.sin(pitch) * 0.6
    dist = max(Wp / 2 / (S["fill"] * ht), Hp / 2 / (S["vmax"] * 2 * SUBJECT_Y * vt), 3.0) + Dp * 0.1
    if shot == "close":     # close, not inside it
        dist = max(dist, 2.0 * max(sy, min(sx, sz)))
    dist = _num(k.get("dist"), dist)
    if shot == "inside":
        rr = 0.25 * max(sx, sz)
        pos = [cx + math.sin(a) * rr, cy - sy / 2 + max(1.8, sy * 0.4), cz + math.cos(a) * rr]
        if "height" in k:
            pos[1] = cy + _num(k["height"], 0.0)
        look = [cx - math.sin(a) * rr, cy - sy * 0.1, cz - math.cos(a) * rr]
        return {"pos": [_r(v) for v in pos], "look": [_r(v) for v in look], "fov": fov}
    horiz, up = dist * math.cos(pitch), dist * math.sin(pitch)
    if shot == "low":
        up = (max(cy - sy / 2, 0.0 if cy > 0 else cy - sy / 2) + 1.0) - cy
    up = _num(k.get("height"), up)
    pos = [cx + math.sin(a) * horiz, cy + up, cz + math.cos(a) * horiz]
    if cy > 0 and pos[1] < 0.7:      # subject above the ground: keep the camera above it too
        pos[1] = 0.7
    if bounds and pos[1] < 4 and cy > 0:
        # a low camera outside the terrain block would look at its cut face: walk it in towards the subject and
        # widen the lens so the subject keeps its size in frame
        x0, x1, z0, z1 = bounds
        d0 = math.hypot(pos[0] - cx, pos[2] - cz)
        for _ in range(60):
            if x0 + 1 < pos[0] < x1 - 1 and z0 + 1 < pos[2] < z1 - 1:
                break
            pos[0] += (cx - pos[0]) * 0.05
            pos[2] += (cz - pos[2]) * 0.05
        d1 = math.hypot(pos[0] - cx, pos[2] - cz)
        if d1 < d0 * 0.98:
            fov = round(min(55.0, max(fov, 2 * math.degrees(math.atan(math.tan(math.radians(fov) / 2) * d0 / max(d1, 1.0))))), 1)
    return {"pos": [_r(v) for v in pos], "look": _aim(pos, [cx, cy, cz], fov), "fov": fov}


def _target(tg, anchors: dict, default: dict, size=None) -> dict:
    """An anchor for a shot: an id or macro anchor name, or [x, y, z]; `size` (a number or [w, h, d]) overrides."""
    if isinstance(tg, str) and tg in anchors:
        a = anchors[tg]
    elif isinstance(tg, (list, tuple)) and len(tg) == 3 and all(_num(v) is not None for v in tg):
        a = _anchor([_num(v) for v in tg], [8, 5, 8])
    else:
        a = default
    if _num(size) is not None:
        a = _anchor(a["center"], [_num(size)] * 3)
    elif isinstance(size, (list, tuple)) and len(size) == 3 and all(_num(v) is not None for v in size):
        a = _anchor(a["center"], [_num(v) for v in size])
    return a


def _main_anchor(anchors: dict) -> dict:
    for name, a in anchors.items():
        if "." not in name:
            return a
    return next(iter(anchors.values()), _anchor([0, 2, -6], [14, 6, 14]))


def resolve_camera(keys: list, anchors: dict, t_end: float | None = None, aspect: float = 9 / 16, terrain=None) -> list:
    """Turn shot keys into pos/look/fov keys (times must already be seconds). Plain pos/look keys pass through.
    An orbit sweeps `sweep` degrees (default 90) around its target from `at` until `until`, the next key or the end."""
    keys = sorted((k for k in keys if isinstance(k, dict)), key=lambda k: _num(k.get("at"), 0.0))
    default = _main_anchor(anchors)
    bounds = None
    if isinstance(terrain, dict):
        tw, tl_, cut = _num(terrain.get("width"), 40.0), _num(terrain.get("length"), 40.0), _num(terrain.get("cut"), 0.0)
        bounds = (-tw / 2, tw / 2, cut - tl_, cut)
    out = []
    for i, k in enumerate(keys):
        if "shot" not in k:
            out.append(k)
            continue
        at = _num(k.get("at"), 0.0)
        nxt = _num(keys[i + 1].get("at")) if i + 1 < len(keys) else None
        shot = k["shot"] if k.get("shot") in SHOTS else "medium"
        anc = _target(k.get("target"), anchors, default, k.get("size"))
        angle = _num(k.get("angle"), 30.0)
        if shot == "orbit":
            until = _num(k.get("until"), nxt if nxt is not None else (t_end if t_end is not None else at + 6.0))
            if nxt is not None:
                until = min(until, nxt)
            until = max(until, at + 0.5)
            sweep = _num(k.get("sweep"), 90.0)
            n = max(2, math.ceil(abs(sweep) / 18))
            last = n - 1 if (nxt is not None and until >= nxt - 1e-6) else n
            for j in range(last + 1):
                u = j / n
                key = _shot_key("orbit", anc, angle + sweep * u * u * (3 - 2 * u), k, aspect, bounds)
                key["at"] = round(at + (until - at) * u, 4)
                if j > 0:
                    key["ease"] = "linear"
                out.append(key)
            continue
        key = _shot_key(shot, anc, angle, k, aspect, bounds)
        key["at"] = at
        if k.get("ease"):
            key["ease"] = k["ease"]
        out.append(key)
    return out


def _auto_fog(w: dict):
    """Wide shots of big subjects stand far back: push the haze out so the subject is not washed out."""
    so = w.get("style_overrides") or {}
    if "fog" in so:
        return
    near0, far0 = FOG.get(w.get("style") or "desert", FOG["desert"])
    ds = [math.dist(k["pos"], k["look"]) for k in w.get("camera", []) if isinstance(k.get("pos"), list) and isinstance(k.get("look"), list)]
    if ds and max(ds) * 1.05 > near0:
        w["style_overrides"] = {**so, "fog": [round(max(ds) * 1.15, 1), round(max(far0, max(ds) * 3.2), 1)]}


def _extent(anchors: dict) -> float:
    ext = 0.0
    for a in anchors.values():
        (cx, _, cz), (sx, _, sz) = a["center"], a["size"]
        ext = max(ext, abs(cx) + sx / 2, abs(cz + 10) + sz / 2)
    return round(min(80.0, ext * 1.15), 1)


def expand(world: dict, t_end: float | None = None, aspect: float = 9 / 16, camera: bool = True) -> dict:
    """Expand macros into primitives and digs, fill in hill outlines and roads, collect anchors (macro anchors and
    objects with an "id") and, when `camera`, resolve shot keys into pos/look/fov."""
    w = copy.deepcopy(world)
    terrain = w.setdefault("terrain", {}) if w.get("terrain") is not False else None
    objs, anchors = [], {}
    for o in w.get("objects", []):
        if not isinstance(o, dict):
            continue
        if _pyramid_primitive(o):
            o = {**o, "type": "cone", "segments": 4}
        t = o.get("type")
        if t in MACRO_FUNCS:
            digs, more, anc = MACRO_FUNCS[t](o)
            if terrain is not None:
                terrain.setdefault("digs", []).extend(digs)
            objs.extend(more)
            anchors.update(anc)
            continue
        if t in ("hill", "cliff"):
            o = _prepare_hill(o)
        if o.get("id") is not None:
            anchors[str(o["id"])] = _object_anchor(o)
        objs.append(o)
    w["objects"] = objs
    w["anchors"] = anchors
    if camera and isinstance(w.get("camera"), list) and w["camera"]:
        shots = any(isinstance(k, dict) and "shot" in k for k in w["camera"])
        w["camera"] = resolve_camera(w["camera"], anchors, t_end, aspect, terrain)
        if shots:
            _auto_fog(w)
    if anchors:
        w["_extent"] = _extent(anchors)
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
    """Resolve scene references to seconds, then expand macros (they slice numeric phase windows) and frame shots."""
    idx = scene_index(spec)
    w = resolve(spec["world3d"], spec, tl, idx)
    t_end = tl[-1]["start"] + tl[-1]["dur"] if tl else None
    W, H = spec.get("_W"), spec.get("_H")
    aspect = (W / H) if W and H else {"16:9": 16 / 9, "1:1": 1.0, "4:5": 0.8}.get(spec.get("aspect"), 9 / 16)
    return expand(w, t_end=t_end, aspect=aspect)


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
        t = (o or {}).get("type") if isinstance(o, dict) else None
        if t not in KIT and t not in MACROS:
            errs.append(f"world3d object {k + 1}: unknown type {t!r} (use {sorted(KIT | MACROS)})")
        elif t == "mound" and _num(o.get("r"), 2.0) > 5:
            warns.append(f"world3d object {k + 1}: a mound of r {o.get('r')} reads as a flat blob; use hill or cliff for terrain")
    ids = [str(o["id"]) for o in objs if isinstance(o, dict) and o.get("id") is not None]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        warns.append(f"world3d: id {i!r} is used more than once")
    anchors = {}
    try:
        anchors = expand(world, camera=False).get("anchors", {})
    except Exception as e:     # bad macro parameters
        errs.append(f"world3d objects could not be expanded: {type(e).__name__}: {e}")
    cam = world.get("camera", [])
    if not isinstance(cam, list) or not cam:
        warns.append("world3d.camera has no keys; a default three-quarter view will be used")
        cam = []
    for i, key in enumerate(cam):
        where = f"world3d camera key {i + 1}"
        if not isinstance(key, dict):
            errs.append(f"{where}: must be an object")
            continue
        if "shot" in key:
            if key["shot"] not in SHOTS:
                errs.append(f"{where}: unknown shot {key['shot']!r} (use {sorted(SHOTS)})")
            tg = key.get("target")
            if tg is None:
                warns.append(f"{where}: shot has no target; it will frame the main subject")
            elif isinstance(tg, str):
                if tg not in anchors:
                    errs.append(f"{where}: unknown target {tg!r} (known: {', '.join(sorted(anchors)) or 'none'})")
            elif not (isinstance(tg, list) and len(tg) == 3 and all(_num(v) is not None for v in tg)):
                errs.append(f"{where}: target must be an object id, a macro anchor or [x, y, z]")
            for f in ("angle", "dist", "height", "fov", "sweep"):
                if f in key and _num(key[f]) is None:
                    errs.append(f"{where}: {f} must be a number")
        elif "pos" not in key and "follow" not in key:
            warns.append(f"{where}: give a shot and target (or pos and look)")

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
