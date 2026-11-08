"""Release notes for the video library. Every video is a GitHub Release (tag video-<id>) whose body is readable
markdown plus a hidden JSON block that the web UI parses.

    python tools/library.py notes data/out/<id> > notes.md
"""
from __future__ import annotations

import json
import os
import sys

MARK_START = "<!-- vidforge"
MARK_END = "-->"


def _load(out, name, default=None):
    p = os.path.join(out, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def notes(out: str, options: dict | None = None) -> str:
    s = _load(out, "summary.json", {}) or {}
    meta = _load(out, "meta.json", {}) or {}
    pub = _load(out, "published.json", {}) or {}
    facts = [f for f in (_load(out, "facts.json", {}) or {}).get("facts", []) if isinstance(f, dict)]
    qa = _load(out, "qa.json", {}) or {}
    yt = meta.get("youtube", {})
    lines = [f"**{s.get('title') or yt.get('title') or s.get('id')}**", ""]
    desc = (yt.get("description") or "").split("\n\n")[0]
    if desc:
        lines += [desc, ""]
    rows = [("Length", f"{round(s['duration'])} s" if s.get("duration") else None),
            ("Language", s.get("language")), ("Format", s.get("format")),
            ("Review score", f"{s['qa_score']}/10" if s.get("qa_score") is not None else None),
            ("Claude cost", f"${s['usd']:.2f}" if s.get("usd") is not None else None)]
    rows = [r for r in rows if r[1]]
    if rows:
        lines += ["| | |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows] + [""]
    posted = []
    for k, label in (("youtube", "YouTube"), ("instagram", "Instagram")):
        p = pub.get(k) or {}
        if p.get("url"):
            posted.append(f"{label}: {p['url']}" + (f" ({p['privacy']})" if p.get("privacy") else ""))
        elif p.get("error"):
            posted.append(f"{label}: failed ({p['error'][:120]})")
    if posted:
        lines += ["Posted: " + " · ".join(posted).replace(" · ", ", "), ""]
    if facts:
        lines += ["Sources: " + ", ".join(f"[{(f.get('source_title') or 'source')[:40]}]({f.get('source_url')})"
                                         for f in facts[:5] if f.get("source_url")), ""]
    blob = {"summary": s, "meta": meta, "published": pub, "options": options or _load(out, "options.json", {}),
            "sources": [{"claim": f.get("claim"), "url": f.get("source_url"), "title": f.get("source_title"),
                         "confidence": f.get("confidence")} for f in facts[:12]],
            "qa": {"score": qa.get("score"), "pass": qa.get("pass"),
                   "issues": [i.get("problem") for i in qa.get("issues", []) if i.get("severity") != "minor"][:6]}}
    raw = json.dumps(blob, ensure_ascii=False).replace("-->", "--\\u003e")
    lines += [MARK_START, raw, MARK_END]
    return "\n".join(lines)


def parse(body: str) -> dict:
    i = body.find(MARK_START)
    if i < 0:
        return {}
    j = body.find(MARK_END, i + len(MARK_START))
    return json.loads(body[i + len(MARK_START):j].strip())


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "notes":
        opts = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
        sys.stdout.write(notes(sys.argv[2], opts))
    else:
        sys.exit("usage: python tools/library.py notes <out_dir> [options_json]")
