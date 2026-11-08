"""Offline tests: engine validation and a fast preview render, plus the agent loop against a fake Claude.

Run: python -m pytest -q tests   (or: python tests/test_offline.py)
"""
import copy
import json
import os
import sys
import tempfile
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agents import llm, qa, research, scout, writer  # noqa: E402
from engine.pipeline import render_episode, word_time  # noqa: E402
from engine.validate import validate  # noqa: E402

EXAMPLE = json.load(open(os.path.join(ROOT, "examples", "leonids_hi.json"), encoding="utf-8"))


# ------------------------------------------------------------------ engine
def test_example_validates():
    errs, warns = validate(EXAMPLE)
    assert errs == [], errs


def test_validator_catches_bad_spec():
    bad = copy.deepcopy(EXAMPLE)
    bad["scenes"][0]["elements"].append({"type": "prop", "name": "dragon"})
    bad["scenes"][1]["narration"] = ""
    errs, _ = validate(bad)
    assert any("dragon" in e for e in errs) and any("narration is empty" in e for e in errs)


def test_word_cue():
    t = word_time("सबसे अच्छा समय: अठारह नवंबर", "अठारह", 0.3, 4.0)
    assert 0.3 < t < 4.3


def test_preview_render_two_scenes():
    spec = copy.deepcopy(EXAMPLE)
    spec["scenes"] = spec["scenes"][:2]
    spec["preview"] = True
    spec["fps"] = 15
    out = tempfile.mkdtemp()
    res = render_episode(spec, out)
    assert os.path.getsize(res["video"]) > 50_000
    assert res["scenes"] == 2 and res["duration"] > 3


# ------------------------------------------------------------------ stock footage
FOOTAGE_BG = {"type": "footage", "query": "cat playing", "dim": 0.5, "tint": "#0b1030",
              "fallback": {"type": "sky", "time": "night"}}


def test_footage_background_validates():
    spec = copy.deepcopy(EXAMPLE)
    spec["scenes"][0]["background"] = copy.deepcopy(FOOTAGE_BG)
    spec["footage"] = "auto"
    errs, _ = validate(spec)
    assert errs == [], errs
    bad = copy.deepcopy(spec)
    bad["scenes"][0]["background"] = {"type": "footage", "dim": 1.5, "fallback": {"type": "footage", "query": "x"}}
    bad["footage"] = "maybe"
    errs, _ = validate(bad)
    assert any("query" in e for e in errs) and any("dim" in e for e in errs)
    assert any("fallback" in e for e in errs) and any("`footage`" in e for e in errs)


def test_footage_falls_back_without_key(monkeypatch):
    """No PEXELS_API_KEY: the footage scene renders on its fallback background and the mp4 is still produced."""
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    from engine import footage
    assert footage.search("cat playing") == []
    spec = copy.deepcopy(EXAMPLE)
    spec["scenes"] = spec["scenes"][:2]
    spec["scenes"][1]["background"] = copy.deepcopy(FOOTAGE_BG)
    spec["preview"] = True
    spec["fps"] = 12
    out = tempfile.mkdtemp()
    res = render_episode(spec, out)
    assert os.path.getsize(res["video"]) > 50_000 and res["scenes"] == 2
    assert res["footage"] == []


