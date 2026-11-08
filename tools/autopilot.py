"""Autopilot: decides, once an hour, whether a video should be made now and with which options.

Runs at the top of the scheduled draft-video workflow. Reads the single `autopilot` row in Supabase, counts the
videos it already made today (IST), checks the posting slots and the topic queue, then either skips or creates a
job and prints the decision for the workflow:

    python tools/autopilot.py            # writes skip / request_id / job_id / options to $GITHUB_OUTPUT

Rules (all times Asia/Kolkata):
  - disabled -> skip
  - videos made today by autopilot >= videos_per_day -> skip
  - the k-th video of the day belongs to the k-th hour of sorted post_hours; due when the current hour >= it
  - topic: first queued entry of `topics`; else, when trending_fill is on, an empty topic (the scout picks a trend)
    with language and niche rotating over `languages` / `niches`; else skip
The job and the video share one id: ap-<YYYYMMDD-HHMMSS>.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import store  # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")


def now_ist() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).astimezone(IST)


def _row() -> dict:
    row = store.one("autopilot", id="eq.1")
    return row or {}


def _today_count(now: dt.datetime) -> int:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(dt.timezone.utc)
    rows = store.select("videos", select="id", source="eq.autopilot",
                        created_at=f"gte.{start.isoformat(timespec='seconds')}")
    return len(rows or [])


def _pick(values, index, default):
    vals = [v for v in (values or []) if v]
    return vals[index % len(vals)] if vals else default


def build_options(ap: dict, topic: dict | None, count: int) -> dict:
    """Options JSON for tools/e2e.py, from the autopilot row plus the chosen topic (or None for a trend)."""
    extra = ap.get("options") or {}
    platforms = ap.get("platforms") or {}
    o = {
        "topic": (topic or {}).get("text", "") or "",
        "language": (topic or {}).get("language") or _pick(ap.get("languages"), count, "en"),
        "niche": (topic or {}).get("niche") or _pick(ap.get("niches"), count, "space"),
        "format": (topic or {}).get("format") or "auto",
        "publish": {"youtube": bool(platforms.get("youtube")), "instagram": bool(platforms.get("instagram")),
                    "privacy": ap.get("privacy") or "public"},
        "source": "autopilot",
    }
    for k in ("hashtags", "voice", "music", "length", "notes", "writer", "aspect", "handle"):
        if extra.get(k):
            o[k] = extra[k]
    return o


def decide(now: dt.datetime | None = None) -> dict:
    """Returns {"skip": True, "reason": ...} or {"skip": False, "request_id", "job_id", "options"}."""
    now = now or now_ist()
    ap = _row()
    if not ap or not ap.get("enabled"):
        return {"skip": True, "reason": "autopilot off"}
    per_day = int(ap.get("videos_per_day") or 0)
    count = _today_count(now)
    if count >= per_day:
        return {"skip": True, "reason": f"quota reached ({count}/{per_day} today)"}
    hours = sorted(int(h) for h in (ap.get("post_hours") or [9]))
    due_hour = hours[min(count, len(hours) - 1)]
    if now.hour < due_hour:
        return {"skip": True, "reason": f"video {count + 1} is due at {due_hour:02d}:00 IST (now {now:%H:%M})"}

    topics = list(ap.get("topics") or [])
    topic = next((t for t in topics if isinstance(t, dict) and (t.get("status") or "queued") == "queued" and t.get("text")), None)
    if topic is None and not ap.get("trending_fill", True):
        return {"skip": True, "reason": "no queued topic and trending fill is off"}

    rid = "ap-" + now.strftime("%Y%m%d-%H%M%S")
    options = build_options(ap, topic, count)
    options["job_id"] = rid
    store.job_create(rid, "make", options, video_id=rid)
    store.video_upsert(rid, status="queued", stage="Queued", source="autopilot", options=options,
                       topic=options["topic"] or None, language=options["language"], niche=options["niche"])
    patch = {"last_run_at": store.now_iso()}
    if topic is not None:
        topic["status"] = "running"
        topic["video_id"] = rid
        patch["topics"] = topics
    store.update("autopilot", {"id": 1}, patch)
    return {"skip": False, "request_id": rid, "job_id": rid, "options": options,
            "reason": f"video {count + 1}/{per_day}, slot {due_hour:02d}:00 IST, topic: {options['topic'] or '(trending)'}"}


def mark_topic(rid: str, status: str) -> bool:
    """Set the status of the queued topic that produced video <rid> (called by e2e after packaging)."""
    ap = _row()
    topics = list(ap.get("topics") or [])
    hit = False
    for t in topics:
        if isinstance(t, dict) and t.get("video_id") == rid:
            t["status"] = status
            hit = True
    if hit:
        store.update("autopilot", {"id": 1}, {"topics": topics})
    return hit


def write_outputs(d: dict) -> None:
    lines = [f"skip={'true' if d.get('skip') else 'false'}"]
    if not d.get("skip"):
        lines += [f"request_id={d['request_id']}", f"job_id={d['job_id']}",
                  "options=" + json.dumps(d["options"], ensure_ascii=False, separators=(",", ":"))]
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    else:
        print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["mark"] and len(argv) >= 3:
        print("updated" if mark_topic(argv[1], argv[2]) else "no topic for that video")
        return 0
    if not store.enabled():
        print("autopilot off (Supabase not configured)")
        write_outputs({"skip": True})
        return 0
    d = decide()
    print(d.get("reason") or ("skip" if d["skip"] else "go"))
    write_outputs(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
