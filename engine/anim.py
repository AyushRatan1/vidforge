"""Easing, entrances/exits, keyframes and procedural behaviors for scene elements."""
from __future__ import annotations

import math
from dataclasses import dataclass


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, u):
    return a + (b - a) * u


def _back_out(u, s=1.70158):
    u -= 1
    return u * u * ((s + 1) * u + s) + 1


def _elastic_out(u):
    if u in (0, 1):
        return u
    return 2 ** (-10 * u) * math.sin((u * 10 - 0.75) * (2 * math.pi) / 3) + 1


def _bounce_out(u):
    n1, d1 = 7.5625, 2.75
    if u < 1 / d1:
        return n1 * u * u
    if u < 2 / d1:
        u -= 1.5 / d1
        return n1 * u * u + 0.75
    if u < 2.5 / d1:
        u -= 2.25 / d1
        return n1 * u * u + 0.9375
    u -= 2.625 / d1
    return n1 * u * u + 0.984375


EASES = {
    "linear": lambda u: u,
    "in": lambda u: u ** 3,
    "out": lambda u: 1 - (1 - u) ** 3,
    "in_out": lambda u: 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2,
    "back": _back_out,
    "elastic": _elastic_out,
    "bounce": _bounce_out,
}


def ease(name: str, u: float) -> float:
    return EASES.get(name or "in_out", EASES["in_out"])(clamp(u))


@dataclass
class Xf:
    x: float
    y: float
    sx: float = 1.0
    sy: float = 1.0
    rot: float = 0.0
    alpha: float = 1.0
    visible: bool = True
    reveal: float = 1.0  # 0..1 progress for typewriter / draw-on effects


ENTER_DUR = 0.5
EXIT_DUR = 0.35


def _apply_keys(el, t, W, H, xf: Xf):
    keys = el.get("keys")
    if not keys:
        mv = el.get("move")
        if not mv:
            return
        to = mv.get("to", [el.get("x", 0.5), el.get("y", 0.5)])
        s, e = float(mv.get("start", 0)), float(mv.get("end", 1))
        u = ease(mv.get("ease", "in_out"), (t - s) / max(1e-3, e - s))
        xf.x = lerp(xf.x, to[0] * W, u)
        xf.y = lerp(xf.y, to[1] * H, u)
        return
    keys = sorted(keys, key=lambda k: k.get("t", 0))
    prev = keys[0]
    nxt = keys[-1]
    for k in keys:
        if k.get("t", 0) <= t:
            prev = k
        if k.get("t", 0) > t:
            nxt = k
            break
    if t <= keys[0].get("t", 0):
        prev = nxt = keys[0]
    span = max(1e-3, nxt.get("t", 0) - prev.get("t", 0))
    u = ease(nxt.get("ease", "in_out"), (t - prev.get("t", 0)) / span) if nxt is not prev else 1.0

    def g(k, name, default):
        return k.get(name, default)

    if "x" in prev or "x" in nxt:
        xf.x = lerp(g(prev, "x", el.get("x", 0.5)), g(nxt, "x", g(prev, "x", el.get("x", 0.5))), u) * W
    if "y" in prev or "y" in nxt:
        xf.y = lerp(g(prev, "y", el.get("y", 0.5)), g(nxt, "y", g(prev, "y", el.get("y", 0.5))), u) * H
    if "scale" in prev or "scale" in nxt:
        s = lerp(g(prev, "scale", 1), g(nxt, "scale", g(prev, "scale", 1)), u)
        xf.sx *= s
        xf.sy *= s
    if "rot" in prev or "rot" in nxt:
        xf.rot += lerp(g(prev, "rot", 0), g(nxt, "rot", g(prev, "rot", 0)), u)
    if "alpha" in prev or "alpha" in nxt:
        xf.alpha *= lerp(g(prev, "alpha", 1), g(nxt, "alpha", g(prev, "alpha", 1)), u)