def test_footage_prepare_and_composite():
    """prepare() cuts a synthetic clip to WxH and the requested length; the renderer composites it under a scene."""
    import subprocess
    from engine import footage
    d = tempfile.mkdtemp()
    src = os.path.join(d, "src.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=12",
                    "-t", "2", "-pix_fmt", "yuv420p", src], check=True)
    dst = footage.prepare(src, os.path.join(d, "cut.mp4"), 270, 480, 3.0, 12)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", dst], capture_output=True, text=True)
    assert probe.stdout.strip() == "270,480"
    assert abs(footage.probe_duration(dst) - 3.0) < 0.2       # looped past the 2 s source
    # a footage scene with a prepared file goes through the two-input ffmpeg path
    spec = copy.deepcopy(EXAMPLE)
    spec["scenes"] = spec["scenes"][:2]
    spec["scenes"][1]["background"] = copy.deepcopy(FOOTAGE_BG)
    spec["preview"] = True
    spec["fps"] = 12
    from engine import pipeline
    import numpy as np
    spec = pipeline.normalize(spec)
    from engine import audio as A
    voices = [np.zeros(int(1.2 * A.SR), dtype=np.float32)] * 2
    tl = pipeline.build_timeline(spec, voices)
    big = footage.prepare(src, os.path.join(d, "scene.mp4"), spec["_W"], spec["_H"], tl[1]["dur"] + 0.5, 12)
    spec["scenes"][1]["background"].update({"_file": big, "_clip": "test_1"})
    from engine.renderer import Renderer
    rnd = Renderer(spec, tl, np.zeros(sum(s["frames"] for s in tl)))
    still = rnd.still(1, 1.0, os.path.join(d, "still.png"))
    assert os.path.getsize(still) > 1000
    mp4 = rnd.encode_scene(1, os.path.join(d, "scene_out.mp4"))
    assert os.path.getsize(mp4) > 5_000
    assert abs(footage.probe_duration(mp4) - tl[1]["dur"]) < 0.2
    assert footage.credits([{"id": "1", "provider": "pexels", "credit": "Ana"}]) == ["Video: Ana / Pexels"]


def test_footage_pick_is_deterministic():
    from engine import footage
    res = [{"id": str(i), "provider": "pexels", "duration": 3 + i} for i in range(8)]
    a = footage.pick(res, 6.0, query="cat playing")
    b = footage.pick(res, 6.0, query="cat playing")
    assert a == b and a["duration"] >= 6.0
    c = footage.pick(res, 6.0, exclude={a["id"]}, query="cat playing")
    assert c["id"] != a["id"]
    assert footage.pick(res, 99.0)["id"] == "7"           # nothing long enough: the longest
    assert footage.pick([], 3.0) is None


# ------------------------------------------------------------------ agents with a fake Claude
class FakeBlock(SimpleNamespace):
    def model_dump(self, **kw):
        return {k: v for k, v in self.__dict__.items()}


def msg(blocks, stop="tool_use"):
    return SimpleNamespace(content=blocks, stop_reason=stop,
                           usage=SimpleNamespace(input_tokens=100, output_tokens=50, server_tool_use=None))


class FakeClaude(llm.Claude):
    def __init__(self, script):
        self.roles = dict(llm.DEFAULT_ROLES)
        self.usage = {"input_tokens": 0, "output_tokens": 0, "web_searches": 0}
        self.script = list(script)
        self.calls = []

    def create(self, role, system, messages, tools=None, tool_choice=None, max_tokens=16000):
        self.calls.append({"role": role, "tools": [t.get("name") for t in tools or []], "choice": tool_choice,
                           "n_messages": len(messages)})
        m = self.script.pop(0)
        self._track(m)
        return m


def tool(name, payload):
    return FakeBlock(type="tool_use", name=name, input=payload, id="toolu_1")


def test_scout_sorts_and_routes():
    ideas = {"ideas": [{"topic": "a", "angle": "", "hook": "", "format": "space_facts", "why_now": "", "evergreen": True,
                        "risk": "low", "score": 40, "title": "A"},
                       {"topic": "b", "angle": "", "hook": "", "format": "space_facts", "why_now": "", "evergreen": False,
                        "risk": "low", "score": 90, "title": "B"}]}
    c = FakeClaude([msg([tool("submit_ideas", ideas)])])
    out = scout.scout(c, {"name": "x", "niche": "space"}, [{"source": "t", "title": "Leonids"}])
    assert [i["topic"] for i in out] == ["b", "a"]
    assert c.calls[0]["role"] == "scout" and c.calls[0]["choice"] == {"type": "tool", "name": "submit_ideas"}


def test_research_handles_pause_and_nudge():
    facts = {"summary": "s", "facts": [{"claim": "71 km/s", "source_url": "https://x", "confidence": "high"}], "avoid": []}
    c = FakeClaude([
        msg([FakeBlock(type="server_tool_use", name="web_search", input={"query": "leonids"}, id="srv_1")], stop="pause_turn"),
        msg([FakeBlock(type="text", text="Found it.")], stop="end_turn"),
        msg([tool("submit_facts", facts)]),
    ])
    out = research.research(c, {"topic": "Leonids"}, {"name": "x"})
    assert out["facts"][0]["claim"] == "71 km/s"
    assert "web_search" in c.calls[0]["tools"] and c.calls[0]["choice"] == {"type": "auto"}
    assert c.calls[2]["choice"] == {"type": "tool", "name": "submit_facts"}


