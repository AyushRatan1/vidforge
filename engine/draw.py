"""Procedural drawing: backgrounds, planets, character rigs, props, particles, text, images, SVG."""
from __future__ import annotations

import math
import re
import os
import random
from functools import lru_cache

import skia

from .fonts import hex_color as C
from .fonts import text_block

TAU = 2 * math.pi


# ---------------------------------------------------------------- helpers
def fill(color, alpha=1.0, aa=True):
    p = skia.Paint(AntiAlias=aa)
    p.setColor(C(color, alpha) if isinstance(color, str) else color)
    return p


def stroke(color, width, alpha=1.0, cap="round"):
    p = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width)
    p.setColor(C(color, alpha))
    p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def radial(cx, cy, r, colors, pos=None, alpha=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), max(1e-3, r), [C(c, alpha) for c in colors], pos))
    return p


def linear(x0, y0, x1, y1, colors, pos=None, alpha=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear(
        [skia.Point(x0, y0), skia.Point(x1, y1)], [C(c, alpha) for c in colors], pos))
    return p


def glow(color, sigma, alpha=1.0):
    p = fill(color, alpha)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(0.1, sigma)))
    return p


def mix(c1: str, c2: str, u: float) -> str:
    a, b = c1.lstrip("#"), c2.lstrip("#")
    r = [int(int(a[i:i + 2], 16) * (1 - u) + int(b[i:i + 2], 16) * u) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(r)


def shade(c: str, u: float) -> str:
    """u<0 darken, u>0 lighten."""
    return mix(c, "#000000", -u) if u < 0 else mix(c, "#ffffff", u)


def star_path(cx, cy, r_out, r_in, points=5, rot=-90):
    path = skia.Path()
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / points)
        pt = (cx + r * math.cos(a), cy + r * math.sin(a))
        path.moveTo(*pt) if i == 0 else path.lineTo(*pt)
    path.close()
    return path


def heart_path(cx, cy, s):
    p = skia.Path()
    p.moveTo(cx, cy + s * 0.9)
    p.cubicTo(cx - s * 1.6, cy - s * 0.1, cx - s * 0.8, cy - s * 1.3, cx, cy - s * 0.45)
    p.cubicTo(cx + s * 0.8, cy - s * 1.3, cx + s * 1.6, cy - s * 0.1, cx, cy + s * 0.9)
    p.close()
    return p


# ---------------------------------------------------------------- backgrounds
def draw_background(cv: skia.Canvas, bg: dict, t: float, W: int, H: int, ctx: dict):
    kind = (bg or {}).get("type", "gradient")
    fn = BACKGROUNDS.get(kind, bg_gradient)
    fn(cv, bg or {}, t, W, H, ctx)


def bg_solid(cv, bg, t, W, H, ctx):
    cv.drawRect(skia.Rect(0, 0, W, H), fill(bg.get("color", "#101020")))


def bg_gradient(cv, bg, t, W, H, ctx):
    cols = bg.get("colors") or ["#1e3c72", "#2a5298"]
    if len(cols) == 1:
        cols = [cols[0], cols[0]]
    cv.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, W * 0.25, H, cols))
    _vignette(cv, W, H, bg.get("vignette", 0.35))


def _vignette(cv, W, H, strength):
    if strength <= 0:
        return
    cv.drawRect(skia.Rect(0, 0, W, H),
                radial(W / 2, H / 2, max(W, H) * 0.75, ["#00000000", "#000000"], [0.55, 1.0], alpha=strength))


def bg_space(cv, bg, t, W, H, ctx):
    top, bot = (bg.get("colors") or ["#03020c", "#140b33"])[:2]
    cv.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [top, bot]))
    rnd = random.Random(bg.get("seed", 7))
    for i, col in enumerate(bg.get("nebula", ["#5b2a86", "#1b4b8a", "#a3316f"])):
        cx = (0.2 + 0.6 * rnd.random()) * W + math.sin(t * 0.07 + i) * W * 0.03
        cy = (0.15 + 0.7 * rnd.random()) * H + math.cos(t * 0.05 + i) * H * 0.02
        r = (0.35 + 0.3 * rnd.random()) * W
        cv.drawCircle(cx, cy, r, radial(cx, cy, r, [col, col + "00"], alpha=0.55))
    n = int(bg.get("stars", 260))
    drift = float(bg.get("drift", 0.004))
    for i in range(n):
        x = (rnd.random() * W + t * drift * W * (0.3 + rnd.random())) % W
        y = rnd.random() * H
        s = rnd.random() ** 3 * 3.2 + 0.7
        tw = 0.55 + 0.45 * math.sin(t * (1 + rnd.random() * 2.5) + rnd.random() * TAU)
        a = (0.35 + 0.65 * rnd.random()) * tw
        col = rnd.choice(["#ffffff", "#ffffff", "#cfe3ff", "#ffe9c4"])
        if s > 2.8:
            cv.drawCircle(x, y, s * 3.2, glow(col, s * 1.6, a * 0.5))
        cv.drawCircle(x, y, s, fill(col, a))
    if bg.get("shooting", True):
        period = 4.5
        k = int(t // period)
        u = (t % period) / 0.9
        if u < 1:
            r2 = random.Random(k * 97 + 3)
            sx, sy = r2.uniform(0.1, 0.8) * W, r2.uniform(0.05, 0.4) * H
            ex, ey = sx + W * 0.35, sy + W * 0.18
            px, py = sx + (ex - sx) * u, sy + (ey - sy) * u
            tail = 0.25
            qx, qy = sx + (ex - sx) * max(0, u - tail), sy + (ey - sy) * max(0, u - tail)
            p = linear(qx, qy, px, py, ["#ffffff00", "#ffffff"], alpha=1 - u)
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(3)
            p.setStrokeCap(skia.Paint.kRound_Cap)
            cv.drawLine(qx, qy, px, py, p)


def _cloud(cv, cx, cy, s, color="#ffffff", alpha=1.0):
    for dx, dy, r in ((-0.55, 0.1, 0.42), (0, -0.15, 0.55), (0.55, 0.05, 0.45), (0.25, 0.25, 0.4), (-0.25, 0.25, 0.4)):
        cv.drawCircle(cx + dx * s, cy + dy * s, r * s, fill(color, alpha))


def bg_sky(cv, bg, t, W, H, ctx):
    tod = bg.get("time", "day")
    cols = bg.get("colors") or {
        "day": ["#4fb3ff", "#bfe8ff"],
        "sunset": ["#3a1c71", "#d76d77", "#ffaf7b"],
        "night": ["#0b1033", "#273469"],
        "dawn": ["#f6d365", "#fda085"],
    }.get(tod, ["#4fb3ff", "#bfe8ff"])
    cv.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, 0, H, cols))
    if tod == "night":
        bg_space_stars_only(cv, t, W, H, 120)
    rnd = random.Random(bg.get("seed", 3))
    for i in range(int(bg.get("clouds", 4))):
        s = W * (0.08 + 0.07 * rnd.random())
        x = ((rnd.random() * 1.4 - 0.2) * W + t * W * 0.012 * (0.5 + rnd.random())) % (W * 1.4) - W * 0.2
        y = (0.06 + 0.4 * rnd.random()) * H
        _cloud(cv, x, y, s, "#ffffff", 0.9 if tod == "day" else 0.35)
    if bg.get("ground", True):
        g = bg.get("ground_colors") or (["#7ccf5a", "#4fa63a"] if tod in ("day", "dawn") else ["#2d4a3e", "#1b2f27"])
        for layer, (col, base, amp, freq) in enumerate(((g[0], 0.80, 0.025, 2.2), (g[-1], 0.86, 0.02, 3.1))):
            path = skia.Path()
            path.moveTo(0, H)
            for i in range(0, 41):
                x = W * i / 40
                y = H * base + H * amp * math.sin(i / 40 * TAU * freq / 2 + layer * 1.7)
                path.lineTo(x, y)
            path.lineTo(W, H)
            path.close()
            cv.drawPath(path, fill(col))


def bg_space_stars_only(cv, t, W, H, n):
    rnd = random.Random(11)
    for _ in range(n):
        x, y = rnd.random() * W, rnd.random() * H * 0.7
        a = 0.5 + 0.5 * math.sin(t * (1 + rnd.random() * 2) + rnd.random() * TAU)
        cv.drawCircle(x, y, rnd.random() * 2 + 0.6, fill("#ffffff", a))


