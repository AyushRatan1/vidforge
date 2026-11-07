"""Trend scout: turns raw India trend signals into ranked, safe video ideas for one channel."""
from __future__ import annotations

import datetime as dt
import json

from .formats import FORMATS
from .llm import Claude

SYSTEM = """You are the trend scout for a faceless YouTube Shorts / Instagram Reels channel aimed at Indian audiences.
You get raw trend signals (Google Trends India, Google News India, YouTube India trending, niche searches) and the
channel's profile. Pick the ideas most likely to win views FOR THIS CHANNEL in the next 7 days.

Rules:
- Stay inside the channel's niche and allowed formats. A trend outside the niche is only usable if there is a
  genuine angle inside the niche (e.g. a cricket final -> 'the physics of a swing ball' for a science channel).
- Prefer: dated events coming up (sky events, launches, festivals, exams, big matches), evergreen curiosity with a
  timely hook, and topics Indian viewers are actively searching in Hindi.
- Avoid or mark high risk: tragedies and disasters in progress, active political or communal controversy,
  celebrity rumours, medical or financial advice, anything about real private people, film/TV/IPL footage, and
  existing copyrighted characters or songs. Kids formats must be gentle and educational.
- Each idea needs a specific angle and a hook line a viewer would stop scrolling for, in the channel language.
- Be honest about uncertainty: if a date is 'no earlier than', say so in why_now.
"""

SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "angle": {"type": "string", "description": "the specific take, one sentence"},
                    "hook": {"type": "string", "description": "first spoken line, in the channel language"},
                    "format": {"type": "string", "enum": list(FORMATS)},
                    "why_now": {"type": "string", "description": "trend signal or date that makes this timely"},
                    "publish_by": {"type": "string", "description": "ISO date by which it should be live"},
                    "evergreen": {"type": "boolean"},
                    "risk": {"type": "string", "enum": ["low", "medium", "high"]},
                    "risk_note": {"type": "string"},
                    "score": {"type": "integer", "description": "1-100 expected performance for this channel"},
                    "title": {"type": "string", "description": "YouTube title, <70 chars, channel language"},
                    "sources": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["topic", "angle", "hook", "format", "why_now", "evergreen", "risk", "score", "title"],
            },
        }
    },
    "required": ["ideas"],
}


def scout(claude: Claude, channel: dict, signals: list[dict], n: int = 8, extra_notes: str = "") -> list[dict]:
    today = dt.date.today().isoformat()
    sig = [s for s in signals if not s.get("error")][:160]
    errors = [s for s in signals if s.get("error")]
    prompt = (
        f"Today is {today} (India).\n\nCHANNEL PROFILE\n{json.dumps(_profile(channel), ensure_ascii=False, indent=1)}\n\n"
        f"TREND SIGNALS ({len(sig)})\n{json.dumps(sig, ensure_ascii=False)}\n\n"
        + (f"Feeds that failed: {[e['source'] for e in errors]}\n\n" if errors else "")
        + (f"Notes from the owner: {extra_notes}\n\n" if extra_notes else "")
        + f"Return the best {n} ideas, highest score first. Include at least two evergreen ideas so the channel "
          f"never runs dry."
    )
    out = claude.json_tool("scout", SYSTEM, prompt, "submit_ideas", "Submit ranked video ideas", SCHEMA, max_tokens=12000)
    ideas = out.get("ideas", [])
    return sorted(ideas, key=lambda i: -int(i.get("score", 0)))


def _profile(ch: dict) -> dict:
    keys = ["name", "niche", "language", "caption_script", "audience", "formats", "voice", "mascot", "handle",
            "palette", "notes", "seed_queries"]
    return {k: ch.get(k) for k in keys if ch.get(k)}
