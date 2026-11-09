"""Shared helpers for long-video build scripts (longform/<name>/build.py).

A build script lists chapters as (chapter_id, title, [scenes]) and calls build(); every chapter becomes an ordinary
VidForge spec (chNN.json) that the longform workflow renders in parallel and joins into one video.
Stills are pinned by Pixabay id after reviewing candidate sheets (tools/image_candidates.py).
"""
import json
import os

FALLBACK = {"type": "gradient", "colors": ["#1d1a17", "#0d0b09"]}
MOVES = ("in", "out", "left", "right")


def pin(image_id, move="in", dim=0.14):
    return {"type": "footage", "image_id": image_id, "move": move, "dim": dim, "fallback": FALLBACK}


def vid(q, dim=0.2):
    return {"type": "footage", "query": q, "dim": dim, "fallback": FALLBACK}


def card(text):
    return {"type": "text", "text": text, "x": 0.5, "y": 0.13, "size": 0.034, "color": "#1c1a17", "bg": "#ffd54a",
            "style": "label", "stroke": False, "enter": "pop", "at": 0.2, "until": 4.5}


def tag(text, at_word=None, y=0.13, until=None):
    el = {"type": "text", "text": text, "x": 0.5, "y": y, "size": 0.026, "color": "#ffffff", "bg": "#1c1a17",
          "bg_alpha": 0.78, "style": "label", "stroke": False, "enter": "fade"}
    if at_word:
        el["at_word"] = at_word
    else:
        el["at"] = 0.3
    if until:
        el["until"] = until
    return el


def S(narration, bg, *elements):
    return {"narration": narration, "background": bg, "elements": list(elements)}


def build(here, chapters, base, title_fmt, seed=200):
    for k, (cid, title, scenes) in enumerate(chapters, 1):
        spec = json.loads(json.dumps(base))
        spec["title"] = title_fmt.format(k=k, title=title)
        spec.setdefault("music", {})["seed"] = seed + k
        for i, sc in enumerate(scenes):
            sc.setdefault("id", f"{cid}_{i + 1:02d}")
        spec["scenes"] = scenes
        with open(os.path.join(here, f"{cid}.json"), "w", encoding="utf-8") as f:
            json.dump(spec, f, ensure_ascii=False, indent=1)
    words = sum(len(sc["narration"].split()) for _, _, scs in chapters for sc in scs)
    print(f"{len(chapters)} chapters, {sum(len(s) for _, _, s in chapters)} scenes, {words} words")
