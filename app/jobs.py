"""Job orchestration: research -> write -> stills -> QA (auto-fix once) -> render -> review -> publish."""
from __future__ import annotations

import copy
import datetime as dt
import os
import traceback
from concurrent.futures import ThreadPoolExecutor

from agents.llm import Claude
from agents.qa import issues_to_instructions, review
from agents.research import research
from agents.scout import scout
from agents.writer import revise, write_episode
from engine.pipeline import render_episode
from engine.validate import validate
from publish import instagram, youtube
from trends.sources import gather

from . import db

OUT = os.path.join(db.DATA, "out")
PRICES = {  # USD per million tokens (input, output)
    "claude-fable-5-1": (10, 50), "claude-opus-5-5": (4, 20), "claude-sonnet-5-5": (2, 10), "claude-haiku-5-5": (0.1, 0.5),
}

_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="render")   # renders are CPU bound: one at a time
_agents = ThreadPoolExecutor(max_workers=3, thread_name_prefix="agent")


def claude() -> Claude:
    return Claude(db.get_setting("anthropic_api_key", ""), db.get_setting("models", {}) or {})


def _usage(c: Claude, data: dict) -> dict:
    u = data.get("usage", {"input_tokens": 0, "output_tokens": 0, "web_searches": 0, "usd": 0.0})
    for k in ("input_tokens", "output_tokens", "web_searches"):
        u[k] = u.get(k, 0) + c.usage.get(k, 0)
    # rough cost: attribute everything to the writer model's price (upper bound when writer is the priciest)
    pin, pout = PRICES.get(c.roles["writer"], (4, 20))
    u["usd"] = round(u["input_tokens"] / 1e6 * pin + u["output_tokens"] / 1e6 * pout + u["web_searches"] * 0.01, 3)
    c.usage = {"input_tokens": 0, "output_tokens": 0, "web_searches": 0}
    return u


def channel_overrides(spec: dict, ch: dict) -> dict:
    """The channel owns branding and audience flags; never trust the model for these."""
    spec = copy.deepcopy(spec)
    if ch.get("handle"):
        spec.setdefault("overlay", {})["handle"] = ch["handle"]
    if ch.get("voice"):
        spec["voice"] = ch["voice"]
    if ch.get("audience") == "kids":
        spec["made_for_kids"] = True
    if ch.get("captions"):
        spec["captions"] = {**(spec.get("captions") or {}), **ch["captions"]}
    if ch.get("music_file"):
        spec.setdefault("music", {})["file"] = ch["music_file"]
    if "ai-assisted" not in (spec.get("description") or "").lower():
        spec["description"] = (spec.get("description") or "").rstrip() + "\n\nVisuals and voice are AI-assisted."
    return spec


# ---------------------------------------------------------------- scouting
def run_scout(cid: str, notes: str = "", n: int = 8) -> list[dict]:
    ch = db.channel(cid)
    signals = gather(ch.get("niche", "general"), db.get_setting("youtube_api_key", ""), ch.get("seed_queries"),
                     db.get_setting("nasa_api_key", ""))
    c = claude()
    ideas = scout(c, ch, signals, n=n, extra_notes=notes)
    return db.add_ideas(cid, ideas)


# ---------------------------------------------------------------- making videos
def start_job(cid: str, idea: dict | None = None, topic: str = "", notes: str = "", spec: dict | None = None) -> str:
    ch = db.channel(cid)
    if idea is None:
        fmt = (ch.get("formats") or ["space_facts"])[0]
        idea = {"topic": topic, "angle": topic, "hook": "", "format": fmt, "why_now": "requested by owner",
                "evergreen": True, "risk": "low", "score": 0, "title": topic}
    jid = db.new_job(cid, idea.get("id"), {"idea": idea, "notes": notes, **({"spec": spec} if spec else {})})
    if idea.get("id"):
        db.set_idea_status(idea["id"], "in_production")
    _pool.submit(_safe, make_video, jid)
    return jid


def _safe(fn, jid, *a):
    try:
        fn(jid, *a)
    except Exception as e:
        traceback.print_exc()
        db.update_job(jid, status="failed", error=f"{type(e).__name__}: {e}")


def _progress(jid, stage, base, span):
    def cb(s, frac):
        db.update_job(jid, stage=f"{stage}:{s}", progress=round(base + span * frac, 3))
    return cb