def bg_sunburst(cv, bg, t, W, H, ctx):
    a, b = (bg.get("colors") or ["#ffd54f", "#ffb300"])[:2]
    cx, cy = bg.get("center", [0.5, 0.42])
    cx, cy = cx * W, cy * H
    cv.drawRect(skia.Rect(0, 0, W, H), fill(b))
    rays = int(bg.get("rays", 16))
    rot = t * float(bg.get("speed", 8))
    R = max(W, H) * 1.2
    for i in range(rays):
        a0 = math.radians(rot + i * 360 / rays)
        a1 = math.radians(rot + (i + 0.5) * 360 / rays)
        p = skia.Path()
        p.moveTo(cx, cy)
        p.lineTo(cx + R * math.cos(a0), cy + R * math.sin(a0))
        p.lineTo(cx + R * math.cos(a1), cy + R * math.sin(a1))
        p.close()
        cv.drawPath(p, fill(a))
    cv.drawCircle(cx, cy, W * 0.5, radial(cx, cy, W * 0.5, ["#ffffff", "#ffffff00"], alpha=0.35))
    _vignette(cv, W, H, 0.25)


def bg_paper(cv, bg, t, W, H, ctx):
    base = bg.get("color", "#f6e7c8")
    cv.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [shade(base, 0.08), shade(base, -0.06)]))
    rnd = random.Random(5)
    for _ in range(900):
        cv.drawCircle(rnd.random() * W, rnd.random() * H, rnd.random() * 1.6, fill("#7a5c2e", 0.06))
    _vignette(cv, W, H, bg.get("vignette", 0.45))


def bg_grid(cv, bg, t, W, H, ctx):
    top, bot = (bg.get("colors") or ["#050b1f", "#0d1b3e"])[:2]
    line = bg.get("line", "#2bd4ff")
    cv.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, 0, H, [top, bot]))
    step = W / 12
    off = (t * step * 0.25) % step
    p = stroke(line, 1.5, 0.12)
    y = -step + off
    while y < H:
        cv.drawLine(0, y, W, y, p)
        y += step
    x = 0
    while x <= W:
        cv.drawLine(x, 0, x, H, p)
        x += step
    cv.drawCircle(W / 2, H * 0.45, W * 0.7, radial(W / 2, H * 0.45, W * 0.7, [line, line + "00"], alpha=0.12))


def bg_underwater(cv, bg, t, W, H, ctx):
    cv.drawRect(skia.Rect(0, 0, W, H), linear(0, 0, 0, H, bg.get("colors") or ["#38c4e6", "#0a4b8f", "#06264f"]))
    for i in range(5):
        x = W * (0.1 + 0.2 * i) + math.sin(t * 0.4 + i) * W * 0.04
        p = skia.Path()
        p.moveTo(x - W * 0.03, 0)
        p.lineTo(x + W * 0.03, 0)
        p.lineTo(x + W * 0.14, H * 0.8)
        p.lineTo(x - W * 0.02, H * 0.8)
        p.close()
        cv.drawPath(p, linear(0, 0, 0, H * 0.8, ["#ffffff", "#ffffff00"], alpha=0.12))
    draw_particles(cv, {"kind": "bubbles", "count": 26, "seed": 9}, t, W, H)
    cv.drawRect(skia.Rect(0, H * 0.88, W, H), fill("#e8d29a"))


def bg_image(cv, bg, t, W, H, ctx):
    img = load_image(bg.get("path", ""))
    if img is None:
        return bg_gradient(cv, {"colors": ["#222", "#000"]}, t, W, H, ctx)
    z0, z1 = bg.get("zoom", [1.0, 1.12])
    dur = max(0.1, ctx.get("scene_dur", 5))
    z = z0 + (z1 - z0) * min(1, t / dur)
    _draw_cover(cv, img, W, H, z, bg.get("focus", [0.5, 0.5]))
    if bg.get("darken", 0.25):
        cv.drawRect(skia.Rect(0, 0, W, H), fill("#000000", float(bg.get("darken", 0.25))))


def bg_footage(cv, bg, t, W, H, ctx):
    """Real stock video. The moving picture itself is composited by ffmpeg under the Skia frames (see
    Renderer.encode_scene), so for the live scene this draws only the tint rect and the canvas stays
    transparent elsewhere. When the scene is drawn as the outgoing scene of a transition (ctx["as_prev"]),
    or no clip was resolved, a still (`_last_frame`) or the fallback background stands in for the video."""
    if not bg.get("_file"):
        fb = bg.get("fallback") or {"type": "gradient", "colors": ["#1d2742", "#121a2e"]}
        draw_background(cv, fb if fb.get("type") != "footage" else {"type": "gradient"}, t, W, H, ctx)
    elif ctx.get("as_prev"):
        img = load_image(bg.get("_last_frame", ""))
        if img is not None:
            _draw_cover(cv, img, W, H)
        else:
            cv.drawRect(skia.Rect(0, 0, W, H), fill("#000000"))
    dim = float(bg.get("dim", 0.45))
    if dim > 0:
        cv.drawRect(skia.Rect(0, 0, W, H), fill(bg.get("tint", "#000000"), min(0.9, dim)))


BACKGROUNDS = {
    "solid": bg_solid, "gradient": bg_gradient, "space": bg_space, "sky": bg_sky,
    "sunburst": bg_sunburst, "paper": bg_paper, "grid": bg_grid, "underwater": bg_underwater,
    "image": bg_image, "footage": bg_footage,
    "world3d": bg_footage,   # resolved into a prepared clip by engine/world3d.py; draws its fallback if that fails
}


# ---------------------------------------------------------------- images & svg
@lru_cache(maxsize=64)
def load_image(path: str):
    if not path or not os.path.exists(path):
        return None
    return skia.Image.open(path)


def _draw_cover(cv, img, W, H, zoom=1.0, focus=(0.5, 0.5)):
    iw, ih = img.width(), img.height()
    s = max(W / iw, H / ih) * zoom
    dw, dh = iw * s, ih * s
    x = (W - dw) * focus[0]
    y = (H - dh) * focus[1]
    cv.drawImageRect(img, skia.Rect(x, y, x + dw, y + dh), skia.SamplingOptions(skia.FilterMode.kLinear))


@lru_cache(maxsize=128)
def _svg_dom(markup: str):
    data = markup.encode("utf-8")
    dom = skia.SVGDOM.MakeFromStream(skia.MemoryStream(data))
    return dom


def _svg_viewbox(markup: str):
    import re
    m = re.search(r'viewBox\s*=\s*"([\d.\-\s,]+)"', markup)
    if m:
        v = [float(x) for x in re.split(r"[\s,]+", m.group(1).strip())]
        if len(v) == 4:
            return v[2], v[3]
    w = re.search(r'\swidth\s*=\s*"([\d.]+)', markup)
    h = re.search(r'\sheight\s*=\s*"([\d.]+)', markup)
    return (float(w.group(1)) if w else 100.0, float(h.group(1)) if h else 100.0)


def draw_svg(cv, markup: str, w_px: float):
    if not markup:
        return
    dom = _svg_dom(markup)
    if dom is None:
        return
    vw, vh = _svg_viewbox(markup)
    s = w_px / vw
    dom.setContainerSize(skia.Size(vw, vh))
    cv.save()
    cv.scale(s, s)
    cv.translate(-vw / 2, -vh / 2)
    dom.render(cv)
    cv.restore()


# ---------------------------------------------------------------- planets
PLANETS = {
    "earth": {"base": "#2b7bd6", "light": "#6ec1ff", "atmo": "#7fd3ff"},
    "mars": {"base": "#c1440e", "light": "#f08a4b", "atmo": "#ff9b6a"},
    "moon": {"base": "#9a9a9a", "light": "#e6e6e6", "atmo": None},
    "mercury": {"base": "#8c7f75", "light": "#cfc3b8", "atmo": None},
    "venus": {"base": "#d8a657", "light": "#f7e0a3", "atmo": "#ffe7a8"},
    "jupiter": {"base": "#c99b6d", "light": "#f1d7b0", "atmo": "#ffe0b8"},
    "saturn": {"base": "#d9b56f", "light": "#f6e3b2", "atmo": "#ffeec2"},
    "uranus": {"base": "#6fd3d6", "light": "#c4f6f3", "atmo": "#bffcff"},
    "neptune": {"base": "#2f55d4", "light": "#7a9cff", "atmo": "#8fb0ff"},
    "pluto": {"base": "#c8a98a", "light": "#efe0cf", "atmo": None},
    "sun": {"base": "#ff9d00", "light": "#fff2a8", "atmo": "#ffb300"},
    "exoplanet": {"base": "#7b3fa0", "light": "#d39bff", "atmo": "#c58bff"},
}


