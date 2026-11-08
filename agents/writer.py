"""Writer/director: idea + fact sheet -> renderable scene spec. Validates and self-repairs once."""
from __future__ import annotations

import json
import os

from engine.validate import validate

from .formats import FORMATS, format_brief
from .llm import Claude
from .scene_guide import SCENE_GUIDE

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


def _example_for(channel: dict, fmt: str = "") -> str:
    """Show the writer a finished spec in the same format or language/audience as the channel."""
    if fmt == "3d_build":
        name = "built_rani_ki_vav.json"
    elif channel.get("audience") == "kids":
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
- "en": natural international English; voice af_heart unless the channel says otherwise.
- "es", "fr", "it", "pt": write narration and on-screen text in that language (voices ef_dora, ff_siwis, if_sara,
  pf_dora). Any other language: write in it, but warn in the description that the voice may sound foreign.
- Respect the target length and aspect in OWNER NOTES when given (e.g. "about 60 seconds", "16:9 long-form").

VISUALS
- When the channel niche or the topic is real-world (animals, nature, travel, food, sports, people, history,
  mythology, tech, festivals, news), give most scenes a background of type "footage" so real video plays under
  the text, and keep drawn mascots, counters and labels on top. Footage `query` values are ALWAYS short English
  visual phrases (2-4 words, what a camera would see), whatever the narration language, and should differ from
  scene to scene. Always set a `fallback` drawn background and dim 0.35-0.6 for contrast.
- Astronomy, abstract explainers and kids' animation stay on drawn backgrounds (space, grid, sunburst, paper).
- If the channel says footage is off, use drawn backgrounds only.

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
        "footage": {"type": "string", "enum": ["auto", "off"]},
        "world3d": {"type": "object", "description": "3D build world for the 3d_build format (see the guide)"},
        "scenes": {"type": "array", "items": {"type": "object", "properties": {
            "id": {"type": "string"}, "narration": {"type": "string"}, "caption": {"type": "string"},
            "background": {"type": "object"}, "camera": {"type": "object"}, "transition": {"type": "string"},
            "sfx": {"type": "array"}, "hold": {"type": "number"},
            "elements": {"type": "array", "items": {"type": "object"}},
        }, "required": ["id", "narration", "elements"]}},
    },
    "required": ["title", "description", "tags", "language", "voice", "aspect", "made_for_kids", "scenes"],
}


def _system(channel: dict | None = None, fmt: str = ""):
    return SYSTEM_TMPL.format(guide=SCENE_GUIDE, example=_example_for(channel or {}, fmt))


def write_episode(claude: Claude, idea: dict, facts: dict, channel: dict, notes: str = "") -> dict:
    fmt = idea.get("format") or (channel.get("formats") or ["space_facts"])[0]
    footage_off = str(channel.get("footage", "auto")).lower() == "off"
    prompt = (
        f"CHANNEL\n{json.dumps({k: channel.get(k) for k in ('name', 'niche', 'language', 'caption_script', 'audience', 'voice', 'mascot', 'handle', 'palette', 'notes', 'footage')}, ensure_ascii=False, indent=1)}\n\n"
        f"{format_brief(fmt)}\n\nIDEA\n{json.dumps(idea, ensure_ascii=False, indent=1)}\n\n"
        f"FACT SHEET\n{json.dumps(facts, ensure_ascii=False, indent=1)}\n\n"
        + (f"OWNER NOTES\n{notes}\n\n" if notes else "")
        + ("Stock footage is OFF for this channel: drawn backgrounds only.\n\n" if footage_off else "")
        + "Write and direct the episode now."
    )
    system = _system(channel, fmt)
    spec = claude.json_tool("writer", system, prompt, "submit_episode", "Submit the complete episode spec",
                            SCHEMA, max_tokens=32000)
    spec = _repair_loop(claude, spec, prompt, system)
    if fmt in FORMATS:
        spec.setdefault("format", fmt)
    if footage_off:
        spec["footage"] = "off"
    else:
        need = footage_shortfall(spec, channel)
        if need:
            fix = ("This is a real-world topic, but these scenes still use drawn backgrounds: " + ", ".join(need) +
                   ". Give each of them a background of type \"footage\" with a concrete 2-4 word English query of what a "
                   "camera would see for that moment (e.g. 'ancient temple fire ritual', 'eagle flying sky', 'royal palace "
                   "courtyard'), vary the queries, keep a drawn fallback and dim 0.35-0.6, and keep every element on top. "
                   "Replace emoji-only scenes with footage plus one or two drawn labels. Keep everything else unchanged and "
                   "resubmit the complete spec.")
            history = [{"role": "user", "content": prompt},
                       {"role": "assistant", "content": [{"type": "text", "text": json.dumps(spec, ensure_ascii=False)}]}]
            spec = _repair_loop(claude, claude.json_tool("writer", system, fix, "submit_episode",
                                                         "Submit the complete episode spec", SCHEMA,
                                                         max_tokens=32000, history=history), prompt, system)
    return spec


DRAWN_NICHES = {"space", "science", "kids", "astronomy"}


def footage_shortfall(spec: dict, channel: dict | None, min_share: float = 0.6) -> list[str]:
    """Scene ids that should carry footage but do not. Empty when the topic is drawn by nature or coverage is fine."""
    ch = channel or {}
    if str(ch.get("footage", "auto")).lower() == "off" or spec.get("footage") == "off" or spec.get("made_for_kids"):
        return []
    if spec.get("world3d"):            # 3D build videos draw their own world
        return []
    niche = str(ch.get("niche", "")).lower()
    if not niche or niche in DRAWN_NICHES:
        return []
    scenes = spec.get("scenes") or []
    if len(scenes) < 3:
        return []
    with_footage = [sc for sc in scenes if (sc.get("background") or {}).get("type") == "footage"]
    if len(with_footage) >= min_share * len(scenes):
        return []
    return [str(sc.get("id") or f"scene {i + 1}") for i, sc in enumerate(scenes)
            if (sc.get("background") or {}).get("type") != "footage"]


def revise(claude: Claude, spec: dict, instructions: str, facts: dict | None = None, channel: dict | None = None) -> dict:
    prompt = (
        f"Here is the current episode spec:\n{json.dumps(spec, ensure_ascii=False)}\n\n"
        + (f"Fact sheet:\n{json.dumps(facts, ensure_ascii=False)}\n\n" if facts else "")
        + f"Revise it. Keep everything that works; change what this asks for:\n{instructions}\n\n"
          "Return the complete revised spec via submit_episode."
    )
    system = _system(channel or {"language": spec.get("language"), "audience": "kids" if spec.get("made_for_kids") else "general"},
                     spec.get("format", ""))
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