def test_writer_repairs_invalid_spec_once():
    bad = copy.deepcopy(EXAMPLE)
    bad["scenes"][0]["elements"].append({"type": "prop", "name": "dragon"})
    c = FakeClaude([msg([tool("submit_episode", bad)]), msg([tool("submit_episode", copy.deepcopy(EXAMPLE))])])
    spec = writer.write_episode(c, {"topic": "Leonids", "format": "space_facts"}, {"facts": []}, {"name": "x"})
    assert not any(e.get("name") == "dragon" for e in spec["scenes"][0]["elements"])
    assert len(c.calls) == 2 and c.calls[1]["n_messages"] == 3


def test_forced_tool_choice_fallback():
    """Opus/Fable reject a forced tool_choice; json_tool must fall back to auto and still get the tool call."""
    import anthropic

    class Picky(FakeClaude):
        def create(self, role, system, messages, tools=None, tool_choice=None, max_tokens=16000):
            if tool_choice and tool_choice.get("type") == "tool":
                resp = SimpleNamespace(request=SimpleNamespace(method="POST", url="https://api.anthropic.com/v1/messages"),
                                       status_code=400, headers={})
                raise anthropic.BadRequestError('tool_choice: type "tool" and "any" are not supported for this model.',
                                                response=resp, body=None)
            return super().create(role, system, messages, tools, tool_choice, max_tokens)

    c = Picky([msg([FakeBlock(type="text", text="Here is my idea")], stop="end_turn"),
               msg([tool("submit_ideas", {"ideas": []})])])
    c.roles["scout"] = "claude-test-picky"
    out = scout.scout(c, {"name": "x"}, [])
    assert out == [] and all(call["choice"] == {"type": "auto"} for call in c.calls)
    assert "claude-test-picky" in llm.NO_FORCED_TOOL


def test_qa_sends_images(tmp_path=None):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "still_01_18.jpg")
    from PIL import Image
    Image.new("RGB", (54, 96), "black").save(p)
    rv = {"pass": False, "score": 6, "issues": [{"scene": "1", "severity": "major", "problem": "text cut", "fix": "y 0.2"}],
          "fact_check": "ok"}
    c = FakeClaude([msg([tool("submit_review", rv)])])
    out = qa.review(c, EXAMPLE, [p], {})
    assert out["score"] == 6 and "text cut" in qa.issues_to_instructions(out)


def test_research_tolerates_loose_tool_output():
    """Seen live: with tool_choice auto the model returned facts as plain strings (and sometimes as a JSON string)."""
    loose = {"summary": "s", "avoid": "myth one",
             "facts": ["Mars has two moons (source: https://nasa.gov/mars).",
                       '{"claim": "Phobos is falling", "source_url": "https://esa.int/p", "confidence": "HIGH"}',
                       {"claim": "Deimos is small", "url": "https://x.org", "confidence": "sure"}]}
    c = FakeClaude([msg([tool("submit_facts", loose)])])
    out = research.research(c, {"title": "Mars"}, {"name": "x"})
    f = out["facts"]
    assert [x["claim"] for x in f] == ["Mars has two moons.", "Phobos is falling", "Deimos is small"]
    assert [x["source_url"] for x in f] == ["https://nasa.gov/mars", "https://esa.int/p", "https://x.org"]
    assert [x["confidence"] for x in f] == ["medium", "high", "medium"] and out["avoid"] == ["myth one"]
    as_string = dict(loose, facts=json.dumps([{"claim": "a", "source_url": "https://a.b", "confidence": "low"}]))
    c = FakeClaude([msg([tool("submit_facts", as_string)])])
    assert research.research(c, {}, {})["facts"][0]["claim"] == "a"


