"""Static checks on a scene spec before rendering. Returns (errors, warnings) as readable strings."""
from __future__ import annotations

import unicodedata

from .draw import BACKGROUNDS, PLANETS, PROPS, SPECIES

ELEMENT_TYPES = {"text", "counter", "emoji", "planet", "character", "prop", "shape", "particles",
                 "constellation", "image", "svg"}
ENTERS = {None, "none", "pop", "fade", "grow", "drop", "slide_up", "slide_down", "slide_left", "slide_right",
          "spin_in", "typewriter", "draw"}
BEHAVIORS = {"float", "bob", "spin", "pulse", "sway", "bounce", "squash", "wiggle", "orbit", "twinkle", "drift", "shake"}
PARTICLES = {"confetti", "sparkles", "snow", "bubbles", "fireflies", "rain", "hearts", "stars", "leaves", "meteors", "stream"}
TRANSITIONS = {None, "fade", "slide_left", "slide_up", "zoom", "circle", "none"}
from .audio import VOICES as _VOICE_MAP

VOICES = set(_VOICE_MAP)
MOODS = {"cosmic", "playful", "mystery", "epic", "calm", "upbeat", "indian", "devotional", "none"}


def _check_footage(bg: dict) -> list[str]:
    errs = []
    if not (str(bg.get("query", "")).strip() or str(bg.get("image", "")).strip() or bg.get("image_id")):
        errs.append("footage background needs a `query` (2-4 concrete English words), or `image` / `image_id` for a still")
    if bg.get("move") is not None and bg.get("move") not in ("in", "out", "left", "right", "up", "down"):
        errs.append(f"footage move {bg.get('move')!r} must be in, out, left, right, up or down")
    try:
        dim = float(bg.get("dim", 0.45))
        if not 0 <= dim <= 0.9:
            errs.append(f"footage dim {dim} must be between 0 and 0.9")
    except (TypeError, ValueError):
        errs.append(f"footage dim {bg.get('dim')!r} must be a number")
    fb = bg.get("fallback")
    if fb is not None:
        if not isinstance(fb, dict) or fb.get("type") not in BACKGROUNDS or fb.get("type") == "footage":
            errs.append(f"footage fallback must be a drawn background, not {fb!r}")
    return errs


def validate(spec: dict) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    scenes = spec.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return ["`scenes` must be a non-empty list"], warns
    if spec.get("voice") and spec["voice"] not in VOICES:
        errs.append(f"unknown voice {spec['voice']!r}; use one of {sorted(VOICES)}")
    mood = (spec.get("music") or {}).get("mood")
    if mood and mood not in MOODS:
        warns.append(f"unknown music mood {mood!r}, falling back to cosmic")
    if not spec.get("title"):
        warns.append("missing title")
    if spec.get("footage") not in (None, "auto", "off"):
        errs.append(f"`footage` must be \"auto\" or \"off\", not {spec.get('footage')!r}")
    hindi = spec.get("language") in ("hi", "hinglish") or str(spec.get("voice", "")).startswith("h")
    if spec.get("language") not in (None, "en", "hi", "hinglish", "es", "fr", "it", "pt"):
        warns.append(f"language {spec.get('language')!r} has no matching voice; narration will use {spec.get('voice')}")
    if spec.get("world3d") is not None:
        from .world3d import validate_world
        ids = {str(k + 1) for k in range(len(scenes))} | {str(sc.get("id")) for sc in scenes if sc.get("id")}
        e3, w3 = validate_world(spec["world3d"], ids)
        errs += e3
        warns += w3
    total_chars = 0
    for i, sc in enumerate(scenes):
        where = f"scene {i + 1} ({sc.get('id', '?')})"
        nar = (sc.get("narration") or "").strip()
        if not nar:
            errs.append(f"{where}: narration is empty")
        total_chars += len(nar)
        if hindi and nar and sum(c.isdigit() for c in nar):
            warns.append(f"{where}: Hindi narration contains digits; spell numbers as words for the voice")
        if len(nar) > 220:
            warns.append(f"{where}: narration is long ({len(nar)} chars); split into two scenes")
        bg = sc.get("background") or {}
        if bg and bg.get("type") not in BACKGROUNDS:
            errs.append(f"{where}: unknown background type {bg.get('type')!r}")
        if bg.get("type") == "footage":
            errs += [f"{where}: {e}" for e in _check_footage(bg)]
        if sc.get("transition") not in TRANSITIONS:
            warns.append(f"{where}: unknown transition {sc.get('transition')!r}")
        els = sc.get("elements") or []
        if not els and not (spec.get("world3d") and bg.get("type", "world3d") == "world3d"):
            warns.append(f"{where}: no elements; the scene will be just a background")
        for j, el in enumerate(els):
            ew = f"{where} element {j + 1}"
            typ = el.get("type")
            if typ not in ELEMENT_TYPES:
                errs.append(f"{ew}: unknown type {typ!r}")
                continue
            if el.get("enter") not in ENTERS:
                warns.append(f"{ew}: unknown enter {el.get('enter')!r}")
            for b in el.get("behaviors", []) or []:
                if b.get("kind") not in BEHAVIORS:
                    warns.append(f"{ew}: unknown behavior {b.get('kind')!r}")
            if typ == "planet" and el.get("style", "earth") not in PLANETS and el.get("style") not in ("black_hole", "neutron_star", "pulsar"):
                errs.append(f"{ew}: unknown planet style {el.get('style')!r}")
            if typ == "prop" and el.get("name") not in PROPS:
                errs.append(f"{ew}: unknown prop {el.get('name')!r}; available: {sorted(PROPS)}")
            if typ == "character" and el.get("species", "blob") not in SPECIES:
                errs.append(f"{ew}: unknown species {el.get('species')!r}")
            if typ == "particles" and el.get("kind") not in PARTICLES:
                errs.append(f"{ew}: unknown particle kind {el.get('kind')!r}")
            if typ in ("text", "emoji") and not str(el.get("text", "")).strip():
                errs.append(f"{ew}: empty text")
            if typ == "text":
                words = len(str(el.get("text", "")).split())
                size = float(el.get("size", 0.08))
                if words > 8:
                    warns.append(f"{ew}: {words} words on screen; keep text to 2-6 words")
                visible = sum(1 for ch in str(el.get("text", "")) if unicodedata.category(ch) not in ("Mn", "Mc"))
                if size * visible > 1.6 and not el.get("width"):
                    warns.append(f"{ew}: text may wrap to many lines at size {size}")
            if typ not in ("particles",) and not el.get("overlay"):
                y = float(el.get("y", 0.5))
                if 0.69 <= y <= 0.81 and typ in ("text", "counter"):
                    warns.append(f"{ew}: sits in the caption band (y≈0.70-0.80); move it")
            if typ == "image" and not el.get("path"):
                errs.append(f"{ew}: image needs a path")
            if typ == "svg" and "<svg" not in str(el.get("svg", "")):
                errs.append(f"{ew}: svg element needs inline <svg> markup")
    est = total_chars / (14.5 if hindi else 15.5)  # rough seconds of speech
    if spec.get("aspect", "9:16") == "9:16" and est > 62:
        warns.append(f"estimated length {est:.0f}s; Shorts work best under 58s")
    return errs, warns
