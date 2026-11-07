"""QA director: looks at rendered stills (vision) and checks the script against the fact sheet."""
from __future__ import annotations

import base64
import json

from .llm import Claude

SYSTEM = """You are the QA reviewer for an animated Shorts channel for Indian audiences. You see sampled frames
(two per scene, in order) plus the script and the fact sheet. Judge it the way a strict YouTube reviewer and a
picky viewer would. Check:
1. Readability: text cut off, overlapping other text, text in the caption band, too small, too many words.
2. Visual sense: does each frame show what the narration is about? Empty or confusing frames?
3. Facts: every claim in narration/captions is supported by the fact sheet; numbers and dates match.
4. Safety and policy: kids content is gentle and correctly flagged made_for_kids; no copyrighted characters or
   logos; nothing misleading; sensitive topics handled neutrally.
5. Retention: is the hook in the first 1.5 s strong? Is there a payoff?
Be concrete: name the scene and the element and the exact fix in spec terms (move y to 0.6, shorten text to ...).
Pass only if a viewer would not notice a problem."""

SCHEMA = {
    "type": "object",
    "properties": {
        "pass": {"type": "boolean"},
        "score": {"type": "integer", "description": "1-10 overall"},
        "hook_score": {"type": "integer"},
        "issues": {"type": "array", "items": {"type": "object", "properties": {
            "scene": {"type": "string"}, "severity": {"type": "string", "enum": ["blocker", "major", "minor"]},
            "problem": {"type": "string"}, "fix": {"type": "string"}}, "required": ["scene", "severity", "problem", "fix"]}},
        "fact_check": {"type": "string"},
        "made_for_kids_correct": {"type": "boolean"},
    },
    "required": ["pass", "score", "issues", "fact_check"],
}


def review(claude: Claude, spec: dict, stills: list[str], facts: dict | None = None) -> dict:
    content = [{"type": "text", "text": "Frames in order (scene N early, scene N later):"}]
    for p in stills[:24]:
        with open(p, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode()
        content.append({"type": "text", "text": p.rsplit("/", 1)[-1]})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}})
    slim = {k: spec.get(k) for k in ("title", "language", "made_for_kids", "aspect")}
    slim["scenes"] = [{"id": s.get("id"), "narration": s.get("narration"), "caption": s.get("caption")} for s in spec.get("scenes", [])]
    content.append({"type": "text", "text": f"SCRIPT\n{json.dumps(slim, ensure_ascii=False, indent=1)}\n\n"
                                            f"FACT SHEET\n{json.dumps(facts or {}, ensure_ascii=False, indent=1)}"})
    return claude.json_tool("qa", SYSTEM, content, "submit_review", "Submit the QA review", SCHEMA, max_tokens=8000)


def issues_to_instructions(rv: dict) -> str:
    lines = [f"- [{i['severity']}] scene {i['scene']}: {i['problem']} -> {i['fix']}" for i in rv.get("issues", [])
             if i.get("severity") in ("blocker", "major")]
    if rv.get("fact_check") and "ok" not in rv["fact_check"].lower()[:10]:
        lines.append(f"- facts: {rv['fact_check']}")
    return "\n".join(lines)