def draw_neutron_star(cv, el, t, r):
    """Tiny, blinding star with optional rotating pulsar beams."""
    if el.get("beams", True):
        ang = t * float(el.get("beam_speed", 90)) + float(el.get("beam_angle", 30))
        L = r * float(el.get("beam_length", 9))
        for k in (0, 180):
            cv.save()
            cv.rotate(ang + k)
            p = skia.Path()
            p.moveTo(0, -r * 0.25)
            p.lineTo(L, -r * 1.6)
            p.lineTo(L, r * 1.6)
            p.lineTo(0, r * 0.25)
            p.close()
            paint = linear(0, 0, L, 0, ["#e9f7ff", "#9fd8ff00"], alpha=0.85)
            paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.25))
            cv.drawPath(p, paint)
            cv.restore()
    for k in range(3):
        rr = r * (1.8 + k * 0.7)
        cv.save()
        cv.rotate(float(el.get("beam_angle", 30)) + 90)
        cv.drawOval(skia.Rect(-rr * 0.45, -rr, rr * 0.45, rr), stroke("#9fd8ff", r * 0.04, 0.25 - k * 0.06))
        cv.restore()
    pulse = 1 + 0.06 * math.sin(t * 9)
    cv.drawCircle(0, 0, r * 3.2 * pulse, radial(0, 0, r * 3.2 * pulse, ["#bfe6ff", "#5aa9ff00"], alpha=0.6))
    cv.drawCircle(0, 0, r, radial(-r * 0.2, -r * 0.2, r * 1.2, ["#ffffff", "#d6efff", "#7cc4ff"], [0, 0.55, 1]))


def draw_planet(cv, el, t, r):
    style = el.get("style", "earth")
    if style == "black_hole":
        return draw_black_hole(cv, el, t, r)
    if style in ("neutron_star", "pulsar"):
        return draw_neutron_star(cv, el, t, r)
    pal = dict(PLANETS.get(style, PLANETS["earth"]))
    if el.get("color"):
        pal["base"] = el["color"]
        pal["light"] = shade(el["color"], 0.45)
    spin = t * float(el.get("spin_speed", 0.08))
    if style == "sun":
        pulse = 1 + 0.03 * math.sin(t * 2.2)
        cv.drawCircle(0, 0, r * 2.1 * pulse, radial(0, 0, r * 2.1 * pulse, ["#ffcc33", "#ff660000"], alpha=0.55))
        cv.drawCircle(0, 0, r * 1.35, radial(0, 0, r * 1.35, ["#ffe680", "#ff990000"], alpha=0.8))
    elif pal.get("atmo") and el.get("glow", True):
        cv.drawCircle(0, 0, r * 1.18, radial(0, 0, r * 1.18, [pal["atmo"], pal["atmo"] + "00"], [0.82, 1.0], alpha=0.55))
    has_rings = el.get("rings", style == "saturn")
    if has_rings:
        _rings(cv, r, back=True, color=el.get("ring_color", "#e8d6a8"))
    cv.drawCircle(0, 0, r, radial(-r * 0.35, -r * 0.4, r * 1.6, [pal["light"], pal["base"], shade(pal["base"], -0.35)], [0, 0.45, 1]))
    clip = skia.Path()
    clip.addCircle(0, 0, r)
    cv.save()
    cv.clipPath(clip, doAntiAlias=True)
    rnd = random.Random(hash(style) % 1000)
    if style in ("jupiter", "saturn", "uranus", "neptune", "venus", "exoplanet"):
        bands = 9 if style in ("jupiter", "saturn") else 5
        for i in range(bands):
            y = -r + (i + 0.5) * 2 * r / bands + math.sin(i * 1.3) * r * 0.03
            h = 2 * r / bands * (0.35 + 0.4 * rnd.random())
            col = shade(pal["base"], (rnd.random() - 0.5) * 0.5)
            path = skia.Path()
            path.moveTo(-r, y)
            for k in range(25):
                x = -r + 2 * r * k / 24
                path.lineTo(x, y + math.sin(k * 0.8 + spin * 6 + i) * h * 0.15)
            path.lineTo(r, y + h)
            path.lineTo(-r, y + h)
            path.close()
            cv.drawPath(path, fill(col, 0.55))
        if style == "jupiter":
            sx = ((0.3 + spin * 0.6) % 2.4 - 1.2) * r
            cv.drawOval(skia.Rect(sx - r * 0.2, r * 0.18, sx + r * 0.2, r * 0.36), fill("#b5532c", 0.85))
    elif style == "earth":
        land = ["#3f9d4a", "#4caf50", "#6b8e3d", "#c2a25a"]
        for i in range(8):
            cx = ((rnd.random() * 2.6 + spin) % 2.6 - 1.3) * r
            cy = (rnd.random() * 1.4 - 0.7) * r
            col = land[i % len(land)] if i % 3 else land[0]
            for j in range(9):
                ang = rnd.random() * TAU
                d = rnd.random() * r * 0.2
                cv.drawCircle(cx + math.cos(ang) * d * 1.3, cy + math.sin(ang) * d * 0.8,
                              r * (0.045 + 0.07 * rnd.random()), fill(col))
        for i in range(9):
            cx = ((rnd.random() * 2.6 + spin * 1.35) % 2.6 - 1.3) * r
            cy = (rnd.random() * 1.7 - 0.85) * r
            for j in range(3):
                w = r * (0.07 + 0.08 * rnd.random())
                ox = (j - 1) * w * 0.9
                oy = (rnd.random() - 0.5) * r * 0.03
                cv.drawOval(skia.Rect(cx + ox - w, cy + oy - w * 0.28, cx + ox + w, cy + oy + w * 0.28), fill("#ffffff", 0.55))
        cv.drawOval(skia.Rect(-r * 0.55, -r * 1.04, r * 0.55, -r * 0.84), fill("#ffffff", 0.85))
    elif style in ("moon", "mercury", "mars", "pluto"):
        for i in range(14):
            cx = ((rnd.random() * 2.6 + spin) % 2.6 - 1.3) * r
            cy = (rnd.random() * 1.8 - 0.9) * r
            cr = r * (0.05 + 0.12 * rnd.random())
            cv.drawCircle(cx, cy, cr, fill(shade(pal["base"], -0.25), 0.55))
            cv.drawCircle(cx - cr * 0.15, cy - cr * 0.15, cr * 0.75, fill(shade(pal["base"], 0.1), 0.4))
        if style == "mars":
            cv.drawOval(skia.Rect(-r * 0.4, -r * 1.02, r * 0.4, -r * 0.85), fill("#ffffff", 0.85))
    elif style == "sun":
        for i in range(10):
            cx = ((rnd.random() * 2.6 + spin * 0.5) % 2.6 - 1.3) * r
            cy = (rnd.random() * 1.8 - 0.9) * r
            cv.drawCircle(cx, cy, r * 0.12, fill("#ffffff", 0.18 + 0.1 * math.sin(t * 3 + i)))
    cv.restore()
    if style != "sun":
        # night side shading
        cv.drawCircle(0, 0, r, radial(r * 0.45, r * 0.5, r * 1.5, ["#00000000", "#000000"], [0.35, 1.0], alpha=0.55))
    if has_rings:
        _rings(cv, r, back=False, color=el.get("ring_color", "#e8d6a8"))
    if el.get("face"):
        draw_face(cv, el, t, r * 0.9, el.get("_amp", 0.0))


def _rings(cv, r, back, color):
    cv.save()
    cv.rotate(-14)
    rect_clip = skia.Rect(-r * 3, -r * 3, r * 3, 0) if back else skia.Rect(-r * 3, 0, r * 3, r * 3)
    cv.clipRect(rect_clip, doAntiAlias=True)
    for k, (rr, w, a) in enumerate(((2.05, 0.10, 0.55), (1.8, 0.16, 0.8), (1.55, 0.09, 0.6))):
        p = stroke(shade(color, -0.1 * k), r * w, a)
        cv.drawOval(skia.Rect(-r * rr, -r * rr * 0.28, r * rr, r * rr * 0.28), p)
    cv.restore()


def draw_black_hole(cv, el, t, r):
    cv.drawCircle(0, 0, r * 2.6, radial(0, 0, r * 2.6, ["#ff8a3d", "#ff8a3d00"], [0.2, 1], alpha=0.35))
    cv.save()
    cv.rotate(-12)
    for k in range(6):
        rr = r * (1.4 + k * 0.22)
        a = 0.85 - k * 0.12
        p = stroke(mix("#ffd27a", "#ff5a1f", k / 6), r * 0.16, a)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.04))
        sweep = (t * 60 * (1 + k * 0.2)) % 360
        cv.drawArc(skia.Rect(-rr, -rr * 0.32, rr, rr * 0.32), sweep, 300, False, p)
    cv.restore()
    cv.drawCircle(0, 0, r * 1.06, stroke("#ffe2a8", r * 0.08, 0.9))
    cv.drawCircle(0, 0, r, fill("#000000"))


# ---------------------------------------------------------------- characters
SPECIES = {"blob", "cat", "bunny", "bear", "elephant", "owl", "robot", "kid", "astronaut", "monkey", "lion"}


def _blink(t, seed):
    period = 3.1 + (seed % 7) * 0.23
    ph = (t + seed * 0.37) % period
    if ph < 0.14:
        return max(0.08, abs(ph - 0.07) / 0.07)
    return 1.0


