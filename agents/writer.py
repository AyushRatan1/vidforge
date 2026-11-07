"""Writer/director: idea + fact sheet -> renderable scene spec. Validates and self-repairs once."""
from __future__ import annotations

import json
import os

from engine.validate import validate

from .formats import format_brief
from .llm import Claude
from .scene_guide import SCENE_GUIDE

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


def _example_for(channel: dict) -> str:
    """Show the writer a finished spec in the same language/audience as the channel."""
    if channel.get("audience") == "kids":
        name = "kids_counting_hi.json"
    elif channel.get("language") == "en":
        name = "space_is_weird_01_voyager.json"
    else:
        name = "leonids_hi.json"
    try:
        return open(os.path.join(EXAMPLES_DIR, name), encoding="utf-8").read()
    except OSError:
        return "{}"

SYSTEM_TMPL = """You are the head writer and animation director of a faceless video channel for Indian audiences.
You write the script AND direct every scene as a JSON scene spec that a renderer turns into video.

{guide}

LANGUAGE
- "hi": natural spoken Hindi (Devanagari), the way a friendly teacher talks, English technical words are fine
  when Indians actually say them (e.g. "पीक", "ISRO" -> "इसरो"). Short sentences.
- "hinglish": narration still in Devanagari for the voice; captions may be Roman Hinglish via the caption field.
- "en": Indian-English friendly tone; use voices af_heart or am_michael unless the channel says otherwise.

TRUTH
- Use ONLY the facts in the fact sheet. If a number is approximate say "करीब"/"about". Never invent quotes,
  statistics, dates or scripture. Put the sources in the description.
- Kids formats: gentle, educational, no unsafe behaviour on screen, no scary imagery, made_for_kids=true.
- Never use existing copyrighted characters, logos, songs or film footage. Original mascots only.
- Add the line "Visuals and voice are AI-assisted." to the description.

Return the complete spec by calling submit_episode. Here is a finished example of the quality bar:
{example}
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"}, "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "language": {"type": "string"}, "voice": {"type": "string"}, "speed": {"type": "number"},
        "aspect": {"type": "string", "enum": ["9:16", "16:9", "1:1"]},
        "made_for_kids": {"type": "boolean"}, "category": {"type": "string"},
        "music": {"type": "object"}, "captions": {"type": "object"}, "overlay": {"type": "object"},
        "thumbnail": {"type": "object"}, "transition": {"type": "string"},
        "scenes": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "narration": {"type": "string"}, "caption": {"type": "string"},
            "background": {"type": "object"}, "camera": {"type": "object"}, "transition": {"type": "string"},
            "sfx": {"type": "array"}, "hold": {"type": "number"},
            "elements": {"type": "array", "items": {"type": "object"}},
        }, "required": ["id", "narration", "elements"]}},
    },
    "required": ["title", "description", "tags", "language", "voice", "aspect", "made_for_kids", "scenes"],
}


def _system(channel: dict | None = None):
    return SYSTEM_TMPL.format(guide=SCENE_GUIDE, example=_example_for(channel or {}))


def write_episode(claude: Claude, idea: dict, facts: dict, channel: dict, notes: str = "") -> dict:
    fmt = idea.get("format") or (channel.get("formats") or ["space_facts"])[0]
    prompt = (
        f"CHANNEL\n{json.dumps({k: channel.get(k) for k in ('name', 'niche', 'language', 'caption_script', 'audience', 'voice', 'mascot', 'handle', 'palette', 'notes')}, ensure_ascii=False, indent=1)}\n\n"
        f"{format_brief(fmt)}\n\nIDEA\n{json.dumps(idea, ensure_ascii=False, indent=1)}\n\n"
        f"FACT SHEET\n{json.dumps(facts, ensure_ascii=False, indent=1)}\n\n"
        + (f"OWNER NOTES\n{notes}\n\n" if notes else "")
        + "Write and direct the episode now."
    )
    system = _system(channel)
    spec = claude.json_tool("writer", system, prompt, "submit_episode", "Submit the complete episode spec",
                            SCHEMA, max_tokens=32000)
    return _repair_loop(claude, spec, prompt, system)


def revise(claude: Claude, spec: dict, instructions: str, facts: dict | None = None, channel: dict | None = None) -> dict:
    prompt = (
        f"Here is the current episode spec:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
        + (f"Fact sheet:\n{json.dumps(facts, ensure_ascii=False)}\n\n" if facts else "")
        + f"Revise it. Keep everything that works; change what this asks for:\n{instructions}\n\n"
          "Return the complete revised spec via submit_episode."
    )
    system = _system(channel or {"language": spec.get("language"), "audience": "kids" if spec.get("made_for_kids") else "general"})
    out = claude.json_tool("writer", system, prompt, "submit_episode", "Submit the complete episode spec",
                           SCHEMA, max_tokens=32000)
    return _repair_loop(claude, out, prompt, system)


def _repair_loop(claude: Claude, spec: dict, prompt: str, system: str) -> dict:
    errs, warns = validate(spec)
    if not errs and len(warns) <= 3:
        spec["_lint"] = warns
        return spec
    fix = ("The spec failed validation. Fix every error and as many warnings as sensible, keep the rest unchanged, "
           "and resubmit the complete spec.\nERRORS:\n- " + "\n- ".join(errs or ["none"]) +
           "\nWARNINGS:\n- " + "\n- ".join(warns or ["none"]))
    history = [{"role": "user", "content": prompt},
               {"role": "assistant", "content": [{"type": "text", "text": json.dumps(spec, ensure_ascii=False)}]}]
    spec2 = claude.json_tool("writer", system, fix, "submit_episode", "Submit the complete episode spec",
                             SCHEMA, max_tokens=32000, history=history)
    errs2, warns2 = validate(spec2)
    spec2["_lint"] = errs2 + warns2
    return spec2
