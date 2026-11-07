"""Live end-to-end test: real trends -> Claude scout -> Claude research (web search) -> Claude writer -> stills ->
Claude QA (vision) -> auto-fix -> full render. Needs ANTHROPIC_API_KEY (env) or a key saved in Settings.

    ANTHROPIC_API_KEY=sk-ant-... python run.py e2e --language en
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

CHANNELS = {
    "en": {"name": "Space Is Weird", "niche": "space", "language": "en", "audience": "general", "voice": "af_heart",
           "formats": ["space_facts", "facts_list"], "handle": "@vidforge.cosmos",
           "mascot": "robot id=bolt, colour #8fa3b8, small, bottom-left in hook and outro, talking=true",
           "palette": "deep purple space, gold #ffd400 headlines, purple #7c3aed pills",
           "notes": "International English audience. Bingeable series: badge 'SPACE IS WEIRD · #N' in scene 1, end with a "
                    "teaser for the next episode. Units: km first, miles in brackets.",
           "captions": {"uppercase": True}},
    "hi": {"name": "Aasmaan Ki Baatein", "niche": "space", "language": "hi", "audience": "general", "voice": "hm_omega",
           "formats": ["space_facts", "festival", "facts_list"], "handle": "@vidforge.space",
           "mascot": "astronaut id=mascot, talking=true", "notes": "Hindi for Indian viewers, IST times."},
}
CHANNELS["hinglish"] = {**CHANNELS["hi"], "language": "hinglish"}


def _step(name):
    print(f"\n== {name}", flush=True)
    return time.time()


def run_e2e(niche="space", language="en", topic="", fmt="space_facts", writer_model=""):
    db.init()
    key = db.get_setting("anthropic_api_key", "")
    if not key:
        raise SystemExit("Set ANTHROPIC_API_KEY or save the key in Settings first.")
    roles = dict(db.get_setting("models", {}) or {})
    if writer_model:
        roles["writer"] = writer_model
    c = Claude(key, roles)
    ch = {**CHANNELS.get(language, CHANNELS["en"]), "niche": niche}
    out = os.path.join(db.DATA, "out", "e2e_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out, exist_ok=True)
    save = lambda name, obj: json.dump(obj, open(os.path.join(out, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    t_all = time.time()
    print(f"Models: {c.roles}\nOutput: {out}")

    if topic:
        idea = {"topic": topic, "angle": topic, "hook": "", "format": fmt, "why_now": "owner request",
                "evergreen": True, "risk": "low", "score": 0, "title": topic}
    else:
        t = _step("1/6 trends")
        signals = gather(niche, db.get_setting("youtube_api_key", ""), ["space facts", "astronomy news"])
        ok = [s for s in signals if not s.get("error")]
        print(f"   {len(ok)} signals ({len(signals) - len(ok)} feeds failed) in {time.time() - t:.1f}s")
        t = _step("2/6 scout (Claude)")
        ideas = scout(c, ch, signals, n=6)
        save("ideas.json", ideas)
        for i in ideas[:6]:
            print(f"   [{i.get('score')}] {i.get('risk'):6} {i.get('title')}")
        idea = next((i for i in ideas if i.get("risk") == "low"), ideas[0])
        print(f"   picked: {idea.get('title')}  ({time.time() - t:.1f}s)")
    save("idea.json", idea)

    t = _step("3/6 research (Claude + web search)")
    facts = research(c, idea, ch)
    save("facts.json", facts)
    print(f"   {len(facts.get('facts', []))} sourced facts, {c.usage['web_searches']} searches ({time.time() - t:.1f}s)")
    for f in facts.get("facts", [])[:5]:
        print(f"   - {f.get('claim')}  [{f.get('confidence')}] {f.get('source_url')}")

    t = _step("4/6 write + direct (Claude)")
    spec = channel_overrides(write_episode(c, idea, facts, ch), ch)
    save("spec.json", spec)
    print(f"   '{spec.get('title')}': {len(spec.get('scenes', []))} scenes, lint: {spec.get('_lint') or 'clean'} ({time.time() - t:.1f}s)")

    t = _step("5/6 stills + QA (Claude vision)")
    stills = render_episode(spec, out, stills_only=True)["stills"]
    rv = review(c, spec, stills, facts)
    save("qa.json", rv)
    print(f"   QA {rv.get('score')}/10 pass={rv.get('pass')}  hook={rv.get('hook_score')}")
    for i in rv.get("issues", [])[:6]:
        print(f"   - [{i['severity']}] {i['scene']}: {i['problem']}")
    fix = issues_to_instructions(rv)
    if not rv.get("pass") and fix:
        print("   auto-fixing...")
        spec = channel_overrides(revise(c, spec, fix, facts, ch), ch)
        save("spec.json", spec)
        stills = render_episode(spec, out, stills_only=True)["stills"]
        rv = review(c, spec, stills, facts)
        save("qa_after_fix.json", rv)
        print(f"   QA after fix {rv.get('score')}/10 pass={rv.get('pass')} ({time.time() - t:.1f}s)")

    t = _step("6/6 render (free, CPU)")
    res = render_episode(spec, out, progress=lambda s, f: print(f"\r   {s:<8} {f * 100:5.1f}%", end="", flush=True))
    print(f"\n   {res['video']}  {res['duration']}s  rendered in {time.time() - t:.0f}s")

    u = c.usage
    pin, pout = PRICES.get(c.roles["writer"], (4, 20))
    usd = u["input_tokens"] / 1e6 * pin + u["output_tokens"] / 1e6 * pout + u["web_searches"] * 0.01
    summary = {"video": res["video"], "title": spec.get("title"), "qa_score": rv.get("score"), "qa_pass": rv.get("pass"),
               "input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"], "web_searches": u["web_searches"],
               "approx_usd_upper_bound": round(usd, 3), "total_seconds": round(time.time() - t_all)}
    save("summary.json", summary)
    print("\n== done\n" + json.dumps(summary, ensure_ascii=False, indent=1))
    return summary