def draw_face(cv, el, t, r, amp, skin=None):
    expr = el.get("expression", "happy")
    seed = hash(el.get("id", "x")) % 97
    look = el.get("look", [0, 0])
    eye_y = -r * 0.12
    ex = r * 0.34
    erx, ery = r * 0.17, r * 0.22
    if expr == "surprised":
        erx, ery = r * 0.2, r * 0.27
    bl = _blink(t, seed) if el.get("blink", True) else 1.0
    for sgn in (-1, 1):
        cx = sgn * ex
        if expr == "wink" and sgn == 1:
            cv.drawArc(skia.Rect(cx - erx, eye_y - ery * 0.3, cx + erx, eye_y + ery * 0.6), 200, 140, False, stroke("#1b1b2f", r * 0.06))
            continue
        rect = skia.Rect(cx - erx, eye_y - ery * bl, cx + erx, eye_y + ery * bl)
        cv.drawOval(rect, fill("#ffffff"))
        if bl > 0.3:
            px = cx + look[0] * erx * 0.4
            py = eye_y + look[1] * ery * 0.4 + ery * 0.12
            pr = erx * 0.62
            cv.drawCircle(px, py, pr * bl ** 0.5, fill("#1b1b2f"))
            cv.drawCircle(px - pr * 0.35, py - pr * 0.4, pr * 0.32, fill("#ffffff"))
            cv.drawCircle(px + pr * 0.3, py + pr * 0.3, pr * 0.14, fill("#ffffff", 0.8))
        if expr == "sad":
            cv.drawLine(cx - erx, eye_y - ery * 1.25 + (sgn * r * 0.05), cx + erx, eye_y - ery * 1.25 - (sgn * r * 0.05), stroke("#1b1b2f", r * 0.05))
        if expr == "thinking" and sgn == -1:
            cv.drawLine(cx - erx, eye_y - ery * 1.35, cx + erx, eye_y - ery * 1.15, stroke("#1b1b2f", r * 0.05))
    # cheeks
    if el.get("blush", True):
        for sgn in (-1, 1):
            cv.drawOval(skia.Rect(sgn * r * 0.55 - r * 0.13, r * 0.12, sgn * r * 0.55 + r * 0.13, r * 0.24), fill("#ff6b9a", 0.45))
    # mouth
    my = r * 0.28
    talking = el.get("talking", False) and amp > 0.04
    if talking or expr == "surprised":
        o = max(0.25, min(1.0, amp * 1.6)) if talking else 0.7
        w = r * (0.22 if expr != "surprised" else 0.14)
        h = r * 0.22 * o
        rect = skia.Rect(-w, my - h * 0.4, w, my + h)
        cv.drawOval(rect, fill("#5a1a2b"))
        cv.save()
        clip = skia.Path()
        clip.addOval(rect)
        cv.clipPath(clip, doAntiAlias=True)
        cv.drawOval(skia.Rect(-w * 0.7, my + h * 0.35, w * 0.7, my + h * 1.4), fill("#ff7b8f"))
        cv.restore()
    elif expr == "sad":
        cv.drawArc(skia.Rect(-r * 0.18, my, r * 0.18, my + r * 0.2), 200, 140, False, stroke("#1b1b2f", r * 0.055))
    else:
        cv.drawArc(skia.Rect(-r * 0.2, my - r * 0.12, r * 0.2, my + r * 0.12), 20, 140, False, stroke("#1b1b2f", r * 0.055))


def draw_character(cv, el, t, r, amp):
    sp = el.get("species", "blob")
    col = el.get("color", {"cat": "#ffa94d", "bunny": "#f3f0ff", "bear": "#a9744f", "elephant": "#9fb3c8",
                           "owl": "#8d6e63", "robot": "#b0bec5", "kid": "#f1c27d", "astronaut": "#f5f7fa",
                           "monkey": "#8d5a3b", "lion": "#f4b942"}.get(sp, "#7c5cff"))
    dark = shade(col, -0.3)
    belly = shade(col, 0.45)
    seed = hash(el.get("id", "c")) % 50
    wave = el.get("wave", False)
    # feet
    for sgn in (-1, 1):
        cv.drawOval(skia.Rect(sgn * r * 0.45 - r * 0.25, r * 0.82, sgn * r * 0.45 + r * 0.25, r * 1.08), fill(dark))
    # ears / back features
    if sp == "elephant":
        for sgn in (-1, 1):
            cv.drawOval(skia.Rect(sgn * r * 0.95 - r * 0.55, -r * 0.6, sgn * r * 0.95 + r * 0.55, r * 0.45), fill(shade(col, -0.1)))
            cv.drawOval(skia.Rect(sgn * r * 0.95 - r * 0.38, -r * 0.45, sgn * r * 0.95 + r * 0.38, r * 0.3), fill("#f7b6c2", 0.6))
    elif sp == "bunny":
        for sgn in (-1, 1):
            sw = math.sin(t * 2 + sgn) * 4
            cv.save()
            cv.rotate(sgn * 12 + sw)
            cv.drawOval(skia.Rect(sgn * r * 0.38 - r * 0.17, -r * 1.85, sgn * r * 0.38 + r * 0.17, -r * 0.6), fill(col))
            cv.drawOval(skia.Rect(sgn * r * 0.38 - r * 0.09, -r * 1.7, sgn * r * 0.38 + r * 0.09, -r * 0.75), fill("#ffb3c7"))
            cv.restore()
    elif sp in ("bear", "monkey"):
        for sgn in (-1, 1):
            ex = sgn * r * (0.72 if sp == "bear" else 0.98)
            ey = -r * (0.72 if sp == "bear" else 0.05)
            cv.drawCircle(ex, ey, r * 0.27, fill(col))
            cv.drawCircle(ex, ey, r * 0.15, fill(belly))
    elif sp == "lion":
        n = 18
        for i in range(n):
            a = TAU * i / n + math.sin(t * 1.5) * 0.03
            cv.drawCircle(math.cos(a) * r * 0.95, math.sin(a) * r * 0.95 - r * 0.05, r * 0.33, fill("#c76b1b"))
    # arms
    for sgn in (-1, 1):
        ang = sgn * 25
        if wave and sgn == 1:
            ang = -120 + 25 * math.sin(t * 9)
        cv.save()
        cv.translate(sgn * r * 0.86, r * 0.25)
        cv.rotate(ang)
        cv.drawOval(skia.Rect(-r * 0.14, -r * 0.05, r * 0.14, r * 0.5), fill(dark if sp != "astronaut" else "#dfe6ee"))
        cv.restore()
    # body
    if sp == "robot":
        body = skia.RRect.MakeRectXY(skia.Rect(-r * 0.95, -r * 0.95, r * 0.95, r * 0.95), r * 0.3, r * 0.3)
        cv.drawRRect(body, linear(0, -r, 0, r, [shade(col, 0.25), shade(col, -0.15)]))
        cv.drawLine(0, -r * 0.95, 0, -r * 1.3, stroke(dark, r * 0.06))
        cv.drawCircle(0, -r * 1.35, r * 0.1, glow("#ff4d6d", r * 0.04, 0.6 + 0.4 * math.sin(t * 6)))
        cv.drawCircle(0, -r * 1.35, r * 0.08, fill("#ff4d6d"))
    else:
        bw, bh = r, r
        if sp == "kid":
            # shirt body + head
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-r * 0.7, r * 0.35, r * 0.7, r * 0.95), r * 0.3, r * 0.3),
                         fill(el.get("shirt", "#ff6f61")))
            bh = r * 0.85
        cv.drawOval(skia.Rect(-bw, -bh, bw, bh), radial(-r * 0.3, -r * 0.4, r * 1.5, [shade(col, 0.2), col, shade(col, -0.2)], [0, 0.5, 1]))
        if sp not in ("kid", "astronaut", "robot"):
            cv.drawOval(skia.Rect(-r * 0.55, r * 0.15, r * 0.55, r * 0.92), fill(belly, 0.8))
    if sp == "cat":
        for sgn in (-1, 1):
            p = skia.Path()
            p.moveTo(sgn * r * 0.25, -r * 0.88)
            p.lineTo(sgn * r * 0.75, -r * 1.3)
            p.lineTo(sgn * r * 0.85, -r * 0.55)
            p.close()
            cv.drawPath(p, fill(col))
        for sgn in (-1, 1):
            for k in (-1, 0, 1):
                cv.drawLine(sgn * r * 0.35, r * 0.2 + k * r * 0.06, sgn * r * 0.85, r * 0.12 + k * r * 0.12, stroke(dark, r * 0.02))
    if sp == "owl":
        for sgn in (-1, 1):
            p = skia.Path()
            p.moveTo(sgn * r * 0.3, -r * 0.9)
            p.lineTo(sgn * r * 0.65, -r * 1.25)
            p.lineTo(sgn * r * 0.75, -r * 0.65)
            p.close()
            cv.drawPath(p, fill(dark))
    if sp == "kid":
        hair = el.get("hair", "#2b1d16")
        cv.save()
        clip = skia.Path()
        clip.addOval(skia.Rect(-r, -r * 0.85, r, r * 0.85))
        cv.clipPath(clip, doAntiAlias=True)
        cv.drawOval(skia.Rect(-r * 1.1, -r * 1.25, r * 1.1, -r * 0.2), fill(hair))
        cv.restore()
        if el.get("hairstyle") == "ponytail":
            cv.drawCircle(r * 0.95, -r * 0.5, r * 0.28, fill(hair))
    if sp == "astronaut":
        cv.drawOval(skia.Rect(-r * 0.78, -r * 0.7, r * 0.78, r * 0.6), fill("#1d2b53"))
        cv.save()
        cv.translate(0, -r * 0.05)
        draw_face(cv, {**el, "blush": False}, t, r * 0.62, amp)
        cv.restore()
        cv.drawOval(skia.Rect(-r * 0.6, -r * 0.6, -r * 0.15, -r * 0.3), fill("#ffffff", 0.35))
        return
    face_r = r * (0.85 if sp != "robot" else 0.8)
    draw_face(cv, el, t, face_r, amp)
    if sp == "elephant":
        sway = math.sin(t * 2.2) * 8
        cv.save()
        cv.translate(0, r * 0.05)
        cv.rotate(sway)
        p = skia.Path()
        p.moveTo(-r * 0.12, 0)
        p.cubicTo(-r * 0.15, r * 0.5, r * 0.1, r * 0.75, r * 0.32, r * 0.62)
        p.lineTo(r * 0.3, r * 0.48)
        p.cubicTo(r * 0.12, r * 0.55, r * 0.1, r * 0.3, r * 0.12, 0)
        p.close()
        cv.drawPath(p, fill(shade(col, -0.05)))
        cv.restore()
    if sp in ("bear", "lion", "monkey"):
        cv.drawOval(skia.Rect(-r * 0.12, r * 0.08, r * 0.12, r * 0.22), fill("#2b1b14"))
    if sp == "owl":
        p = skia.Path()
        p.moveTo(-r * 0.09, r * 0.05)
        p.lineTo(r * 0.09, r * 0.05)
        p.lineTo(0, r * 0.22)
        p.close()
        cv.drawPath(p, fill("#ffb703"))


