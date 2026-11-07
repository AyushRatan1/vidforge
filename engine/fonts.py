"""Font registry and shaped text rendering (Devanagari + Latin) on Skia."""
from __future__ import annotations

import os
import re
from functools import lru_cache

import skia

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

# family name -> candidate files (first that exists wins)
_FONT_FILES = {
    "Mukta": ["Mukta-ExtraBold.ttf", "Mukta-Bold.ttf"],
    "Baloo 2": ["Baloo2.ttf"],
    "Noto Sans Devanagari": ["NotoSansDevanagari.ttf"],
    "Poppins": ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf", "Poppins-Bold.ttf"],
    "Noto Color Emoji": ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "NotoColorEmoji.ttf"],
}

DEVANAGARI = re.compile(r"[ऀ-ॿ]")

_collection = None


def _resolve(path: str) -> str | None:
    for cand in (path, os.path.join(FONT_DIR, path)):
        if os.path.exists(cand):
            return cand
    return None


def collection() -> skia.textlayout_FontCollection:
    global _collection
    if _collection is None:
        prov = skia.textlayout_TypefaceFontProvider()
        for files in _FONT_FILES.values():
            for f in files:
                p = _resolve(f)
                if p:
                    tf = skia.Typeface.MakeFromFile(p)
                    if tf:
                        prov.registerTypeface(tf)
        fc = skia.textlayout_FontCollection()
        fc.setDefaultFontManager(prov)
        _collection = fc
    return _collection


STYLE_FAMILIES = {
    # style -> (latin family, devanagari family, weight)
    "title": (["Baloo 2", "Mukta"], ["Mukta", "Baloo 2"], 800),
    "big": (["Baloo 2", "Mukta"], ["Mukta", "Baloo 2"], 800),
    "body": (["Poppins", "Mukta"], ["Mukta", "Noto Sans Devanagari"], 700),
    "label": (["Poppins", "Mukta"], ["Mukta"], 700),
    "caption": (["Poppins", "Mukta"], ["Mukta"], 800),
    "story": (["Baloo 2", "Mukta"], ["Baloo 2", "Mukta"], 700),
    "emoji": (["Noto Color Emoji"], ["Noto Color Emoji"], 400),
}


def families_for(text: str, style: str):
    lat, dev, weight = STYLE_FAMILIES.get(style, STYLE_FAMILIES["body"])
    fams = list(dev if DEVANAGARI.search(text or "") else lat)
    # always allow Devanagari, Latin and emoji glyphs to fall back
    for extra in ("Mukta", "Poppins", "Noto Color Emoji"):
        if extra not in fams:
            fams.append(extra)
    return fams, weight


def _color(c) -> int:
    return c if isinstance(c, int) else hex_color(c)


@lru_cache(maxsize=512)
def hex_color(h: str, alpha: float = 1.0) -> int:
    h = (h or "#ffffff").strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) == 8:
        a = int(h[6:8], 16) / 255.0
        h = h[:6]
        alpha *= a
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        r, g, b = 255, 255, 255
    return skia.ColorSetARGB(int(max(0, min(1, alpha)) * 255), r, g, b)


def make_paragraph(
    runs,
    width: float,
    size: float,
    style: str = "body",
    align: str = "center",
    stroke: float = 0.0,
    stroke_color: str = "#000000",
    line_height: float = 1.1,
    letter_spacing: float = 0.0,
):
    """runs: list of (text, color_hex). Returns a laid-out paragraph.

    When stroke > 0 the paragraph paints only the outline (draw it first, then fill).
    """
    full = "".join(t for t, _ in runs)
    fams, weight = families_for(full, style)
    ps = skia.textlayout_ParagraphStyle()
    ps.setTextAlign(
        {
            "center": skia.textlayout_TextAlign.kCenter,
            "left": skia.textlayout_TextAlign.kLeft,
            "right": skia.textlayout_TextAlign.kRight,
        }.get(align, skia.textlayout_TextAlign.kCenter)
    )
    b = skia.textlayout_ParagraphBuilder.make(ps, collection(), skia.Unicode())
    for text, color in runs:
        ts = skia.textlayout_TextStyle()
        ts.setFontFamilies(fams)
        ts.setFontSize(size)
        ts.setFontStyle(skia.FontStyle(weight, skia.FontStyle.kNormal_Width, skia.FontStyle.kUpright_Slant))
        ts.setHeight(line_height)
        ts.setHeightOverride(True)
        if letter_spacing:
            ts.setLetterSpacing(letter_spacing)
        p = skia.Paint(AntiAlias=True)
        if stroke > 0:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(stroke)
            p.setStrokeJoin(skia.Paint.kRound_Join)
            p.setColor(_color(stroke_color))
        else:
            p.setColor(_color(color))
        ts.setForegroundPaint(p)
        b.pushStyle(ts)
        b.addText(text)
        b.pop()
    para = b.Build()
    para.layout(width)
    return para


class TextBlock:
    """A cached stroke+fill paragraph pair, painted centered on (cx, cy)."""

    def __init__(self, runs, width, size, style="body", align="center", stroke=0.0,
                 stroke_color="#000000", line_height=1.1, shadow=True):
        self.fill = make_paragraph(runs, width, size, style, align, 0, stroke_color, line_height)
        self.outline = (
            make_paragraph(runs, width, size, style, align, stroke, stroke_color, line_height)
            if stroke > 0 else None
        )
        self.shadow = shadow and stroke > 0
        self.width = width
        self.height = self.fill.Height
        self.text_width = self.fill.LongestLine

    def paint(self, canvas: skia.Canvas, cx: float, cy: float):
        x = cx - self.width / 2
        y = cy - self.height / 2
        if self.shadow and self.outline is not None:
            canvas.save()
            canvas.translate(0, self.fill.Height * 0.06)
            canvas.saveLayerAlpha(None, 90)
            self.outline.paint(canvas, x, y)
            canvas.restore()
            canvas.restore()
        if self.outline is not None:
            self.outline.paint(canvas, x, y)
        self.fill.paint(canvas, x, y)


_block_cache: dict = {}


def text_block(key_runs: tuple, width: float, size: float, **kw) -> TextBlock:
    key = (key_runs, round(width), round(size, 1), tuple(sorted(kw.items())))
    blk = _block_cache.get(key)
    if blk is None:
        if len(_block_cache) > 2000:
            _block_cache.clear()
        blk = TextBlock(list(key_runs), width, size, **kw)
        _block_cache[key] = blk
    return blk