def test_coerce_schema():
    sch = {"type": "object", "properties": {"n": {"type": "integer"}, "ok": {"type": "boolean"},
                                            "items": {"type": "array", "items": {"type": "object", "required": ["name"],
                                                                                 "properties": {"name": {"type": "string"}}}}}}
    out = llm.coerce({"n": "7", "ok": "true", "items": '[{"name": "a"}, "b"]'}, sch)
    assert out == {"n": 7, "ok": True, "items": [{"name": "a"}, {"name": "b"}]}


def test_metadata_limits():
    """Hashtag and length rules hold whatever the model returns."""
    from agents import metadata
    many = [f"#tag{i}" for i in range(12)] + ["#Shorts", "#space facts", "#SPACE-facts"]
    raw = {"youtube": {"title": "A very long title " * 10 + "#viral", "description": "Desc #extra",
                       "hashtags": many, "tags": ["x" * 90] * 8 + ["space"]},
           "instagram": {"caption": "Caption #inline", "hashtags": many}}
    m = metadata.finalize(raw, {"aspect": "9:16"}, brand_tags=["#SpaceIsWeird"], extra_tags=["my tag"])
    yt, ig = m["youtube"], m["instagram"]
    assert len(yt["title"]) <= 100 and yt["title"].endswith("#Shorts") and "#viral" not in yt["title"]
    assert len(yt["hashtags"]) <= 5 and "#Shorts" not in yt["hashtags"]
    assert yt["hashtags"][:2] == ["#MyTag", "#SpaceIsWeird"]
    assert sum(len(t) + 1 for t in yt["tags"]) <= 480
    assert len(ig["hashtags"]) <= 5 and ig["caption"].count("#") == len(ig["hashtags"])
    assert metadata.AI_LINE in yt["description"] and metadata.AI_LINE in ig["caption"]
    assert metadata.clean_tag("#space facts!") == "#SpaceFacts" and metadata.clean_tag("अंतरिक्ष") == "#अंतरिक्ष"


def test_library_notes_roundtrip():
    from tools import library
    d = tempfile.mkdtemp()
    json.dump({"id": "abc", "title": "T", "duration": 31.6, "language": "en", "qa_score": 9, "usd": 0.5},
              open(os.path.join(d, "summary.json"), "w"))
    json.dump({"youtube": {"title": "T #Shorts", "description": "Line one --> tricky\n\nmore"}},
              open(os.path.join(d, "meta.json"), "w"))
    body = library.notes(d, {"niche": "space"})
    data = library.parse(body)
    assert data["summary"]["id"] == "abc" and data["options"]["niche"] == "space"
    assert "tricky" in data["meta"]["youtube"]["description"]


# ------------------------------------------------------------------ autopilot against a fake Supabase store
class FakeStore:
    """Stands in for tools.store.select/upsert/update: one autopilot row and a list of today's autopilot videos."""

    def __init__(self, ap: dict, videos_today: int = 0):
        self.ap = {"id": 1, "enabled": True, "videos_per_day": 3, "post_hours": [9, 13, 18], "platforms": {"youtube": True},
                   "languages": ["en", "hi"], "niches": ["space", "tech"], "topics": [], "trending_fill": True,
                   "privacy": "public", "options": {}, **ap}
        self.videos_today = videos_today
        self.upserts, self.updates = [], []

    def select(self, table, **f):
        if table == "autopilot":
            return [self.ap]
        if table == "videos":
            return [{"id": f"v{i}"} for i in range(self.videos_today)]
        return []

    def upsert(self, table, row, on_conflict="id"):
        self.upserts.append((table, row))
        return row

    def update(self, table, match, patch):
        self.updates.append((table, match, patch))
        if table == "autopilot":
            self.ap.update(patch)
        return [patch]

    def install(self, monkeypatch):
        from tools import store
        monkeypatch.setattr(store, "select", self.select)
        monkeypatch.setattr(store, "upsert", self.upsert)
        monkeypatch.setattr(store, "update", self.update)
        return self


def _ist(hour, minute=0):
    import datetime as dt
    from tools.autopilot import IST
    return dt.datetime(2026, 11, 8, hour, minute, tzinfo=IST)


