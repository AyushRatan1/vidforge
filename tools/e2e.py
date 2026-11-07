"""End-to-end flow, runnable all at once or one stage at a time (GitHub Actions runs it stage by stage so the
web UI can show live progress).

    ANTHROPIC_API_KEY=sk-ant-... python run.py e2e --language en                       # everything
    python run.py e2e --stage scout --out data/out/x --language en --niche space       # one stage

Stages: scout -> research -> write -> qa -> render. State lives in the --out folder as JSON files.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time

from agents.llm import Claude
from agents.qa import issues_to_instructions, review
from agents.research import research
from agents.scout import scout
from agents.writer import revise, write_episode
from app import db
from app.jobs import PRICES, channel_overrides
from engine.pipeline import render_episode
from trends.sources import gather

STAGES = ["scout", "research", "write", "qa", "render"]

CHANNELS = {
    "en": {"name": "Space Is Weird", "language": "en", "audience": "general", "voice": "af_heart",
           "formats": ["space_facts", "facts_list"], "handle": "@vidforge.cosmos",
           "mascot": "robot id=bolt, colour #8fa3b8, small, bottom-left in hook and outro, talking=true",
           "palette": "deep purple space, gold #ffd400 headlines, purple #7c3aed pills",
           "notes": "International English audience. Bingeable series: a small series badge in scene 1, end with a "
                    "teaser for the next episode. Units: km first, miles in brackets.",
           "captions": {"uppercase": True}},
    "hi": {"name": "Aasmaan Ki Baatein", "language": "hi", "audience": "general", "voice": "hm_omega",
           "formats": ["space_facts", "festival", "facts_list"], "handle": "@vidforge.space",
           "mascot": "astronaut id=mascot, talking=true", "notes": "Hindi for Indian viewers, IST times."},
}
CHANNELS["hinglish"] = {**CHANNELS["hi"], "language": "hinglish"}

NICHE_FORMATS = {
    "space": ["space_facts", "facts_list", "quiz"],
    "science": ["space_facts", "facts_list", "quiz"],
    "tech": ["trend_explainer", "facts_list"],
    "news": ["trend_explainer"],
    "sports": ["trend_explainer", "facts_list", "quiz"],
    "general": ["trend_explainer", "facts_list", "quiz"],
    "stories": ["story"],
    "mythology": ["story", "festival"],
    "kids": ["kids_learning", "kids_story"],
}


def build_channel(language: str, niche: str, fmt: str = "auto") -> dict:
    ch = json.loads(json.dumps(CHANNELS.get(language, CHANNELS["en"])))
    ch["niche"] = niche
    if niche != "space":
        ch["name"] = {"en": "VidForge Explains", "hi": "VidForge Hindi", "hinglish": "VidForge Hindi"}[language]
        ch["notes"] = ("International English audience. " if language == "en" else "Indian viewers, IST times. ") + \
                      "End with a teaser for the next video."
        ch["mascot"] = "robot id=bolt, colour #8fa3b8, small, talking=true"
    if niche == "kids":
        ch.update({"name": "VidForge Kids", "audience": "kids", "voice": "hf_alpha" if language != "en" else "af_bella",
                   "handle": "@vidforge.kids", "mascot": "elephant id=gappu, colour #9fb3c8, talking=true",
                   "captions": {"uppercase": False},
                   "notes": "Toddlers and pre-schoolers. Gentle, slow, repetitive, bright. Original content only."})
    formats = list(NICHE_FORMATS.get(niche, ch["formats"]))
    if fmt and fmt != "auto":
        formats = [fmt] + [f for f in formats if f != fmt]
    ch["formats"] = formats
    return ch


def _client(writer_model: str = "") -> Claude:
    db.init()
    key = db.get_setting("anthropic_api_key", "")
    if not key:
        raise SystemExit("Set ANTHROPIC_API_KEY (or save the key in the dashboard Settings) first.")
    roles = dict(db.get_setting("models", {}) or {})
    if writer_model:
        roles["writer"] = writer_model
    return Claude(key, roles)


def _load(out, name, default=None):
    p = os.path.join(out, name)
    if not os.path.exists(p):
        if default is not None:
            return default
        raise SystemExit(f"{name} missing in {out}; run the earlier stage first")
    return json.load(open(p, encoding="utf-8"))


def _save(out, name, obj):
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def _add_usage(out, c: Claude):
    u = _load(out, "usage.json", {"input_tokens": 0, "output_tokens": 0, "web_searches": 0, "writer": c.roles["writer"]})
    for k in ("input_tokens", "output_tokens", "web_searches"):
        u[k] = u.get(k, 0) + c.usage.get(k, 0)
    u["writer"] = c.roles["writer"]
    _save(out, "usage.json", u)
    c.usage = {"input_tokens": 0, "output_tokens": 0, "web_searches": 0}


# ------------------------------------------------------------------ stages
def stage_scout(out, ch, topic="", fmt="auto", writer=""):
    if topic:
        idea = {"topic": topic, "angle": topic, "hook": "", "format": ch["formats"][0], "why_now": "requested",
                "evergreen": True, "risk": "low", "score": 0, "title": topic}
        print(f"   using your topic: {topic}")
    else:
        c = _client(writer)
        seeds = {"space": ["space facts", "astronomy news"], "kids": ["kids learning"], "stories": ["story"],
                 "mythology": ["mythology stories"]}.get(ch["niche"], [])
        signals = gather(ch["niche"], db.get_setting("youtube_api_key", ""), seeds)
        ok = [s for s in signals if not s.get("error")]
        print(f"   {len(ok)} trend signals ({len(signals) - len(ok)} feeds unavailable)")
        ideas = scout(c, ch, signals, n=6)
        _save(out, "ideas.json", ideas)
        for i in ideas:
            print(f"   [{i.get('score')}] {i.get('risk'):6} {i.get('title')}")
        idea = next((i for i in ideas if i.get("risk") == "low"), ideas[0])
        _add_usage(out, c)
    _save(out, "idea.json", idea)
    print(f"   picked: {idea.get('title')}")


def stage_research(out, ch, writer=""):
    c = _client(writer)
    facts = research(c, _load(out, "idea.json"), ch)
    _save(out, "facts.json", facts)
    print(f"   {len(facts.get('facts', []))} sourced facts, {c.usage['web_searches']} web searches")
    for f in facts.get("facts", [])[:6]:
        print(f"   - {f.get('claim')} [{f.get('confidence')}] {f.get('source_url')}")
    _add_usage(out, c)


def stage_write(out, ch, writer=""):
    c = _client(writer)
    spec = channel_overrides(write_episode(c, _load(out, "idea.json"), _load(out, "facts.json"), ch), ch)
    _save(out, "spec.json", spec)
    print(f"   '{spec.get('title')}': {len(spec.get('scenes', []))} scenes, lint: {spec.get('_lint') or 'clean'}")
    _add_usage(out, c)


def stage_qa(out, ch, writer=""):
    c = _client(writer)
    spec, facts = _load(out, "spec.json"), _load(out, "facts.json")
    stills = render_episode(spec, out, stills_only=True)["stills"]
    rv = review(c, spec, stills, facts)
    print(f"   QA {rv.get('score')}/10 pass={rv.get('pass')}")
    for i in rv.get("issues", [])[:6]:
        print(f"   - [{i['severity']}] {i['scene']}: {i['problem']}")
    fix = issues_to_instructions(rv)
    if not rv.get("pass") and fix:
        print("   fixing and re-checking...")
        _save(out, "qa_first.json", rv)
        spec = channel_overrides(revise(c, spec, fix, facts, ch), ch)
        _save(out, "spec.json", spec)
        stills = render_episode(spec, out, stills_only=True)["stills"]
        rv = review(c, spec, stills, facts)
        print(f"   QA after fix {rv.get('score')}/10 pass={rv.get('pass')}")
    _save(out, "qa.json", rv)
    _add_usage(out, c)


def stage_render(out, ch, **_):
    spec = _load(out, "spec.json")
    t = time.time()
    res = render_episode(spec, out, progress=lambda s, f: None)
    print(f"   {res['video']} {res['duration']}s, rendered in {time.time() - t:.0f}s")
    u = _load(out, "usage.json", {"input_tokens": 0, "output_tokens": 0, "web_searches": 0, "writer": "claude-opus-5-5"})
    pin, pout = PRICES.get(u.get("writer"), (4, 20))
    qa = _load(out, "qa.json", {})
    summary = {
        "id": os.path.basename(os.path.normpath(out)), "title": spec.get("title"), "description": spec.get("description"),
        "tags": spec.get("tags"), "language": spec.get("language"), "made_for_kids": spec.get("made_for_kids"),
        "aspect": spec.get("aspect", "9:16"), "duration": res["duration"], "scenes": res["scenes"],
        "qa_score": qa.get("score"), "qa_pass": qa.get("pass"), "render_seconds": res["render_seconds"],
        "input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"], "web_searches": u["web_searches"],
        "usd": round(u["input_tokens"] / 1e6 * pin + u["output_tokens"] / 1e6 * pout + u["web_searches"] * 0.01, 3),
        "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    _save(out, "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return summary


RUNNERS = {"scout": stage_scout, "research": stage_research, "write": stage_write, "qa": stage_qa, "render": stage_render}


def run_e2e(niche="space", language="en", topic="", fmt="auto", writer_model="", stage="all", out=""):
    ch = build_channel(language, niche, fmt)
    out = out or os.path.join(db.DATA, "out", "e2e_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out, exist_ok=True)
    stages = STAGES if stage == "all" else [stage]
    result = None
    for s in stages:
        t = time.time()
        print(f"\n== {s}", flush=True)
        kw = {"writer": writer_model}
        if s == "scout":
            kw.update(topic=topic, fmt=fmt)
        result = RUNNERS[s](out, ch, **kw)
        print(f"   ({time.time() - t:.0f}s)", flush=True)
    return result
