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


if __name__ == "__main__":
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
    for f in fns:
        f()
        print("pass", f.__name__)