def test_autopilot_off(monkeypatch):
    from tools import autopilot
    fs = FakeStore({"enabled": False}).install(monkeypatch)
    d = autopilot.decide(_ist(10))
    assert d["skip"] and d["reason"] == "autopilot off" and not fs.upserts


def test_autopilot_quota_reached(monkeypatch):
    from tools import autopilot
    fs = FakeStore({"videos_per_day": 2}, videos_today=2).install(monkeypatch)
    d = autopilot.decide(_ist(20))
    assert d["skip"] and "quota" in d["reason"] and not fs.upserts


def test_autopilot_not_yet_due(monkeypatch):
    from tools import autopilot
    fs = FakeStore({}, videos_today=1).install(monkeypatch)       # second video belongs to the 13:00 slot
    d = autopilot.decide(_ist(12, 30))
    assert d["skip"] and "13:00" in d["reason"] and not fs.upserts


def test_autopilot_due_with_queued_topic(monkeypatch):
    from tools import autopilot
    topics = [{"text": "Why Venus spins backwards", "language": "hi", "niche": "space", "status": "done", "video_id": "old"},
              {"text": "NavIC vs GPS", "language": "hi", "status": "queued"},
              {"text": "Later", "status": "queued"}]
    fs = FakeStore({"topics": topics, "platforms": {"youtube": True, "instagram": True}, "privacy": "unlisted",
                    "options": {"hashtags": "#india", "voice": "hm_omega", "length": 45}}, videos_today=1).install(monkeypatch)
    d = autopilot.decide(_ist(13, 30))
    assert not d["skip"]
    assert d["request_id"] == d["job_id"] == "ap-20261108-133000"
    o = d["options"]
    assert o["topic"] == "NavIC vs GPS" and o["language"] == "hi" and o["niche"] == "tech"   # niche: round robin by count
    assert o["publish"] == {"youtube": True, "instagram": True, "privacy": "unlisted"}
    assert o["source"] == "autopilot" and o["job_id"] == d["job_id"] and o["voice"] == "hm_omega" and o["length"] == 45
    jobs = [r for t, r in fs.upserts if t == "jobs"]
    assert jobs and jobs[0]["id"] == d["job_id"] and jobs[0]["status"] == "queued" and jobs[0]["kind"] == "make"
    assert any(t == "videos" and r["source"] == "autopilot" and r["status"] == "queued" for t, r in fs.upserts)
    assert fs.ap["topics"][1] == {"text": "NavIC vs GPS", "language": "hi", "status": "running", "video_id": d["job_id"]}
    assert fs.ap["topics"][2]["status"] == "queued" and fs.ap.get("last_run_at")
    assert autopilot.mark_topic(d["job_id"], "done") and fs.ap["topics"][1]["status"] == "done"
    assert not autopilot.mark_topic("nope", "done")


def test_autopilot_due_with_trending_fill(monkeypatch):
    from tools import autopilot
    fs = FakeStore({"topics": [{"text": "x", "status": "done"}]}, videos_today=0).install(monkeypatch)
    d = autopilot.decide(_ist(9))
    assert not d["skip"] and d["options"]["topic"] == "" and d["options"]["language"] == "en" and d["options"]["niche"] == "space"
    assert d["options"]["publish"]["instagram"] is False
    fs2 = FakeStore({"topics": [], "trending_fill": False}).install(monkeypatch)
    d2 = autopilot.decide(_ist(9))
    assert d2["skip"] and "trending fill is off" in d2["reason"] and not fs2.upserts


def test_autopilot_outputs(monkeypatch, tmp_path):
    from tools import autopilot
    p = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(p))
    autopilot.write_outputs({"skip": False, "request_id": "ap-1", "job_id": "ap-1", "options": {"topic": "a b", "publish": {}}})
    lines = p.read_text().splitlines()
    assert lines[:3] == ["skip=false", "request_id=ap-1", "job_id=ap-1"] and lines[3] == 'options={"topic":"a b","publish":{}}'