def make_video(jid: str):
    j = db.job(jid)
    data = j["data"]
    ch = db.channel(j["channel_id"])
    out_dir = os.path.join(OUT, jid)
    spec = data.get("spec")
    c = None
    if not spec:
        c = claude()
        db.update_job(jid, status="running", stage="research", progress=0.05)
        facts = research(c, data["idea"], ch)
        db.update_job(jid, data={"facts": facts, "usage": _usage(c, data)})
        data = db.job(jid)["data"]
        db.update_job(jid, stage="writing", progress=0.15)
        spec = write_episode(c, data["idea"], facts, ch, data.get("notes", ""))
        spec = channel_overrides(spec, ch)
        db.update_job(jid, data={"spec": spec, "usage": _usage(c, data)})
        data = db.job(jid)["data"]
    else:
        spec = channel_overrides(spec, ch)
        db.update_job(jid, data={"spec": spec})

    # QA on stills before paying for the full render
    if db.get_setting("qa_enabled", True) and db.get_setting("anthropic_api_key", ""):
        c = c or claude()
        db.update_job(jid, status="running", stage="qa", progress=0.25)
        stills = render_episode(spec, out_dir, stills_only=True)["stills"]
        rv = review(c, spec, stills, data.get("facts"))
        db.update_job(jid, data={"qa": rv, "usage": _usage(c, data)})
        data = db.job(jid)["data"]
        fix = issues_to_instructions(rv)
        if not rv.get("pass") and fix and db.get_setting("auto_fix", True):
            db.update_job(jid, stage="auto-fix", progress=0.32)
            spec = channel_overrides(revise(c, spec, fix, data.get("facts"), ch), ch)
            stills = render_episode(spec, out_dir, stills_only=True)["stills"]
            rv2 = review(c, spec, stills, data.get("facts"))
            db.update_job(jid, data={"spec": spec, "qa": rv2, "qa_first": rv, "usage": _usage(c, data)})

    db.update_job(jid, status="running", stage="render", progress=0.4)
    result = render_episode(spec, out_dir, progress=_progress(jid, "render", 0.4, 0.58))
    db.update_job(jid, status="review", stage="ready for review", progress=1.0, error=None,
                  data={"render": result})
    if j.get("idea_id"):
        db.set_idea_status(j["idea_id"], "made")
    # optional autopilot publish
    rv = db.job(jid)["data"].get("qa") or {}
    if ch.get("autopublish") and (rv.get("pass") or not db.get_setting("qa_enabled", True)):
        publish(jid, ch.get("autopublish_platforms", ["youtube"]), privacy=ch.get("default_privacy", "public"))


def rerender(jid: str):
    _pool.submit(_safe, _rerender, jid)


def _rerender(jid: str):
    j = db.job(jid)
    spec = j["data"]["spec"]
    errs, warns = validate(spec)
    if errs:
        raise ValueError("; ".join(errs))
    db.update_job(jid, status="running", stage="render", progress=0.1)
    result = render_episode(spec, os.path.join(OUT, jid), progress=_progress(jid, "render", 0.1, 0.88))
    db.update_job(jid, status="review", stage="ready for review", progress=1.0, error=None, data={"render": result})


def revise_job(jid: str, instructions: str):
    _pool.submit(_safe, _revise, jid, instructions)


def _revise(jid: str, instructions: str):
    j = db.job(jid)
    data = j["data"]
    ch = db.channel(j["channel_id"])
    c = claude()
    db.update_job(jid, status="running", stage="revising", progress=0.1)
    spec = channel_overrides(revise(c, data["spec"], instructions, data.get("facts"), ch), ch)
    hist = data.get("revisions", []) + [{"at": dt.datetime.now().isoformat(timespec="seconds"), "instructions": instructions}]
    db.update_job(jid, data={"spec": spec, "revisions": hist, "usage": _usage(c, data)})
    _rerender(jid)


# ---------------------------------------------------------------- publishing
def publish(jid: str, platforms: list[str], privacy: str = "public", publish_at: str | None = None) -> list[dict]:
    j = db.job(jid)
    data = j["data"]
    spec = data["spec"]
    video = (data.get("render") or {}).get("video")
    if not video or not os.path.exists(video):
        raise ValueError("Render the video first")
    sec = db.channel_secrets(j["channel_id"])
    results = []
    if "youtube" in platforms:
        if not sec.get("youtube_creds"):
            raise ValueError("Connect YouTube for this channel first")
        r = youtube.upload(sec["youtube_creds"], video, spec, privacy=privacy, publish_at=publish_at,
                           thumbnail=(data.get("render") or {}).get("thumbnail"))
        if r.get("refreshed_credentials"):
            db.save_channel(db.channel(j["channel_id"]), {"youtube_creds": r["refreshed_credentials"]})
        db.add_publish(jid, "youtube", r["id"], r["url"], r.get("privacy") or privacy)
        results.append({"platform": "youtube", **{k: v for k, v in r.items() if k != "refreshed_credentials"}})
    if "instagram" in platforms:
        if not (sec.get("ig_token") and sec.get("ig_user_id")):
            raise ValueError("Connect Instagram for this channel first")
        r = instagram.publish_reel(sec["ig_user_id"], sec["ig_token"], video, instagram.build_caption(spec))
        db.add_publish(jid, "instagram", r["id"], r.get("url") or "", "published")
        results.append({"platform": "instagram", **r})
    db.update_job(jid, status="published", stage="published")
    return results


# ---------------------------------------------------------------- autopilot
def autopilot(cid: str):
    """Daily run for a channel: scout, take the best low-risk idea, make it (publish only if autopublish is on)."""
    ideas = run_scout(cid, n=6)
    pick = next((i for i in ideas if i.get("risk") == "low"), None)
    if pick:
        start_job(cid, pick)
