"""Researcher: web-searches the idea and returns a sourced fact sheet the writer must stick to."""
from __future__ import annotations

import datetime as dt
import json
import re

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


URL = re.compile(r"https?://[^\s)\]>\"']+")


def normalize(sheet) -> dict:
    """Every fact becomes {claim, source_title, source_url, confidence}, whatever shape the model used."""
    sheet = sheet if isinstance(sheet, dict) else {}
    facts = []
    for f in sheet.get("facts") or []:
        if isinstance(f, str):
            f = {"claim": f}
        if not isinstance(f, dict):
            continue
        claim = str(f.get("claim") or f.get("fact") or f.get("text") or "").strip()
        url = str(f.get("source_url") or f.get("url") or f.get("source") or "").strip()
        if not url.startswith("http"):
            m = URL.search(claim) or URL.search(url)
            url = m.group(0).rstrip(".,;") if m else ""
            if m and m.group(0) in claim:
                claim = re.sub(r"[\s(\[]*(source:?\s*)?" + re.escape(m.group(0)) + r"[)\]]*", "", claim, flags=re.I).strip(" -:;,")
        if not claim:
            continue
        conf = str(f.get("confidence") or "").lower()
        facts.append({"claim": claim, "source_title": str(f.get("source_title") or f.get("title") or "").strip(),
                      "source_url": url, "confidence": conf if conf in ("high", "medium", "low") else "medium"})
    sheet["facts"] = facts
    sheet["summary"] = str(sheet.get("summary") or "")
    for k in ("key_numbers", "dates_ist", "avoid", "visual_ideas"):
        v = sheet.get(k) or []
        sheet[k] = [str(x) for x in (v if isinstance(v, list) else [v])]
    return sheet


def research(claude: Claude, idea: dict, channel: dict) -> dict:
    prompt = (f"Today is {dt.date.today().isoformat()}.\nChannel: {channel.get('name')} ({channel.get('niche')}, "
              f"language {channel.get('language')}).\nIdea:\n{json.dumps(idea, ensure_ascii=False, indent=1)}")
    return normalize(claude.json_tool("research", SYSTEM, prompt, "submit_facts", "Submit the sourced fact sheet",
                                      SCHEMA, max_tokens=12000, extra_tools=[WEB_SEARCH]))
