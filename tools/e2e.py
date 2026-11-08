"""End-to-end flow, runnable all at once or one stage at a time (GitHub Actions runs it stage by stage so the
web UI can show live progress).

    ANTHROPIC_API_KEY=sk-ant-... python run.py e2e --language en                     # everything, local
    python run.py e2e --stage write --out data/out/x --options '{"language":"en"}'   # one stage

Stages: scout -> research -> write -> qa -> render -> package (posting copy + hashtags) -> publish (optional).
Options (JSON, every value optional, custom values welcome):
  language  en | hi | hinglish | es | fr | it | pt | <any language name>
  niche     space | science | tech | stories | mythology | kids | news | sports | general | <any channel idea>
  format    auto | space_facts | trend_explainer | story | facts_list | festival | quiz | kids_learning |
            kids_story | <describe your own format>
  topic, notes (extra instructions), writer (model id), voice (Kokoro voice id), music (mood), aspect (9:16|16:9|1:1),
  length (seconds), hashtags (list or space-separated string), handle, publish {youtube, instagram, privacy, publish_at}
  job_id    Supabase jobs.id to keep updated while the stages run (set by the web UI or autopilot)
  source    "manual" (default) | "autopilot": recorded on the videos row

When SUPABASE_URL and SUPABASE_SERVICE_KEY are set, settings are loaded from the settings table first and the
videos/jobs rows are kept current; without them every store call is a no-op.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time

from agents.formats import FORMATS
from agents.llm import Claude
from agents.metadata import fallback_metadata, write_metadata
from agents.qa import issues_to_instructions, review
from agents.research import research
from agents.scout import scout
from agents.writer import revise, write_episode
from app import db
from app.jobs import PRICES, channel_overrides
from engine.audio import DEFAULT_VOICE
from engine.pipeline import render_episode
from tools import store
from trends.sources import NICHE_SOURCES, gather

STAGES = ["scout", "research", "write", "qa", "render", "package", "publish"]
STAGE_LABELS = {"scout": "Find trend", "research": "Research", "write": "Write and direct", "qa": "Review frames",
                "render": "Render video", "package": "Write captions and hashtags", "publish": "Post"}

BRAND = {"space": "#SpaceIsWeird", "kids": "#VidForgeKids"}

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


def parse_options(raw) -> dict:
    o = raw if isinstance(raw, dict) else json.loads(raw or "{}")
    o = {k: (v.strip() if isinstance(v, str) else v) for k, v in o.items()}
    tags = o.get("hashtags") or []
    if isinstance(tags, str):
        tags = [t for t in tags.replace(",", " ").split() if t]
    o["hashtags"] = tags
    o.setdefault("language", "en")
    o.setdefault("niche", "space")
    o.setdefault("format", "auto")
    o["publish"] = o.get("publish") or {}
    o["source"] = o.get("source") or "manual"
    o["job_id"] = str(o["job_id"]) if o.get("job_id") else ""
    return o


def build_channel(o: dict) -> dict:
    lang, niche, fmt = o["language"], o["niche"], o["format"]
    base_lang = lang if lang in CHANNELS else ("hi" if lang == "hinglish" else "en")
    ch = json.loads(json.dumps(CHANNELS[base_lang]))
    ch["language"] = lang
    custom_niche = niche not in NICHE_SOURCES
    ch["niche"] = "general" if custom_niche else niche
    if niche != "space":
        ch["name"] = "VidForge" + ("" if lang == "en" else f" ({lang})")
        ch["notes"] = ("International audience. " if lang not in ("hi", "hinglish") else "Indian viewers, IST times. ") + \
                      "End with a teaser for the next video."
        ch["mascot"] = "robot id=bolt, colour #8fa3b8, small, talking=true"
        ch["captions"] = {"uppercase": lang == "en"}
    if custom_niche:
        ch["notes"] += f" Channel focus (set by the owner): {niche}."
        ch["seed_queries"] = [niche]
    if niche == "kids":
        ch.update({"name": "VidForge Kids", "audience": "kids", "handle": "@vidforge.kids",
                   "mascot": "elephant id=gappu, colour #9fb3c8, talking=true", "captions": {"uppercase": False},
                   "notes": "Toddlers and pre-schoolers. Gentle, slow, repetitive, bright. Original content only."})
    ch["voice"] = o.get("voice") or (("hf_alpha" if lang in ("hi", "hinglish") else "af_bella") if niche == "kids"
                                     else DEFAULT_VOICE.get(lang, ch["voice"]))
    formats = list(NICHE_FORMATS.get(niche, ["trend_explainer", "facts_list"]))
    if fmt and fmt != "auto":
        formats = [fmt] + [f for f in formats if f != fmt]
    ch["formats"] = formats
    if o.get("handle"):
        ch["handle"] = o["handle"]
    ch["brand_hashtags"] = [BRAND[niche]] if niche in BRAND else []
    if o.get("music"):
        ch["music_mood"] = o["music"]
    notes = []
    if o.get("length"):
        notes.append(f"Target length about {o['length']} seconds.")
    if o.get("aspect") and o["aspect"] != "9:16":
        notes.append(f"Aspect {o['aspect']} (long-form layout: wider compositions, more scenes).")
    if o.get("notes"):
        notes.append(o["notes"])
    ch["owner_notes"] = " ".join(notes)
    return ch


def _client(writer_model: str = "") -> Claude:
    db.init()
    key = db.get_setting("anthropic_api_key", "")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is not set. Add it as a repo secret (Actions) or env var.")
    roles = dict(db.get_setting("models", {}) or {})
    if not roles and os.environ.get("VF_MODELS"):      # Supabase settings.models, loaded by store.load_settings_into_env
        try:
            roles = dict(json.loads(os.environ["VF_MODELS"]) or {})
        except ValueError:
            roles = {}
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


def _finish_spec(spec: dict, o: dict, ch: dict) -> dict:
    spec = channel_overrides(spec, ch)
    if o.get("aspect"):
        spec["aspect"] = o["aspect"]
    if o.get("music"):
        spec.setdefault("music", {})["mood"] = o["music"]
    if o.get("voice"):
        spec["voice"] = o["voice"]
    return spec


# ------------------------------------------------------------------ stages
def stage_scout(out, o, ch):
    fmt = o["format"]
    if o.get("topic"):
        idea = {"topic": o["topic"], "angle": o["topic"], "hook": "", "format": ch["formats"][0], "why_now": "requested",
                "evergreen": True, "risk": "low", "score": 0, "title": o["topic"]}
        print(f"   using your topic: {o['topic']}")
    else:
        c = _client(o.get("writer"))
        signals = gather(ch["niche"], db.get_setting("youtube_api_key", ""), ch.get("seed_queries"))
        ok = [s for s in signals if not s.get("error")]
        print(f"   {len(ok)} trend signals ({len(signals) - len(ok)} feeds unavailable)")
        ideas = scout(c, ch, signals, n=6, extra_notes=ch.get("owner_notes", ""))
        _save(out, "ideas.json", ideas)
        for i in ideas:
            print(f"   [{i.get('score')}] {i.get('risk'):6} {i.get('title')}")
        idea = next((i for i in ideas if i.get("risk") == "low"), ideas[0])
        _add_usage(out, c)
    if fmt and fmt != "auto" and fmt not in FORMATS:
        idea["format"] = fmt                      # owner's own format description
    elif fmt in FORMATS:
        idea["format"] = fmt
    _save(out, "idea.json", idea)
    print(f"   picked: {idea.get('title')} [{idea.get('format')}]")


def stage_research(out, o, ch):
    c = _client(o.get("writer"))
    facts = research(c, _load(out, "idea.json"), ch)
    _save(out, "facts.json", facts)
    print(f"   {len(facts.get('facts', []))} sourced facts, {c.usage['web_searches']} web searches")
    for f in facts.get("facts", [])[:6]:
        print(f"   - {f['claim'][:140]} [{f['confidence']}] {f['source_url'] or 'no link'}")
    _add_usage(out, c)


def stage_write(out, o, ch):
    c = _client(o.get("writer"))
    spec = write_episode(c, _load(out, "idea.json"), _load(out, "facts.json"), ch, ch.get("owner_notes", ""))
    spec = _finish_spec(spec, o, ch)
    _save(out, "spec.json", spec)
    print(f"   '{spec.get('title')}': {len(spec.get('scenes', []))} scenes, lint: {spec.get('_lint') or 'clean'}")
    _add_usage(out, c)


def stage_qa(out, o, ch):
    c = _client(o.get("writer"))
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
        spec = _finish_spec(revise(c, spec, fix, facts, ch), o, ch)
        _save(out, "spec.json", spec)
        stills = render_episode(spec, out, stills_only=True)["stills"]
        rv = review(c, spec, stills, facts)
        print(f"   QA after fix {rv.get('score')}/10 pass={rv.get('pass')}")
    _save(out, "qa.json", rv)
    _add_usage(out, c)


def stage_render(out, o, ch):
    spec = _load(out, "spec.json")
    t = time.time()
    res = render_episode(spec, out, progress=lambda s, f: None)
    print(f"   {res['video']} {res['duration']}s, rendered in {time.time() - t:.0f}s on {os.cpu_count()} cores")
    _save(out, "render.json", res)


def stage_package(out, o, ch):
    spec, facts = _load(out, "spec.json"), _load(out, "facts.json", {})
    try:
        c = _client(o.get("writer"))
        meta = write_metadata(c, spec, facts, ch, o.get("hashtags"))
        _add_usage(out, c)
    except SystemExit:
        meta = fallback_metadata(spec, ch.get("brand_hashtags"), o.get("hashtags"))
    _save(out, "meta.json", meta)
    print(f"   YouTube: {meta['youtube']['title']}  {' '.join(meta['youtube']['hashtags'])}")
    print(f"   Instagram: {' '.join(meta['instagram']['hashtags'])}")
    res = _load(out, "render.json", {})
    u = _load(out, "usage.json", {"input_tokens": 0, "output_tokens": 0, "web_searches": 0, "writer": "claude-opus-5-5"})
    pin, pout = PRICES.get(u.get("writer"), (4, 20))
    qa = _load(out, "qa.json", {})
    idea = _load(out, "idea.json", {})
    summary = {
        "id": os.path.basename(os.path.normpath(out)), "title": meta["youtube"]["title"] or spec.get("title"),
        "topic": idea.get("topic"), "format": idea.get("format"), "language": spec.get("language"),
        "niche": o.get("niche"), "made_for_kids": spec.get("made_for_kids"), "aspect": spec.get("aspect", "9:16"),
        "duration": res.get("duration"), "scenes": res.get("scenes"), "qa_score": qa.get("score"),
        "qa_pass": qa.get("pass"), "render_seconds": res.get("render_seconds"),
        "input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"], "web_searches": u["web_searches"],
        "usd": round(u["input_tokens"] / 1e6 * pin + u["output_tokens"] / 1e6 * pout + u["web_searches"] * 0.01, 3),
        "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    _save(out, "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=1))


def stage_publish(out, o, ch):
    from tools.publish import publish
    p = o.get("publish") or {}
    if not (p.get("youtube") or p.get("instagram")):
        print("   not publishing (no platform selected)")
        return
    publish(out, youtube=bool(p.get("youtube")), instagram=bool(p.get("instagram")),
            privacy=p.get("privacy", "public"), publish_at=p.get("publish_at") or None)


RUNNERS = {"scout": stage_scout, "research": stage_research, "write": stage_write, "qa": stage_qa,
           "render": stage_render, "package": stage_package, "publish": stage_publish}


# ------------------------------------------------------------------ Supabase bookkeeping (no-ops when not configured)
def _track(fn, *args, **kw):
    """Run a store call without ever failing the video over bookkeeping."""
    if not store.enabled():
        return None
    try:
        return fn(*args, **kw)
    except Exception as e:
        print(f"   (store: {e})", flush=True)
        return None


def track_stage_start(out: str, stage: str, o: dict) -> None:
    rid = os.path.basename(os.path.normpath(out))
    label = STAGE_LABELS.get(stage, stage)
    run_id = os.environ.get("GITHUB_RUN_ID")
    fields = {"status": "making", "stage": label, "options": o, "source": o.get("source") or "manual"}
    if run_id:
        fields["run_id"] = run_id
    if o.get("topic"):
        fields["topic"] = o["topic"]
    fields.update({k: o[k] for k in ("language", "niche") if o.get(k)})
    _track(store.video_upsert, rid, **fields)
    _track(store.job_update, o.get("job_id"), status="running", stage=label, video_id=rid, run_id=run_id,
           run_url=store.run_url())


def track_stage_end(out: str, stage: str, o: dict) -> None:
    rid = os.path.basename(os.path.normpath(out))
    if stage == "package":
        row = store.video_from_folder(out, rid, o)
        row.update({"status": "ready", "stage": "Saved to library", "source": o.get("source") or "manual",
                    **store.release_urls(rid)})
        _track(store.upsert, "videos", row)
        if (o.get("source") or "") == "autopilot":
            from tools import autopilot
            _track(autopilot.mark_topic, rid, "done")
    # publish: tools.publish.publish() mirrors published.json into the row itself (also on partial failure)


def run_e2e(niche="", language="", topic="", fmt="", writer_model="", stage="all", out="", options=None):
    _track(store.load_settings_into_env)
    o = parse_options(options or "{}")
    for k, v in (("niche", niche), ("language", language), ("topic", topic), ("format", fmt), ("writer", writer_model)):
        if v:
            o[k] = v
    ch = build_channel(o)
    out = out or os.path.join(db.DATA, "out", "e2e_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out, exist_ok=True)
    stages = STAGES if stage == "all" else [stage]
    for s in stages:
        t = time.time()
        print(f"\n== {s}", flush=True)
        track_stage_start(out, s, o)
        RUNNERS[s](out, o, ch)
        track_stage_end(out, s, o)
        print(f"   ({time.time() - t:.0f}s)", flush=True)
    return out