def _apply_behaviors(el, t, W, H, xf: Xf):
    for b in el.get("behaviors", []) or []:
        k = b.get("kind")
        amp = float(b.get("amp", 0))
        period = float(b.get("period", 3.0)) or 3.0
        phase = float(b.get("phase", 0))
        w = 2 * math.pi * (t / period + phase)
        if k in ("float", "bob"):
            xf.y += (amp or 0.012) * H * math.sin(w)
        elif k == "spin":
            xf.rot += float(b.get("speed", 20)) * t
        elif k == "pulse":
            s = 1 + (amp or 0.05) * math.sin(w)
            xf.sx *= s
            xf.sy *= s
        elif k == "sway":
            xf.rot += (amp or 6) * math.sin(w)
        elif k == "bounce":
            xf.y -= (amp or 0.03) * H * abs(math.sin(w / 2))
        elif k == "squash":
            s = (amp or 0.06) * math.sin(w)
            xf.sx *= 1 + s
            xf.sy *= 1 - s
        elif k == "wiggle":
            xf.rot += (amp or 4) * math.sin(w * 4)
        elif k == "orbit":
            cx, cy = b.get("center", [0.5, 0.5])
            rx = float(b.get("rx", 0.3))
            ry = float(b.get("ry", rx * 0.4))
            xf.x = cx * W + rx * W * math.cos(w)
            xf.y = cy * H + ry * W * math.sin(w)
            if b.get("depth", True):
                d = 0.75 + 0.25 * math.sin(w)
                xf.sx *= d
                xf.sy *= d
        elif k == "twinkle":
            xf.alpha *= 0.55 + 0.45 * (0.5 + 0.5 * math.sin(w))
        elif k == "drift":
            v = b.get("v", [0.02, 0])
            xf.x += v[0] * W * t
            xf.y += v[1] * H * t
        elif k == "shake":
            xf.x += (amp or 0.006) * W * math.sin(t * 61)
            xf.y += (amp or 0.006) * W * math.cos(t * 47)


def _apply_enter_exit(el, t, W, H, xf: Xf, scene_dur: float):
    at = float(el.get("at", 0))
    enter = el.get("enter", "fade")
    dur = float(el.get("enter_dur", ENTER_DUR))
    if t < at:
        xf.visible = False
        return
    u = (t - at) / max(1e-3, dur)
    if u < 1 and enter not in (None, "none"):
        if enter == "pop":
            s = ease("back", u)
            xf.sx *= s
            xf.sy *= s
            xf.alpha *= clamp(u * 3)
        elif enter == "grow":
            s = ease("out", u)
            xf.sx *= s
            xf.sy *= s
        elif enter == "fade":
            xf.alpha *= ease("out", u)
        elif enter == "drop":
            xf.y -= (1 - ease("bounce", u)) * H * 0.35
            xf.alpha *= clamp(u * 4)
        elif enter.startswith("slide_"):
            d = enter[6:]
            off = (1 - ease("out", u))
            if d == "up":
                xf.y += off * H * 0.12
            elif d == "down":
                xf.y -= off * H * 0.12
            elif d == "left":
                xf.x += off * W * 0.7
            elif d == "right":
                xf.x -= off * W * 0.7
            xf.alpha *= clamp(u * 2.5)
        elif enter == "typewriter":
            xf.reveal = clamp((t - at) / max(0.3, float(el.get("type_dur", 1.2))))
        elif enter == "spin_in":
            s = ease("back", u)
            xf.sx *= s
            xf.sy *= s
            xf.rot += (1 - ease("out", u)) * -180
    elif enter == "typewriter":
        xf.reveal = clamp((t - at) / max(0.3, float(el.get("type_dur", 1.2))))

    until = el.get("until")
    if until is not None:
        until = float(until)
        ex = el.get("exit", "fade")
        if t >= until + EXIT_DUR:
            xf.visible = False
            return
        if t >= until:
            v = (t - until) / EXIT_DUR
            if ex == "pop":
                s = 1 - ease("in", v)
                xf.sx *= s
                xf.sy *= s
            elif ex == "fly_up":
                xf.y -= ease("in", v) * H * 0.4
            xf.alpha *= 1 - v


def transform(el: dict, t: float, W: int, H: int, scene_dur: float) -> Xf:
    xf = Xf(x=float(el.get("x", 0.5)) * W, y=float(el.get("y", 0.5)) * H)
    base = float(el.get("scale", 1.0))
    xf.sx = xf.sy = base
    xf.rot = float(el.get("rot", 0))
    xf.alpha = float(el.get("opacity", 1.0))
    if el.get("flip"):
        xf.sx = -xf.sx
    _apply_keys(el, t, W, H, xf)
    _apply_behaviors(el, t, W, H, xf)
    _apply_enter_exit(el, t, W, H, xf, scene_dur)
    xf.alpha = clamp(xf.alpha)
    return xf