# ---------------------------------------------------------------- props
def draw_prop(cv, el, t, s):
    name = el.get("name", "rocket")
    fn = PROPS.get(name)
    if fn:
        fn(cv, el, t, s)


def prop_rocket(cv, el, t, s):
    body = el.get("color", "#f1f3f8")
    accent = el.get("accent", "#ff4d4d")
    if el.get("flame", True):
        fl = 1 + 0.18 * math.sin(t * 40) + 0.1 * math.sin(t * 23)
        p = skia.Path()
        p.moveTo(-s * 0.22, s * 0.75)
        p.quadTo(0, s * (0.75 + 0.9 * fl), s * 0.22, s * 0.75)
        p.close()
        cv.drawPath(p, glow("#ff7b00", s * 0.08, 0.9))
        p2 = skia.Path()
        p2.moveTo(-s * 0.12, s * 0.75)
        p2.quadTo(0, s * (0.75 + 0.5 * fl), s * 0.12, s * 0.75)
        p2.close()
        cv.drawPath(p2, fill("#ffe36e"))
    for sgn in (-1, 1):
        p = skia.Path()
        p.moveTo(sgn * s * 0.25, s * 0.2)
        p.lineTo(sgn * s * 0.55, s * 0.75)
        p.lineTo(sgn * s * 0.25, s * 0.68)
        p.close()
        cv.drawPath(p, fill(accent))
    p = skia.Path()
    p.moveTo(0, -s)
    p.cubicTo(s * 0.42, -s * 0.6, s * 0.32, s * 0.4, s * 0.25, s * 0.75)
    p.lineTo(-s * 0.25, s * 0.75)
    p.cubicTo(-s * 0.32, s * 0.4, -s * 0.42, -s * 0.6, 0, -s)
    p.close()
    cv.drawPath(p, linear(-s * 0.4, 0, s * 0.4, 0, [shade(body, -0.25), body, shade(body, -0.1)]))
    cv.save()
    clip = skia.Path(p)
    cv.clipPath(clip, doAntiAlias=True)
    cv.drawRect(skia.Rect(-s, -s, s, -s * 0.55), fill(accent))
    cv.restore()
    cv.drawCircle(0, -s * 0.15, s * 0.16, fill("#3a4a6b"))
    cv.drawCircle(0, -s * 0.15, s * 0.12, linear(-s * 0.1, -s * 0.3, s * 0.1, 0, ["#9fe7ff", "#2f7bd6"]))
    if el.get("label"):
        blk = text_block(((str(el["label"]), "#1b1b2f"),), s * 0.6, s * 0.14, style="label")
        blk.paint(cv, 0, s * 0.35)


def prop_satellite(cv, el, t, s):
    for sgn in (-1, 1):
        r = skia.Rect(sgn * s * 0.35 - (s * 0.6 if sgn < 0 else 0), -s * 0.18, sgn * s * 0.35 + (s * 0.6 if sgn > 0 else 0), s * 0.18)
        r.sort()
        cv.drawRect(r, fill("#2952a3"))
        for k in range(1, 4):
            x = r.left() + r.width() * k / 4
            cv.drawLine(x, r.top(), x, r.bottom(), stroke("#8fb3ff", s * 0.015))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-s * 0.32, -s * 0.3, s * 0.32, s * 0.3), s * 0.06, s * 0.06), fill("#e0b84f"))
    cv.drawLine(0, -s * 0.3, 0, -s * 0.55, stroke("#cccccc", s * 0.03))
    cv.drawCircle(0, -s * 0.6, s * 0.08, fill("#dddddd"))
    if el.get("label"):
        blk = text_block(((str(el["label"]), "#1b1b2f"),), s * 0.6, s * 0.14, style="label")
        blk.paint(cv, 0, 0)


def prop_ufo(cv, el, t, s):
    cv.drawOval(skia.Rect(-s * 0.4, -s * 0.55, s * 0.4, s * 0.05), linear(0, -s * 0.5, 0, 0, ["#c9f7ff", "#5bc0de"], alpha=0.9))
    cv.drawOval(skia.Rect(-s, -s * 0.15, s, s * 0.25), linear(0, -s * 0.15, 0, s * 0.25, ["#d7dde8", "#7d8799"]))
    for i in range(6):
        x = -s * 0.75 + i * s * 0.3
        on = (int(t * 6) + i) % 2 == 0
        cv.drawCircle(x, s * 0.05, s * 0.06, fill("#ffe066" if on else "#7a6a2e"))
    if el.get("beam"):
        p = skia.Path()
        p.moveTo(-s * 0.25, s * 0.2)
        p.lineTo(s * 0.25, s * 0.2)
        p.lineTo(s * 0.7, s * 2.2)
        p.lineTo(-s * 0.7, s * 2.2)
        p.close()
        cv.drawPath(p, linear(0, 0, 0, s * 2.2, ["#9dffb0", "#9dffb000"], alpha=0.5))


def prop_cloud(cv, el, t, s):
    _cloud(cv, 0, 0, s, el.get("color", "#ffffff"))


def prop_tree(cv, el, t, s):
    cv.drawRect(skia.Rect(-s * 0.1, 0, s * 0.1, s * 0.9), fill("#7a4b2a"))
    col = el.get("color", "#3fa34d")
    sway = math.sin(t * 1.5) * s * 0.03
    for dx, dy, r in ((-0.35, -0.1, 0.42), (0.35, -0.1, 0.42), (0, -0.5, 0.5), (0, 0.05, 0.4)):
        cv.drawCircle(dx * s + sway, dy * s, r * s, fill(shade(col, dy * 0.3)))


def prop_house(cv, el, t, s):
    wall = el.get("color", "#ffe0b2")
    cv.drawRect(skia.Rect(-s * 0.6, -s * 0.2, s * 0.6, s * 0.7), fill(wall))
    p = skia.Path()
    p.moveTo(-s * 0.75, -s * 0.15)
    p.lineTo(0, -s * 0.8)
    p.lineTo(s * 0.75, -s * 0.15)
    p.close()
    cv.drawPath(p, fill(el.get("roof", "#d84315")))
    cv.drawRect(skia.Rect(-s * 0.15, s * 0.25, s * 0.15, s * 0.7), fill("#8d5524"))
    for sgn in (-1, 1):
        cv.drawRect(skia.Rect(sgn * s * 0.38 - s * 0.12, 0, sgn * s * 0.38 + s * 0.12, s * 0.22), fill("#90caf9"))


