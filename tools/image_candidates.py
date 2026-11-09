"""Contact sheets of Pixabay image candidates, so stills for a long video can be chosen by eye and pinned by id.

    python -m tools.image_candidates subjects.json out_dir

subjects.json maps a subject name to a list of [query, kind] pairs (kind: photo, illustration, vector or all):
    {"rama": [["lord rama", "illustration"], ["shri ram", "all"]], "palace": [["amer fort", "photo"]]}
Writes out_dir/sheet_NN.jpg (two subjects per sheet, 12 candidates each, every tile labelled with its Pixabay id)
and out_dir/candidates.json (id, tags, size, page for every tile). Pin a pick in a spec with
{"type": "footage", "image_id": 1234567}.
"""
from __future__ import annotations

import io
import json
import os
import sys

import requests
from PIL import Image, ImageDraw, ImageFont

from engine import footage as F

TW, TH, COLS, ROWS, GAP, HEAD = 320, 180, 4, 3, 4, 34
PER_SHEET = 2


def _font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def candidates(queries: list, n: int = COLS * ROWS) -> list[dict]:
    """Round robin over the queries (best liked first within each) so every query gets a few tiles."""
    lists = []
    for q, kind in queries:
        got = F.search_images(q, kind=kind, orientation="horizontal", per_page=24)
        got += F.search_images(q, kind=kind, orientation="all", per_page=24)
        lists.append([dict(c, query=q) for c in got])
    seen, out = set(), []
    for rank in range(48):
        for lst in lists:
            if rank < len(lst) and lst[rank]["id"] not in seen:
                seen.add(lst[rank]["id"])
                out.append(lst[rank])
                if len(out) >= n:
                    return out
    return out


def _thumb(url: str) -> Image.Image:
    tile = Image.new("RGB", (TW, TH), (24, 20, 16))
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content))
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            ground = Image.new("RGBA", im.size, (28, 20, 12, 255))
            im = Image.alpha_composite(ground, im)
        im = im.convert("RGB")
        im.thumbnail((TW, TH))
        tile.paste(im, ((TW - im.width) // 2, (TH - im.height) // 2))
    except Exception as e:  # a missing thumbnail just shows an empty tile
        ImageDraw.Draw(tile).text((10, 10), f"no preview: {e}"[:40], fill=(200, 80, 80), font=_font(12))
    return tile


def sheet(groups: list[tuple[str, list[dict]]]) -> Image.Image:
    block_h = HEAD + ROWS * (TH + GAP)
    img = Image.new("RGB", (COLS * (TW + GAP), len(groups) * block_h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    big, small = _font(22), _font(15)
    for g, (name, cands) in enumerate(groups):
        y0 = g * block_h
        d.text((8, y0 + 6), name, fill=(255, 213, 74), font=big)
        for i, c in enumerate(cands[: COLS * ROWS]):
            x, y = (i % COLS) * (TW + GAP), y0 + HEAD + (i // COLS) * (TH + GAP)
            img.paste(_thumb(c.get("thumb") or c["url"]), (x, y))
            label = f"{str(c['id']).removeprefix('img')}{'  V' if '/vectors/' in c.get('page_url', '') else ''}"
            w = d.textlength(label, font=small)
            d.rectangle((x, y + TH - 22, x + w + 10, y + TH), fill=(0, 0, 0))
            d.text((x + 5, y + TH - 20), label, fill=(255, 255, 255), font=small)
    return img


def main(path: str, out_dir: str) -> None:
    with open(path, encoding="utf-8") as f:
        subjects = json.load(f)
    os.makedirs(out_dir, exist_ok=True)
    found, names = {}, list(subjects)
    for name in names:
        found[name] = candidates(subjects[name])
        print(f"{name}: {len(found[name])} candidates")
    for k in range(0, len(names), PER_SHEET):
        group = [(n, found[n]) for n in names[k:k + PER_SHEET]]
        sheet(group).save(os.path.join(out_dir, f"sheet_{k // PER_SHEET + 1:02d}.jpg"), quality=86)
    slim = {n: [{"id": str(c["id"]).removeprefix("img"), "query": c.get("query"), "tags": c.get("tags"),
                 "size": f"{c.get('width')}x{c.get('height')}", "page": c.get("page_url")} for c in found[n]]
            for n in names}
    with open(os.path.join(out_dir, "candidates.json"), "w", encoding="utf-8") as f:
        json.dump(slim, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
