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


if __name__ == "__main__":
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
    for f in fns:
        f()
        print("pass", f.__name__)