def prop_balloon(cv, el, t, s):
    col = el.get("color", "#ff4d6d")
    sw = math.sin(t * 1.8) * s * 0.08
    p = skia.Path()
    p.moveTo(0, s * 0.62)
    p.cubicTo(sw, s * 0.9, -sw, s * 1.2, sw * 0.5, s * 1.5)
    cv.drawPath(p, stroke("#555555", s * 0.02))
    cv.drawOval(skia.Rect(-s * 0.45, -s * 0.6, s * 0.45, s * 0.6), radial(-s * 0.15, -s * 0.25, s * 0.8, [shade(col, 0.4), col, shade(col, -0.2)], [0, 0.5, 1]))
    cv.drawOval(skia.Rect(-s * 0.25, -s * 0.45, -s * 0.08, -s * 0.15), fill("#ffffff", 0.45))


def prop_mountain(cv, el, t, s):
    col = el.get("color", "#6d7b8d")
    p = skia.Path()
    p.moveTo(-s, s * 0.6)
    p.lineTo(0, -s * 0.7)
    p.lineTo(s, s * 0.6)
    p.close()
    cv.drawPath(p, linear(0, -s * 0.7, 0, s * 0.6, [shade(col, 0.15), shade(col, -0.2)]))
    p2 = skia.Path()
    p2.moveTo(-s * 0.3, -s * 0.3)
    p2.lineTo(0, -s * 0.7)
    p2.lineTo(s * 0.3, -s * 0.3)
    p2.lineTo(s * 0.1, -s * 0.38)
    p2.lineTo(-s * 0.05, -s * 0.28)
    p2.close()
    cv.drawPath(p2, fill("#ffffff"))


def prop_lightbulb(cv, el, t, s):
    on = el.get("on", True)
    if on:
        cv.drawCircle(0, -s * 0.15, s * 0.9, radial(0, -s * 0.15, s * 0.9, ["#fff59d", "#fff59d00"], alpha=0.6 + 0.2 * math.sin(t * 5)))
    cv.drawCircle(0, -s * 0.15, s * 0.45, fill("#ffe066" if on else "#e0e0e0"))
    cv.drawRect(skia.Rect(-s * 0.18, s * 0.25, s * 0.18, s * 0.55), fill("#9e9e9e"))
    for k in range(3):
        y = s * (0.3 + 0.09 * k)
        cv.drawLine(-s * 0.18, y, s * 0.18, y, stroke("#616161", s * 0.025))


def prop_book(cv, el, t, s):
    col = el.get("color", "#5c6bc0")
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-s * 0.7, -s * 0.5, s * 0.7, s * 0.5), s * 0.05, s * 0.05), fill(col))
    cv.drawRect(skia.Rect(-s * 0.62, -s * 0.42, -s * 0.02, s * 0.42), fill("#fffaf0"))
    cv.drawRect(skia.Rect(s * 0.02, -s * 0.42, s * 0.62, s * 0.42), fill("#fffaf0"))
    for k in range(5):
        y = -s * 0.28 + k * s * 0.13
        cv.drawLine(-s * 0.52, y, -s * 0.12, y, stroke("#b0bec5", s * 0.02))
        cv.drawLine(s * 0.12, y, s * 0.52, y, stroke("#b0bec5", s * 0.02))


def prop_trophy(cv, el, t, s):
    gold = "#ffc107"
    p = skia.Path()
    p.moveTo(-s * 0.5, -s * 0.6)
    p.lineTo(s * 0.5, -s * 0.6)
    p.cubicTo(s * 0.5, 0, s * 0.2, s * 0.15, 0, s * 0.15)
    p.cubicTo(-s * 0.2, s * 0.15, -s * 0.5, 0, -s * 0.5, -s * 0.6)
    p.close()
    cv.drawPath(p, linear(-s * 0.5, 0, s * 0.5, 0, [shade(gold, -0.2), shade(gold, 0.3), gold]))
    for sgn in (-1, 1):
        cv.drawArc(skia.Rect(sgn * s * 0.5 - s * 0.22, -s * 0.55, sgn * s * 0.5 + s * 0.22, -s * 0.1), -90 if sgn > 0 else 90, 180, False, stroke(gold, s * 0.07))
    cv.drawRect(skia.Rect(-s * 0.08, s * 0.15, s * 0.08, s * 0.45), fill(gold))
    cv.drawRect(skia.Rect(-s * 0.35, s * 0.45, s * 0.35, s * 0.6), fill("#6d4c41"))


def prop_telescope(cv, el, t, s):
    cv.save()
    cv.rotate(-30)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-s * 0.7, -s * 0.12, s * 0.6, s * 0.12), s * 0.04, s * 0.04), fill("#37474f"))
    cv.drawRect(skia.Rect(s * 0.5, -s * 0.16, s * 0.7, s * 0.16), fill("#546e7a"))
    cv.restore()
    for a in (-60, 0, 60):
        cv.save()
        cv.rotate(a)
        cv.drawLine(0, 0, 0, s * 0.8, stroke("#8d6e63", s * 0.05))
        cv.restore()


def prop_diya(cv, el, t, s):
    flick = 1 + 0.12 * math.sin(t * 17) + 0.06 * math.sin(t * 29)
    cv.drawCircle(0, -s * 0.45, s * 0.7 * flick, radial(0, -s * 0.45, s * 0.7 * flick, ["#ffcc66", "#ff990000"], alpha=0.6))
    p = skia.Path()
    p.moveTo(-s * 0.6, 0)
    p.quadTo(0, s * 0.6, s * 0.6, 0)
    p.quadTo(0, s * 0.15, -s * 0.6, 0)
    p.close()
    cv.drawPath(p, linear(0, 0, 0, s * 0.4, ["#e8833a", "#a8461b"]))
    f = skia.Path()
    f.moveTo(0, -s * 0.75 * flick)
    f.quadTo(s * 0.16, -s * 0.25, 0, -s * 0.05)
    f.quadTo(-s * 0.16, -s * 0.25, 0, -s * 0.75 * flick)
    f.close()
    cv.drawPath(f, linear(0, -s * 0.75, 0, 0, ["#fff7b0", "#ff9d00"]))


def prop_comet(cv, el, t, s):
    """Comet pointing right (rotate the element to aim it). Tail trails to the left."""
    tail_len = s * float(el.get("tail", 3.2))
    for k, (w, col, a) in enumerate(((0.55, "#7fd6ff", 0.35), (0.32, "#d8f3ff", 0.55), (0.14, "#ffffff", 0.8))):
        p = skia.Path()
        p.moveTo(0, -s * w)
        p.cubicTo(-tail_len * 0.4, -s * w * 0.9, -tail_len * 0.8, -s * w * 0.4, -tail_len, math.sin(t * 2 + k) * s * 0.05)
        p.cubicTo(-tail_len * 0.8, s * w * 0.4, -tail_len * 0.4, s * w * 0.9, 0, s * w)
        p.close()
        paint = linear(0, 0, -tail_len, 0, [col, col + "00"], alpha=a)
        paint.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, s * 0.06))
        cv.drawPath(p, paint)
    cv.drawCircle(0, 0, s * 0.55, glow("#bff0ff", s * 0.2, 0.7))
    cv.drawCircle(0, 0, s * 0.2, fill("#ffffff"))
    rnd = random.Random(7)
    for i in range(18):
        u = ((rnd.random() + t * 0.25 * (0.5 + rnd.random())) % 1.0)
        x = -u * tail_len * 0.9
        y = (rnd.random() - 0.5) * s * (0.3 + u * 0.9)
        cv.drawCircle(x, y, s * 0.03 * (1 - u) + 0.5, fill("#ffffff", 0.8 * (1 - u)))


def prop_voyager(cv, el, t, s):
    """Deep-space probe: big high-gain dish facing the viewer, booms and an RTG."""
    grey = "#b8c0cc"
    cv.drawLine(s * 0.2, s * 0.15, s * 2.3, -s * 0.35, stroke("#cfd6df", s * 0.025))  # magnetometer boom
    cv.drawLine(-s * 0.15, s * 0.25, -s * 1.1, s * 0.85, stroke(grey, s * 0.05))       # RTG boom
    for k in range(3):
        cx, cy = -s * (0.75 + k * 0.14), s * (0.6 + k * 0.08)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - s * 0.07, cy - s * 0.1, cx + s * 0.07, cy + s * 0.1), s * 0.03, s * 0.03), fill("#8a8f99"))
    cv.drawRect(skia.Rect(-s * 0.32, s * 0.05, s * 0.32, s * 0.38), fill("#9aa3ad"))
    cv.drawRect(skia.Rect(-s * 0.32, s * 0.05, s * 0.32, s * 0.12), fill("#d8b04a"))
    cv.drawOval(skia.Rect(-s * 0.85, -s * 0.95, s * 0.85, s * 0.35), radial(-s * 0.2, -s * 0.5, s * 1.1, ["#ffffff", "#e3e8ee", "#aeb7c2"], [0, 0.6, 1]))
    cv.drawOval(skia.Rect(-s * 0.85, -s * 0.95, s * 0.85, s * 0.35), stroke("#8a95a3", s * 0.03))
    cv.drawOval(skia.Rect(-s * 0.45, -s * 0.6, s * 0.45, s * 0.0), stroke("#c3cad3", s * 0.02))
    for a in (-0.5, 0.5):
        cv.drawLine(a * s * 0.8, -s * 0.3, 0, -s * 0.62, stroke("#8a95a3", s * 0.02))
    cv.drawCircle(0, -s * 0.62, s * 0.07, fill("#6d7682"))
    blink = 0.5 + 0.5 * math.sin(t * 3)
    cv.drawCircle(s * 0.25, s * 0.22, s * 0.05, glow("#7dff9a", s * 0.04, blink))