def test_store_noop_without_supabase(monkeypatch):
    from tools import store
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    assert not store.enabled() and store.select("videos") == [] and store.upsert("videos", {"id": "x"}) == {}
    assert store.load_settings_into_env() == {}
    monkeypatch.setenv("GITHUB_REPOSITORY", "me/vidforge")
    assert store.release_urls("abc")["video_url"] == "https://github.com/me/vidforge/releases/download/video-abc/final.mp4"


def test_every_element_type_renders():
    """Smoke test: one still per vocabulary so a missing skia API or a typo in draw.py fails here, not on the runner."""
    from engine import draw
    from engine.validate import PARTICLES, BEHAVIORS
    base = {"title": "smoke", "language": "en", "voice": "af_heart", "aspect": "9:16", "music": {"mood": "none"},
            "captions": {"enabled": False}, "scenes": []}
    shapes = ["circle", "rect", "ring", "star", "heart", "triangle", "line", "arrow", "path"]
    els = [{"type": "shape", "shape": sh, "x": 0.1 + 0.1 * i, "y": 0.2, "w": 0.08, "h": 0.08, "r": 0.04, "color": "#ffd400",
            "x2": 0.3, "y2": 0.3, "d": "M10 10 L90 10 L50 90 Z", "enter": "pop"} for i, sh in enumerate(shapes)]
    els += [{"type": "prop", "name": n, "x": 0.1 + 0.08 * (i % 11), "y": 0.4 + 0.1 * (i // 11), "w": 0.07}
            for i, n in enumerate(sorted(draw.PROPS))]
    els += [{"type": "character", "species": sp, "x": 0.1 + 0.08 * i, "y": 0.72, "w": 0.07, "behavior": b}
            for i, (sp, b) in enumerate(zip(sorted(draw.SPECIES), sorted(BEHAVIORS) * 2))]
    els += [{"type": "particles", "kind": k, "count": 10} for k in sorted(PARTICLES)]
    els += [{"type": "text", "text": "Smoke test", "x": 0.5, "y": 0.9, "size": 0.05},
            {"type": "counter", "to": 1234567, "x": 0.5, "y": 0.1, "size": 0.06, "format": "indian"},
            {"type": "emoji", "text": "🚀", "x": 0.9, "y": 0.1, "size": 0.06},
            {"type": "constellation", "name": "orion", "x": 0.5, "y": 0.5, "w": 0.4},
            {"type": "svg", "svg": "<svg viewBox='0 0 10 10'><circle cx='5' cy='5' r='4' fill='red'/></svg>", "x": 0.5, "y": 0.6, "w": 0.1}]
    for bg in [b for b in draw.BACKGROUNDS if b not in ("image", "footage")]:
        base["scenes"].append({"id": bg, "narration": "Smoke.", "duration": 2,
                               "background": {"type": bg, "mood": "night", "color": "#223355", "colors": ["#223355", "#000000"]},
                               "elements": els[:6] if bg != "space" else els})
    for pl in sorted(draw.PLANETS) + ["black_hole", "neutron_star", "pulsar"]:
        base["scenes"][0]["elements"].append({"type": "planet", "style": pl, "x": 0.2, "y": 0.3, "w": 0.1})
    errs, _ = validate(base)
    assert not [e for e in errs if "unknown" in e.lower()], errs
    d = tempfile.mkdtemp()
    out = render_episode(base, d, stills_only=True)
    assert len(out["stills"]) >= len(base["scenes"])


def test_footage_shortfall_rule():
    sc = lambda i, t: {"id": f"s{i}", "background": {"type": t}}
    spec = {"scenes": [sc(1, "footage"), sc(2, "space"), sc(3, "sunburst"), sc(4, "paper"), sc(5, "footage")]}
    assert writer.footage_shortfall(spec, {"niche": "mythology"}) == ["s2", "s3", "s4"]
    assert writer.footage_shortfall(spec, {"niche": "space"}) == []
    assert writer.footage_shortfall(spec, {"niche": "animals", "footage": "off"}) == []
    assert writer.footage_shortfall(dict(spec, made_for_kids=True), {"niche": "animals"}) == []
    good = {"scenes": [sc(i, "footage") for i in range(4)] + [sc(9, "space")]}
    assert writer.footage_shortfall(good, {"niche": "food"}) == []


def test_publish_gate_skips_failed_review(monkeypatch, capsys):
    from tools import e2e
    d = tempfile.mkdtemp()
    json.dump({"score": 5, "pass": False}, open(os.path.join(d, "qa.json"), "w"))
    called = []
    monkeypatch.setattr("tools.publish.publish", lambda *a, **k: called.append(1))
    e2e.stage_publish(d, {"publish": {"youtube": True}}, {})
    assert not called and "Needs review" in capsys.readouterr().out
    e2e.stage_publish(d, {"publish": {"youtube": True, "force": True}}, {})
    assert called

def test_world3d_time_refs_and_stepwell():
    from engine import world3d as W3
    spec = json.load(open(os.path.join(ROOT, "examples", "built_rani_ki_vav.json"), encoding="utf-8"))
    errs, warns = validate(spec)
    assert errs == [], errs
    tl = [{"start": 5.0 * i, "dur": 5.0, "voice_start": 0.2, "voice_dur": 4.0} for i in range(len(spec["scenes"]))]
    w = W3.prepare_world(spec, tl)
    dig = w["terrain"]["digs"][0]
    assert dig["from"] == 5.0 + 0.25 and dig["to"] == 5.0 + 4.25       # scene "well" is the second scene
    types = [o["type"] for o in w["objects"]]
    assert "stepwell" not in types and types.count("stairs") == 6 and "water" in types and "pavilion" in types
    assert len(w["terrain"]["digs"]) == 2                               # the macro added the big trench
    cam = w["camera"]
    assert all(isinstance(k["at"], float) for k in cam) and cam == sorted(cam, key=lambda k: k["at"])
    bad = dict(spec, world3d=dict(spec["world3d"], objects=[{"type": "dragon"}],
                                  camera=[{"at": {"scene": "nope"}, "pos": [0, 0, 0]}]))
    e2, _ = validate(bad)
    assert any("dragon" in e for e in e2) and any("nope" in e for e in e2)


def test_world3d_renders_a_frame():
    """Smoke test of the browser renderer when a Chromium is available (skipped otherwise)."""
    import pytest
    pytest.importorskip("playwright")
    from engine.world3d import World3DRenderer, expand
    world = expand({"terrain": {"width": 20, "length": 20, "cut": 4,
                                "digs": [{"x0": -2, "x1": 2, "z0": -6, "z1": 4, "depth": 4, "from": 0, "to": 1}]},
                    "objects": [{"type": "stepwell", "x0": -3, "x1": 3, "z_front": 4, "length": 12, "depth": 5, "levels": 3},
                                {"type": "person", "pos": [5, 0, 2], "action": "dig"}, {"type": "trees", "count": 4, "seed": 2}],
                    "camera": [{"at": 0, "pos": [10, 8, 20], "look": [0, -2, -2]}]})
    d = tempfile.mkdtemp()
    try:
        with World3DRenderer(216, 384, scale=0.5) as r:
            r.setup(world)
            out = r.render_range(0.5, 0.5, 4, os.path.join(d, "w.mp4"))
            still = r.still(1.0, os.path.join(d, "w.jpg"))
    except RuntimeError as e:
        pytest.skip(f"no browser: {e}")
    from PIL import Image
    assert os.path.getsize(out) > 1000 and Image.open(still).size == (216, 384)

def test_studio_option_aliases():
    from tools.e2e import parse_options, build_channel
    o = parse_options({"language": "en", "niche": "trending", "format": "facts", "voice": "auto", "music": "auto",
                       "footage": "auto", "writer": "claude-opus-5-5"})
    assert o["format"] == "facts" and o["niche"] == "general" and "voice" not in o and "music" not in o
    ch = build_channel(o)
    assert ch["voice"] != "auto" and ch["formats"][0] == "facts" and ch["footage"] == "auto"
    assert parse_options({"format": "toplist"})["format"] == "facts_list"
    assert parse_options({"format": "trend"})["format"] == "trend_explainer"

if __name__ == "__main__":
    import inspect
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
    for f in fns:
        if any(p.default is p.empty for p in inspect.signature(f).parameters.values()):
            print("skip", f.__name__, "(needs pytest fixtures)")
            continue
        f()
        print("pass", f.__name__)
