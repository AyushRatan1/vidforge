"""Scene compositor: draws every frame of an episode with Skia and encodes per-scene MP4s."""
from __future__ import annotations

import math
import os
import re
import subprocess

import numpy as np
import skia

from . import draw as D
from .anim import clamp, ease, transform
from .fonts import DEVANAGARI, text_block


class Renderer:
    def __init__(self, spec: dict, timeline: list, amp: np.ndarray):
        self.spec = spec
        self.W, self.H = spec["_W"], spec["_H"]
        self.fps = spec["fps"]
        self.tl = timeline
        self.amp = amp
        self.total_frames = sum(s["frames"] for s in timeline)
        cap = dict(DEFAULT_CAPTIONS)
        cap.update(spec.get("captions") or {})
        self.cap = cap
        self._chunks = [self._caption_chunks(i) for i in range(len(timeline))]

    # ---------------------------------------------------------- captions
    def _caption_chunks(self, i):
        sc = self.spec["scenes"][i]
        seg = self.tl[i]
        text = sc.get("caption")
        if text is None:
            text = sc.get("narration", "")
        text = (text or "").strip()
        if not text or not self.cap.get("enabled", True):
            return []
        words = text.split()
        maxw = int(self.cap.get("max_words", 3))
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= maxw or re.search(r"[.,!?।:;]$", w):
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        s0, dur = seg["voice_start"], max(0.4, seg["voice_dur"])
        weights = [len(w) + 2 for w in words]
        total = sum(weights)
        out, k, acc = [], 0, 0.0
        for ch in chunks:
            ws = []
            for w in ch:
                a = s0 + dur * acc / total
                acc += weights[k]
                b = s0 + dur * acc / total
                ws.append((w, a, b))
                k += 1
            out.append(ws)
        return out

    def _draw_captions(self, cv, i, t):
        chunks = self._chunks[i]
        if not chunks:
            return
        cur = None
        for ch in chunks:
            if ch[0][1] - 0.05 <= t <= ch[-1][2] + 0.25:
                cur = ch
        if cur is None:
            return
        cap = self.cap
        hi = cap.get("highlight", "#ffd400")
        base = cap.get("color", "#ffffff")
        upper = cap.get("uppercase", False)
        runs = []
        for j, (w, a, b) in enumerate(cur):
            txt = w.upper() if upper and not DEVANAGARI.search(w) else w
            active = a <= t < b or (j == len(cur) - 1 and t >= b)
            runs.append((txt + (" " if j < len(cur) - 1 else ""), hi if active and cap.get("style") == "karaoke" else base))
        size = float(cap.get("size", 0.078)) * self.W
        blk = text_block(tuple(runs), self.W * 0.9, size, style="caption", stroke=size * 0.2,
                         stroke_color=cap.get("stroke", "#000000"), line_height=1.15)
        pop = clamp((t - cur[0][1] + 0.05) / 0.14)
        s = 0.82 + 0.18 * ease("back", pop)
        cx, cy = self.W / 2, float(cap.get("y", 0.74)) * self.H
        cv.save()
        cv.translate(cx, cy)
        cv.scale(s, s)
        if cap.get("box"):
            pad = size * 0.35
            w2 = blk.text_width / 2 + pad
            h2 = blk.height / 2 + pad * 0.6
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-w2, -h2, w2, h2), size * 0.35, size * 0.35),
                         D.fill(cap["box"], float(cap.get("box_alpha", 0.55))))
        blk.paint(cv, 0, 0)
        cv.restore()

    # ---------------------------------------------------------- elements
    def _element(self, cv, el, t, dur, amp):
        W, H = self.W, self.H
        typ = el.get("type", "shape")
        if typ == "particles":
            a = 1.0
            if t < float(el.get("at", 0)):
                return
            if el.get("until") is not None and t > float(el["until"]):
                return
            cv.saveLayerAlpha(None, int(255 * clamp(float(el.get("opacity", 1)))))
            D.draw_particles(cv, el, t, W, H)
            cv.restore()
            return
        xf = transform(el, t, W, H, dur)
        if not xf.visible or xf.alpha <= 0.01 or abs(xf.sx) < 1e-3 or abs(xf.sy) < 1e-3:
            return
        cv.save()
        cv.translate(xf.x, xf.y)
        if xf.rot:
            cv.rotate(xf.rot)
        cv.scale(xf.sx, xf.sy)
        layered = xf.alpha < 0.999
        if layered:
            cv.saveLayerAlpha(None, int(255 * xf.alpha))
        try:
            if typ in ("text", "counter", "emoji"):
                self._text(cv, el, t, xf)
            elif typ == "planet":
                el2 = el if not el.get("talking") else {**el, "_amp": amp}
                D.draw_planet(cv, el2, t, float(el.get("r", 0.2)) * W)
            elif typ == "character":
                D.draw_character(cv, el, t, float(el.get("r", 0.15)) * W, amp if el.get("talking") else 0.0)
            elif typ == "prop":
                D.draw_prop(cv, el, t, float(el.get("size", 0.15)) * W)
            elif typ == "shape":
                D.draw_shape(cv, el, t, W, reveal=self._draw_on(el, t))
            elif typ == "image":
                self._image(cv, el, t)
            elif typ == "constellation":
                D.draw_constellation(cv, el, t, W, reveal=self._draw_on(el, t))
            elif typ == "svg":
                D.draw_svg(cv, el.get("svg", ""), float(el.get("w", 0.4)) * W)
        finally:
            if layered:
                cv.restore()
            cv.restore()

    def _draw_on(self, el, t):
        if el.get("enter") != "draw":
            return 1.0
        return ease("out", (t - float(el.get("at", 0))) / max(0.1, float(el.get("enter_dur", 0.8))))

    def _text(self, cv, el, t, xf):
        W = self.W
        typ = el["type"]
        style = el.get("style", "title" if typ != "emoji" else "emoji")
        if typ == "counter":
            text = D.counter_text(el, t)
            style = el.get("style", "big")
        else:
            text = str(el.get("text", ""))
        if xf.reveal < 1.0:
            words = text.split()
            n = int(math.ceil(len(words) * xf.reveal))
            text = " ".join(words[:n])
            if not text:
                return
        size = float(el.get("size", 0.08 if typ != "emoji" else 0.18)) * W
        width = float(el.get("width", 0.88)) * W
        color = el.get("color", "#ffffff")
        hl = set(el.get("highlight", []) or [])
        hl_color = el.get("highlight_color", "#ffd400")
        if hl and typ == "text":
            runs = []
            toks = text.split(" ")
            for j, tok in enumerate(toks):
                clean = re.sub(r"[^\wऀ-ॿ]", "", tok)
                runs.append((tok + (" " if j < len(toks) - 1 else ""), hl_color if clean in hl or tok in hl else color))
        else:
            runs = [(text, color)]
        stroke_on = el.get("stroke", typ != "emoji")
        sw = 0.0
        if stroke_on:
            sw = size * float(el.get("stroke_w", 0.16))
        blk = text_block(tuple(runs), width, size, style=style, align=el.get("align", "center"),
                         stroke=sw, stroke_color=el.get("stroke_color", "#000000") if isinstance(stroke_on, bool) else stroke_on,
                         line_height=float(el.get("line_height", 1.1)), shadow=el.get("shadow", True))
        if el.get("bg"):
            pad = size * 0.4
            w2 = blk.text_width / 2 + pad
            h2 = blk.height / 2 + pad * 0.5
            rr = skia.RRect.MakeRectXY(skia.Rect(-w2, -h2, w2, h2), size * float(el.get("bg_radius", 0.4)), size * float(el.get("bg_radius", 0.4)))
            cv.drawRRect(rr, D.fill(el["bg"], float(el.get("bg_alpha", 0.92))))
            if el.get("bg_stroke"):
                cv.drawRRect(rr, D.stroke(el["bg_stroke"], size * 0.08))
        blk.paint(cv, 0, 0)

    def _image(self, cv, el, t):
        img = D.load_image(el.get("path", ""))
        if img is None:
            return
        W = self.W
        w = float(el.get("w", 0.6)) * W
        h = w * img.height() / img.width() if not el.get("h") else float(el["h"]) * W
        rad = float(el.get("radius", 0.03)) * W
        rect = skia.Rect(-w / 2, -h / 2, w / 2, h / 2)
        cv.save()
        clip = skia.Path()
        clip.addRRect(skia.RRect.MakeRectXY(rect, rad, rad))
        cv.clipPath(clip, doAntiAlias=True)
        z = 1.0 + float(el.get("zoom", 0.08)) * clamp(t / 6)
        iw, ih = img.width(), img.height()
        s = max(w / iw, h / ih) * z
        cv.drawImageRect(img, skia.Rect(-iw * s / 2, -ih * s / 2, iw * s / 2, ih * s / 2), skia.SamplingOptions(skia.FilterMode.kLinear))
        cv.restore()
        if el.get("border"):
            cv.drawRRect(skia.RRect.MakeRectXY(rect, rad, rad), D.stroke(el["border"], W * 0.008))

    # ---------------------------------------------------------- scenes
    def footage_bg(self, i):
        """The scene's background dict when it is resolved stock footage (has a prepared `_file`), else None."""
        bg = self.spec["scenes"][i].get("background") or {}
        if bg.get("type") == "footage" and bg.get("_file") and os.path.exists(bg["_file"]):
            return bg
        return None

    def draw_scene(self, cv, i, t, gframe, as_prev=False):
        sc = self.spec["scenes"][i]
        seg = self.tl[i]
        W, H = self.W, self.H
        dur = seg["dur"]
        amp = float(self.amp[min(len(self.amp) - 1, max(0, gframe))]) if len(self.amp) else 0.0
        cam = sc.get("camera") or {}
        z0, z1 = cam.get("zoom", [1.0, 1.06])
        z = z0 + (z1 - z0) * ease("in_out", t / max(0.1, dur))
        pan = cam.get("pan", [0, 0])
        cv.save()
        cv.translate(W / 2, H / 2)
        cv.scale(z, z)
        cv.translate(-W / 2 + pan[0] * W * t / max(0.1, dur), -H / 2 + pan[1] * H * t / max(0.1, dur))
        if cam.get("shake"):
            cv.translate(math.sin(t * 50) * W * 0.004, math.cos(t * 41) * W * 0.004)
        D.draw_background(cv, sc.get("background") or self.spec.get("background") or {"type": "gradient"}, t, W, H,
                          {"scene_dur": dur, "as_prev": as_prev})
        for el in sc.get("elements", []) or []:
            if not el.get("overlay"):
                self._element(cv, el, t, dur, amp)
        cv.restore()
        for el in sc.get("elements", []) or []:
            if el.get("overlay"):
                self._element(cv, el, t, dur, amp)
        self._draw_captions(cv, i, t)

    def draw_frame(self, cv, i, local_frame):
        """Draw frame `local_frame` of scene i, including the transition in from scene i-1."""
        seg = self.tl[i]
        gframe = seg["start_frame"] + local_frame
        t = local_frame / self.fps
        trans = (self.spec["scenes"][i].get("transition") or self.spec.get("transition", "fade")) if i > 0 else "none"
        T = float(self.spec.get("transition_dur", 0.35))
        W, H = self.W, self.H
        if i > 0 and trans != "none" and t < T and self.footage_bg(i) is not None:
            # the live footage sits under the Skia layer, so the outgoing scene must fade out instead of being
            # painted opaque under the incoming one: every transition becomes a cross-fade on footage scenes
            u = ease("in_out", t / T)
            prev = self.tl[i - 1]
            cv.saveLayerAlpha(None, int(255 * (1 - u)))
            self.draw_scene(cv, i - 1, prev["dur"] + t, gframe, as_prev=True)
            cv.restore()
            self.draw_scene(cv, i, t, gframe)
        elif i > 0 and trans != "none" and t < T:
            u = ease("in_out", t / T)
            prev = self.tl[i - 1]
            self.draw_scene(cv, i - 1, prev["dur"] + t, gframe, as_prev=True)
            if trans == "fade":
                cv.saveLayerAlpha(None, int(255 * u))
                self.draw_scene(cv, i, t, gframe)
                cv.restore()
            elif trans in ("slide_left", "slide_up"):
                cv.save()
                if trans == "slide_left":
                    cv.translate((1 - u) * W, 0)
                else:
                    cv.translate(0, (1 - u) * H)
                self.draw_scene(cv, i, t, gframe)
                cv.restore()
            elif trans == "circle":
                cv.save()
                p = skia.Path()
                p.addCircle(W / 2, H / 2, u * math.hypot(W, H) / 2)
                cv.clipPath(p, doAntiAlias=True)
                self.draw_scene(cv, i, t, gframe)
                cv.restore()
            elif trans == "zoom":
                cv.saveLayerAlpha(None, int(255 * u))
                cv.translate(W / 2, H / 2)
                s = 1.25 - 0.25 * u
                cv.scale(s, s)
                cv.translate(-W / 2, -H / 2)
                self.draw_scene(cv, i, t, gframe)
                cv.restore()
            else:
                self.draw_scene(cv, i, t, gframe)
        else:
            self.draw_scene(cv, i, t, gframe)
        self._overlay(cv, gframe)

    def _overlay(self, cv, gframe):
        ov = self.spec.get("overlay") or {}
        W, H = self.W, self.H
        if ov.get("progress_bar", True):
            u = gframe / max(1, self.total_frames - 1)
            cv.drawRect(skia.Rect(0, 0, W, H * 0.006), D.fill("#000000", 0.35))
            cv.drawRect(skia.Rect(0, 0, W * u, H * 0.006), D.fill(ov.get("bar_color", "#ffd400")))
        if ov.get("handle"):
            blk = text_block(((ov["handle"], "#ffffff"),), W * 0.6, W * 0.032, style="label", stroke=W * 0.006,
                             stroke_color="#000000", shadow=False)
            cv.saveLayerAlpha(None, 170)
            blk.paint(cv, W / 2, H * 0.955)
            cv.restore()

    # ---------------------------------------------------------- output
    def still(self, i, t, path):
        arr = np.zeros((self.H, self.W, 4), dtype=np.uint8)
        surf = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        cv = surf.getCanvas()
        cv.clear(skia.ColorBLACK)
        lf = int(round(t * self.fps))
        lf = max(0, min(self.tl[i]["frames"] - 1, lf))
        fbg = self.footage_bg(i)
        if fbg is not None:
            # composite the real footage frame under the drawing so QA judges true readability
            from .footage import extract_frame
            png = extract_frame(fbg["_file"], lf / self.fps, path + ".bg.png")
            img = skia.Image.open(png) if png else None
            if img is not None:
                D._draw_cover(cv, img, self.W, self.H)
            try:
                os.remove(path + ".bg.png")
            except OSError:
                pass
        self.draw_frame(cv, i, lf)
        surf.flushAndSubmit() if hasattr(surf, "flushAndSubmit") else None
        img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
        fmt = skia.kJPEG if path.lower().endswith((".jpg", ".jpeg")) else skia.kPNG
        img.save(path, fmt, 92) if fmt == skia.kJPEG else img.save(path, fmt)
        return path

    def encode_scene(self, i, path, crf=20, preset="veryfast", threads=0):
        seg = self.tl[i]
        W, H = self.W, self.H
        tmp = path[:-4] + ".part.mp4"
        fbg = self.footage_bg(i)
        pipe = ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(self.fps), "-i", "-"]
        if fbg is None:
            cmd = ["ffmpeg", "-y", "-loglevel", "error"] + pipe + [
                   "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                   "-pix_fmt", "yuv420p", "-r", str(self.fps), "-movflags", "+faststart"]
        else:
            # input 0: prepared footage (already WxH, fps, long enough); input 1: the transparent Skia frames.
            # Skia hands over premultiplied RGBA, so unpremultiply before the overlay blends it.
            blur = float(fbg.get("blur", 0) or 0)
            bgf = (f"boxblur={blur:.1f}:1," if blur > 0 else "") + "format=yuv420p"
            fc = (f"[0:v]{bgf}[bg];[1:v]unpremultiply=inplace=1[fg];"
                  "[bg][fg]overlay=0:0:format=auto:shortest=1:eof_action=endall,format=yuv420p[v]")
            cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", fbg["_file"]] + pipe + [
                   "-filter_complex", fc, "-map", "[v]", "-shortest", "-frames:v", str(seg["frames"]),
                   "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                   "-pix_fmt", "yuv420p", "-r", str(self.fps), "-movflags", "+faststart"]
        if threads:
            cmd += ["-threads", str(threads)]
        cmd.append(tmp)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        arr = np.zeros((H, W, 4), dtype=np.uint8)
        surf = skia.Surface(arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        cv = surf.getCanvas()
        clear = skia.ColorBLACK if fbg is None else skia.ColorTRANSPARENT
        try:
            for f in range(seg["frames"]):
                cv.clear(clear)
                self.draw_frame(cv, i, f)
                proc.stdin.write(arr.tobytes())
        finally:
            proc.stdin.close()
            rc = proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg failed for scene {i} (exit {rc})")
        os.replace(tmp, path)
        return path


DEFAULT_CAPTIONS = {
    "enabled": True,
    "style": "karaoke",
    "y": 0.74,
    "size": 0.078,
    "max_words": 3,
    "color": "#ffffff",
    "highlight": "#ffd400",
    "stroke": "#000000",
    "uppercase": False,
    "box": None,
}