def prop_record(cv, el, t, s):
    """The Golden Record: gold disc with grooves, slowly spinning shine."""
    cv.drawCircle(0, 0, s, radial(-s * 0.3, -s * 0.3, s * 1.4, ["#fff2b3", "#e2b33c", "#9c6f12"], [0, 0.5, 1]))
    for k in range(9):
        cv.drawCircle(0, 0, s * (0.4 + k * 0.065), stroke("#7a5508", s * 0.008, 0.45))
    cv.save()
    cv.rotate(t * 25)
    sh = skia.Path()
    sh.moveTo(0, 0)
    sh.arcTo(skia.Rect(-s, -s, s, s), -100, 30, False)
    sh.close()
    cv.drawPath(sh, fill("#ffffff", 0.18))
    cv.restore()
    cv.drawCircle(0, 0, s * 0.3, fill("#c99a2e"))
    cv.drawCircle(0, 0, s * 0.04, fill("#2a1c03"))


PROPS = {
    "voyager": prop_voyager,
    "record": prop_record,
    "comet": prop_comet,
    "rocket": prop_rocket, "satellite": prop_satellite, "ufo": prop_ufo, "cloud": prop_cloud,
    "tree": prop_tree, "house": prop_house, "balloon": prop_balloon, "mountain": prop_mountain,
    "lightbulb": prop_lightbulb, "book": prop_book, "trophy": prop_trophy, "telescope": prop_telescope,
    "diya": prop_diya,
}


