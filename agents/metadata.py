"""Posting metadata: YouTube title/description/tags/hashtags and the Instagram caption, written by Claude and then
hard-checked against each platform's current rules.

Rules encoded (Nov 2026):
- Instagram caps captions at 5 hashtags (rolled out from Dec 2025); 2,200-character captions.
- YouTube shows up to 3 hashtags above the title, ignores all hashtags past 60 and penalises over-tagging;
  titles max 100 characters, descriptions 5,000, tags field about 500 characters in total.
"""
from __future__ import annotations

import json
import re
import unicodedata

from .llm import Claude

IG_MAX_TAGS = 5
YT_MAX_TAGS = 5           # we stay well under YouTube's limits on purpose
YT_TITLE_MAX = 100
YT_DESC_MAX = 5000
YT_TAGS_CHARS = 480
IG_CAPTION_MAX = 2200
AI_LINE = "Visuals and voice are AI-assisted."

SYSTEM = """You write the posting copy for short videos on YouTube Shorts and Instagram Reels. You get the final
script, the fact sheet and the channel profile. Write copy that makes the right people stop and watch, in the
video's language. Rules:
- YouTube title: under 70 characters before " #Shorts", curiosity without clickbait lies, the key subject early.
- YouTube description: 2-4 short lines expanding the hook, one line of sources if facts are cited, then hashtags.
- Hashtags: specific beats generic. Mix 1 broad topic tag, 2-3 niche tags, and the channel's brand tag(s).
  Never add unrelated trending tags, never pad. No spaces inside a hashtag. Hindi videos may use Hindi or
  Roman-script tags that Indians actually search.
- YouTube tags (the hidden tags field): 8-15 search phrases people would type, including spelling variants.
- Instagram caption: first line is the hook (it shows before "more"), then 1-3 lines of value, a soft call to
  comment or follow, then at most 5 hashtags.
- Kids videos: no calls to comment, nothing aimed at collecting data from children.
- Never invent facts; stay within the fact sheet."""

SCHEMA = {
    "type": "object",
    "properties": {
        "youtube": {"type": "object", "properties": {
            "title": {"type": "string"}, "description": {"type": "string"},
            "hashtags": {"type": "array", "items": {"type": "string"}},
            "tags": {"type": "array", "items": {"type": "string"}}},
            "required": ["title", "description", "hashtags", "tags"]},
        "instagram": {"type": "object", "properties": {
            "caption": {"type": "string"}, "hashtags": {"type": "array", "items": {"type": "string"}}},
            "required": ["caption", "hashtags"]},
    },
    "required": ["youtube", "instagram"],
}


def clean_tag(t: str) -> str:
    """'#Space facts!' -> '#SpaceFacts'; keeps Devanagari and other letters/digits/underscore."""
    t = (t or "").strip().lstrip("#")
    parts = re.split(r"[\s\-]+", t)
    t = "".join(p[:1].upper() + p[1:] if p and p[0].isascii() else p for p in parts)
    t = "".join(ch for ch in t if ch == "_" or unicodedata.category(ch)[0] in ("L", "N", "M"))
    return "#" + t if t else ""


def dedupe(tags):
    seen, out = set(), []
    for t in tags:
        c = clean_tag(t)
        if c and c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


def strip_hashtags(text: str) -> str:
    return re.sub(r"(?<!\w)#[^\s#]+", "", text or "").replace("  ", " ").strip()


def finalize(meta: dict, spec: dict, brand_tags=None, extra_tags=None) -> dict:
    """Enforce platform limits no matter what the model returned."""
    brand = dedupe(brand_tags or [])
    extra = dedupe(extra_tags or [])
    yt = meta.get("youtube") or {}
    ig = meta.get("instagram") or {}
    short = spec.get("aspect", "9:16") == "9:16"

    # YouTube
    yt_tags = [t for t in dedupe(extra + brand + list(yt.get("hashtags") or [])) if t.lower() != "#shorts"][:YT_MAX_TAGS]
    title = strip_hashtags(yt.get("title") or spec.get("title") or "")
    suffix = " #Shorts" if short else ""
    title = (title[: YT_TITLE_MAX - len(suffix)].rstrip() + suffix).strip()
    desc = strip_hashtags(yt.get("description") or spec.get("description") or "")
    if AI_LINE.lower() not in desc.lower():
        desc += "\n\n" + AI_LINE
    desc = (desc + "\n\n" + " ".join(yt_tags)).strip()[:YT_DESC_MAX]
    tags, used = [], 0
    for t in [s.strip().lstrip("#") for s in (yt.get("tags") or spec.get("tags") or [])]:
        if t and t.lower() not in [x.lower() for x in tags] and used + len(t) + 1 <= YT_TAGS_CHARS:
            tags.append(t[:100])
            used += len(t) + 1

    # Instagram
    ig_tags = dedupe(extra + brand + list(ig.get("hashtags") or []))[:IG_MAX_TAGS]
    cap = strip_hashtags(ig.get("caption") or "")
    if AI_LINE.lower() not in cap.lower():
        cap += "\n\n" + AI_LINE
    tail = "\n\n" + " ".join(ig_tags) if ig_tags else ""
    cap = cap[: IG_CAPTION_MAX - len(tail)].rstrip() + tail

    return {"youtube": {"title": title, "description": desc, "hashtags": yt_tags, "tags": tags},
            "instagram": {"caption": cap, "hashtags": ig_tags}}


def write_metadata(claude: Claude, spec: dict, facts: dict | None, channel: dict, extra_tags=None) -> dict:
    slim = {k: spec.get(k) for k in ("title", "description", "language", "made_for_kids", "aspect")}
    slim["script"] = [s.get("narration") for s in spec.get("scenes", [])]
    prompt = (f"CHANNEL\n{json.dumps({k: channel.get(k) for k in ('name', 'niche', 'language', 'audience', 'handle', 'brand_hashtags')}, ensure_ascii=False)}\n\n"
              f"VIDEO\n{json.dumps(slim, ensure_ascii=False, indent=1)}\n\n"
              f"FACT SHEET\n{json.dumps({'facts': (facts or {}).get('facts', [])[:8]}, ensure_ascii=False)}\n\n"
              + (f"ALWAYS INCLUDE THESE HASHTAGS: {' '.join(extra_tags)}\n\n" if extra_tags else "")
              + "Write the posting copy.")
    raw = claude.json_tool("metadata", SYSTEM, prompt, "submit_copy", "Submit the posting copy", SCHEMA, max_tokens=6000)
    return finalize(raw, spec, channel.get("brand_hashtags"), extra_tags)


def fallback_metadata(spec: dict, brand_tags=None, extra_tags=None) -> dict:
    """No Claude available: derive copy from the spec."""
    base = {"youtube": {"title": spec.get("title", ""), "description": spec.get("description", ""),
                        "hashtags": spec.get("tags", [])[:3], "tags": spec.get("tags", [])},
            "instagram": {"caption": (spec.get("title", "") + "\n\n" + (spec.get("description") or "").split("\n\n")[0]),
                          "hashtags": spec.get("tags", [])[:3]}}
    return finalize(base, spec, brand_tags, extra_tags)
