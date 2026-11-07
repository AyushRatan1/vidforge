"""Researcher: web-searches the idea and returns a sourced fact sheet the writer must stick to."""
from __future__ import annotations

import datetime as dt
import json

from .llm import WEB_SEARCH, Claude

SYSTEM = """You are the fact-checker for a science/news/story video channel for Indian audiences.
Search the web and build a short fact sheet for the idea. Every claim must come from a source you actually read
in this session; prefer primary sources (ISRO, NASA, IMD, RBI, PIB, official sites, peer-reviewed or major
newspapers). Convert times to IST. Note anything disputed, approximate or 'no earlier than'.
For stories, myths and folk tales, record which version you are following and its source; do not invent
scripture quotes. When finished, call submit_facts. Keep it to what a 60-second video needs."""

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string", "description": "3-4 sentences, plain language"},
        "facts": {"type": "array", "items": {"type": "object", "properties": {
            "claim": {"type": "string"},
            "source_title": {"type": "string"},
            "source_url": {"type": "string"},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        }, "required": ["claim", "source_url", "confidence"]}},
        "key_numbers": {"type": "array", "items": {"type": "string"}},
        "dates_ist": {"type": "array", "items": {"type": "string"}},
        "avoid": {"type": "array", "items": {"type": "string"}, "description": "claims that are wrong, myths, or unverified"},
        "visual_ideas": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "facts", "avoid"],
}


def research(claude: Claude, idea: dict, channel: dict) -> dict:
    prompt = (f"Today is {dt.date.today().isoformat()}.\nChannel: {channel.get('name')} ({channel.get('niche')}, "
              f"language {channel.get('language')}).\nIdea:\n{json.dumps(idea, ensure_ascii=False, indent=1)}")
    return claude.json_tool("research", SYSTEM, prompt, "submit_facts", "Submit the sourced fact sheet",
                            SCHEMA, max_tokens=12000, extra_tools=[WEB_SEARCH])