# ---------------------------------------------------------------- particles
def draw_particles(cv, el, t, W, H):
    kind = el.get("kind", "sparkles")
    n = int(el.get("count", 30))
    rnd = random.Random(el.get("seed", hash(el.get("id", kind)) % 1000))
    cols = el.get("colors") or ["#ff4d6d", "#ffd166", "#06d6a0", "#118ab2", "#ef476f", "#9b5de5"]
    for i in range(n):
        x0, y0 = rnd.random() * W, rnd.random() * H
        sp = 0.5 + rnd.random()
        ph = rnd.random() * TAU
        sz = (0.5 + rnd.random()) * W * 0.012
        if kind == "confetti":
            y = (y0 + t * H * 0.18 * sp) % (H * 1.1) - H * 0.05
            x = x0 + math.sin(t * 2 * sp + ph) * W * 0.03
            cv.save()
            cv.translate(x, y)
            cv.rotate(t * 200 * sp + ph * 57)
            cv.scale(1, abs(math.sin(t * 5 * sp + ph)) + 0.15)
            cv.drawRect(skia.Rect(-sz, -sz * 0.5, sz, sz * 0.5), fill(cols[i % len(cols)]))
            cv.restore()
        elif kind == "sparkles":
            a = max(0, math.sin(t * 2.5 * sp + ph))
            cv.drawPath(star_path(x0, y0, sz * 1.6 * a + 0.1, sz * 0.35 * a + 0.05, 4, 0), fill(el.get("color", "#fff6c2"), a))
        elif kind == "snow":
            y = (y0 + t * H * 0.06 * sp) % H
            x = x0 + math.sin(t * sp + ph) * W * 0.02
            cv.drawCircle(x, y, sz * 0.45, fill("#ffffff", 0.85))
        elif kind == "bubbles":
            y = H - ((H - y0) + t * H * 0.07 * sp) % H
            x = x0 + math.sin(t * 1.5 * sp + ph) * W * 0.02
            cv.drawCircle(x, y, sz * 0.9, stroke("#e0f7ff", 2, 0.7))
            cv.drawCircle(x - sz * 0.3, y - sz * 0.3, sz * 0.2, fill("#ffffff", 0.7))
        elif kind == "fireflies":
            x = x0 + math.sin(t * 0.5 * sp + ph) * W * 0.05
            y = y0 + math.cos(t * 0.4 * sp + ph) * H * 0.03
            a = 0.4 + 0.6 * max(0, math.sin(t * 2 * sp + ph))
            cv.drawCircle(x, y, sz * 1.4, glow("#fff176", sz * 0.8, a * 0.6))
            cv.drawCircle(x, y, sz * 0.35, fill("#fffde7", a))
        elif kind == "rain":
            y = (y0 + t * H * 1.2 * sp) % H
            cv.drawLine(x0, y, x0 - W * 0.006, y + H * 0.03, stroke("#cfe8ff", 2, 0.5))
        elif kind == "hearts":
            y = H - ((H - y0) + t * H * 0.08 * sp) % H
            cv.drawPath(heart_path(x0 + math.sin(t + ph) * W * 0.02, y, sz), fill(cols[i % len(cols)], 0.85))
        elif kind == "stars":
            a = 0.5 + 0.5 * math.sin(t * 2 * sp + ph)
            cv.drawPath(star_path(x0, y0, sz * 1.2, sz * 0.5), fill(el.get("color", "#ffe066"), a))
        elif kind == "meteors":
            # streaks radiating away from a radiant point, each living ~0.7s, staggered
            rx, ry = el.get("radiant", [0.75, 0.2])
            rx, ry = rx * W, ry * H
            life = 0.75
            period = float(el.get("period", 2.4)) * (0.6 + rnd.random() * 0.8)
            start = rnd.random() * period
            u = ((t - start) % period) / life
            cycle = int((t - start) // period)
            if u > 1 or t < start:
                continue
            r2 = random.Random(i * 1000 + cycle)
            ang = r2.uniform(0, TAU)
            d0 = r2.uniform(0.05, 0.35) * W
            length = r2.uniform(0.18, 0.4) * W
            hx = rx + math.cos(ang) * (d0 + length * u)
            hy = ry + math.sin(ang) * (d0 + length * u)
            tx = rx + math.cos(ang) * (d0 + length * max(0, u - 0.45))
            ty = ry + math.sin(ang) * (d0 + length * max(0, u - 0.45))
            a = math.sin(math.pi * u)
            lp = linear(tx, ty, hx, hy, ["#ffffff00", el.get("color", "#fff4d6")], alpha=a)
            lp.setStyle(skia.Paint.kStroke_Style)
            lp.setStrokeWidth(W * 0.005)
            lp.setStrokeCap(skia.Paint.kRound_Cap)
            cv.drawLine(tx, ty, hx, hy, lp)
            cv.drawCircle(hx, hy, W * 0.007, glow("#ffffff", W * 0.004, a))
        elif kind == "stream":
            # particles flowing along a band (y center, angle, thickness) - dust trails, rivers, wind
            yc = float(el.get("y", 0.5)) * H
            ang = math.radians(float(el.get("angle", -15)))
            thick = float(el.get("thickness", 0.12)) * H
            speed = float(el.get("speed", 0.08)) * W
            span = math.hypot(W, H) * 1.2
            along = ((rnd.random() * span + t * speed * sp) % span) - span / 2
            across = (rnd.random() - 0.5) * thick
            x = W / 2 + along * math.cos(ang) - across * math.sin(ang)
            y = yc + along * math.sin(ang) + across * math.cos(ang)
            a = 0.35 + 0.65 * (1 - abs(across) / (thick / 2 + 1e-3))
            if el.get("streak"):
                ln = float(el["streak"]) * W * (0.6 + 0.4 * sp)
                d = 1 if speed >= 0 else -1
                cv.drawLine(x, y, x - d * ln * math.cos(ang), y - d * ln * math.sin(ang),
                            stroke(el.get("color", "#cfefff"), W * 0.003, a * 0.8))
            else:
                cv.drawCircle(x, y, sz * 0.35, fill(el.get("color", "#ffd9a0"), a * 0.8))
        elif kind == "leaves":
            y = (y0 + t * H * 0.08 * sp) % H
            x = x0 + math.sin(t * 1.2 * sp + ph) * W * 0.06
            cv.save()
            cv.translate(x, y)
            cv.rotate(math.sin(t * 2 + ph) * 60)
            cv.drawOval(skia.Rect(-sz, -sz * 0.45, sz, sz * 0.45), fill(rnd.choice(["#e07a1f", "#c94c1c", "#f2b134"])))
            cv.restore()


# ---------------------------------------------------------------- shapes
_SVG_TOKEN = re.compile(r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
_ARGC = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def svg_path(d: str) -> "skia.Path":
    """Parse an SVG path 'd' string into a skia.Path (skia-python 138+ has no ParsePath). Bad input gives an empty path."""
    path = skia.Path()
    toks = _SVG_TOKEN.findall(d or "")
    i, cmd = 0, None
    cx = cy = sx = sy = 0.0
    lcx = lcy = None          # last control point for S/T reflection
    last = ""
    try:
        while i < len(toks):
            t = toks[i]
            if t.isalpha():
                cmd = t
                i += 1
                if cmd in "Zz":
                    path.close()
                    cx, cy = sx, sy
                    last = "Z"
                    continue
            if cmd is None:
                break
            up = cmd.upper()
            n = _ARGC[up]
            args = [float(x) for x in toks[i:i + n]]
            if len(args) < n:
                break
            i += n
            rel = cmd.islower()
            ox, oy = (cx, cy) if rel else (0.0, 0.0)
            if up == "M":
                cx, cy = ox + args[0], oy + args[1]
                path.moveTo(cx, cy)
                sx, sy = cx, cy
                cmd = "l" if rel else "L"          # implicit lineto after moveto
            elif up == "L":
                cx, cy = ox + args[0], oy + args[1]
                path.lineTo(cx, cy)
            elif up == "H":
                cx = ox + args[0]
                path.lineTo(cx, cy)
            elif up == "V":
                cy = oy + args[0]
                path.lineTo(cx, cy)
            elif up == "C":
                x1, y1, x2, y2, x, y = (ox + args[0], oy + args[1], ox + args[2], oy + args[3], ox + args[4], oy + args[5])
                path.cubicTo(x1, y1, x2, y2, x, y)
                lcx, lcy, cx, cy = x2, y2, x, y
            elif up == "S":
                x1, y1 = (2 * cx - lcx, 2 * cy - lcy) if last in ("C", "S") and lcx is not None else (cx, cy)
                x2, y2, x, y = ox + args[0], oy + args[1], ox + args[2], oy + args[3]
                path.cubicTo(x1, y1, x2, y2, x, y)
                lcx, lcy, cx, cy = x2, y2, x, y
            elif up == "Q":
                x1, y1, x, y = ox + args[0], oy + args[1], ox + args[2], oy + args[3]
                path.quadTo(x1, y1, x, y)
                lcx, lcy, cx, cy = x1, y1, x, y
            elif up == "T":
                x1, y1 = (2 * cx - lcx, 2 * cy - lcy) if last in ("Q", "T") and lcx is not None else (cx, cy)
                x, y = ox + args[0], oy + args[1]
                path.quadTo(x1, y1, x, y)
                lcx, lcy, cx, cy = x1, y1, x, y
            elif up == "A":
                rx, ry, rot, large, sweep, x, y = args
                x, y = ox + x, oy + y
                path.arcTo(rx, ry, rot, skia.Path.ArcSize.kLarge_ArcSize if large else skia.Path.ArcSize.kSmall_ArcSize,
                           skia.PathDirection.kCW if sweep else skia.PathDirection.kCCW, x, y)
                cx, cy = x, y
            last = up
            if up not in ("C", "S", "Q", "T"):
                lcx = lcy = None
    except Exception:
        return skia.Path()
    return path


def draw_shape(cv, el, t, W, reveal=1.0):
    shp = el.get("shape", "circle")
    col = el.get("color", "#ffffff")
    w = float(el.get("w", el.get("r", 0.1) * 2)) * W
    h = float(el.get("h", el.get("w", el.get("r", 0.1) * 2))) * W
    p = fill(col)
    if el.get("gradient"):
        g = el["gradient"]
        p = linear(0, -h / 2, 0, h / 2, g)
    sp = stroke(el.get("stroke"), float(el.get("stroke_w", 0.006)) * W) if el.get("stroke") else None
    if shp == "circle":
        cv.drawOval(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), p)
        if sp:
            cv.drawOval(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), sp)
    elif shp == "rect":
        rr = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), float(el.get("radius", 0.02)) * W, float(el.get("radius", 0.02)) * W)
        cv.drawRRect(rr, p)
        if sp:
            cv.drawRRect(rr, sp)
    elif shp == "ring":
        cv.drawOval(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), stroke(col, float(el.get("stroke_w", 0.012)) * W))
    elif shp == "star":
        path = star_path(0, 0, w / 2, w / 4.6, int(el.get("points", 5)))
        cv.drawPath(path, p)
        if sp:
            cv.drawPath(path, sp)
    elif shp == "heart":
        cv.drawPath(heart_path(0, 0, w / 2.6), p)
    elif shp == "triangle":
        path = skia.Path()
        path.moveTo(0, -h / 2)
        path.lineTo(w / 2, h / 2)
        path.lineTo(-w / 2, h / 2)
        path.close()
        cv.drawPath(path, p)
    elif shp in ("line", "arrow"):
        # coordinates relative to element origin, in W units
        x1, y1 = el.get("from", [-0.15, 0])
        x2, y2 = el.get("to", [0.15, 0])
        x1, y1, x2, y2 = x1 * W, y1 * W, x2 * W, y2 * W
        xe, ye = x1 + (x2 - x1) * reveal, y1 + (y2 - y1) * reveal
        lw = float(el.get("stroke_w", 0.01)) * W
        lp = stroke(col, lw)
        if el.get("dashed"):
            lp.setPathEffect(skia.DashPathEffect.Make([lw * 2.5, lw * 2], 0))
        cv.drawLine(x1, y1, xe, ye, lp)
        if shp == "arrow" and reveal > 0.95:
            a = math.atan2(y2 - y1, x2 - x1)
            hl = lw * 3.2
            ah = skia.Path()
            ah.moveTo(x2, y2)
            ah.lineTo(x2 - hl * math.cos(a - 0.5), y2 - hl * math.sin(a - 0.5))
            ah.lineTo(x2 - hl * math.cos(a + 0.5), y2 - hl * math.sin(a + 0.5))
            ah.close()
            cv.drawPath(ah, fill(col))
    elif shp == "path" and el.get("d"):
        path = svg_path(el["d"])
        sc = w / float(el.get("view", 100))
        cv.save()
        cv.scale(sc, sc)
        cv.translate(-float(el.get("view", 100)) / 2, -float(el.get("view", 100)) / 2)
        cv.drawPath(path, p)
        cv.restore()


def draw_constellation(cv, el, t, W, reveal=1.0):
    """points: [[x,y],...] in element-local units (fraction of W, centered); lines: [[i,j],...]."""
    pts = [(p[0] * W, p[1] * W) for p in el.get("points", [])]
    col = el.get("color", "#cfe3ff")
    lw = float(el.get("line_w", 0.004)) * W
    lines = el.get("lines", [])
    n_show = int(math.ceil(len(lines) * reveal)) if lines else 0
    for k, (i, j) in enumerate(lines[:n_show]):
        if i < len(pts) and j < len(pts):
            cv.drawLine(*pts[i], *pts[j], stroke(col, lw, 0.6))
    rnd = random.Random(3)
    for k, (x, y) in enumerate(pts):
        r = float(el.get("star_r", 0.011)) * W * (0.8 + 0.5 * rnd.random())
        a = 0.75 + 0.25 * math.sin(t * 2.2 + k)
        cv.drawCircle(x, y, r * 3, glow(col, r * 1.4, 0.5 * a))
        cv.drawCircle(x, y, r, fill("#ffffff", a))
    if el.get("label"):
        lx, ly = el.get("label_pos", [0, 0.2])
        blk = text_block(((str(el["label"]), col),), W * 0.6, W * 0.04, style="label", stroke=W * 0.006,
                         stroke_color="#000000", shadow=False)
        blk.paint(cv, lx * W, ly * W)


# ---------------------------------------------------------------- numbers
def indian_format(n: float, decimals: int = 0) -> str:
    neg = n < 0
    n = abs(n)
    s = f"{n:.{decimals}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts + [tail])
    out = whole + ("." + frac if frac else "")
    return ("-" if neg else "") + out


def counter_text(el, t):
    a, b = float(el.get("from", 0)), float(el.get("to", 100))
    s = float(el.get("at", 0))
    d = float(el.get("count_dur", 1.5))
    u = max(0.0, min(1.0, (t - s) / max(0.01, d)))
    u = 1 - (1 - u) ** 3
    v = a + (b - a) * u
    dec = int(el.get("decimals", 0))
    num = indian_format(v, dec) if el.get("grouping", "indian") == "indian" else f"{v:,.{dec}f}"
    return f"{el.get('prefix', '')}{num}{el.get('suffix', '')}"
