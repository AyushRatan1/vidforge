"""Thin Claude client: role-based model routing, streaming, JSON-by-tool, server-side web search."""
from __future__ import annotations

import json
import time

import anthropic

MODELS = {
    "claude-fable-5-1": "Claude Fable 5.1 (deepest reasoning, $10/$50 per MTok)",
    "claude-opus-5-5": "Claude Opus 5.5 (best default, $4/$20 per MTok)",
    "claude-sonnet-5-5": "Claude Sonnet 5.5 (fast, $2/$10 per MTok)",
    "claude-haiku-5-5": "Claude Haiku 5.5 (cheapest)",
}

DEFAULT_ROLES = {
    "scout": "claude-sonnet-5-5",      # ranks trend candidates
    "research": "claude-sonnet-5-5",   # web search fact sheet
    "writer": "claude-opus-5-5",       # script + scene direction
    "qa": "claude-sonnet-5-5",         # vision review of frames
    "metadata": "claude-sonnet-5-5",   # titles, captions, hashtags
}

# Models seen to reject a forced tool_choice (adaptive thinking always on). Learned at runtime too.
NO_FORCED_TOOL = {"claude-opus-5-5", "claude-fable-5-1"}

WEB_SEARCH = {"type": "web_search_20250305", "name": "web_search", "max_uses": 6,
              "user_location": {"type": "approximate", "country": "IN", "timezone": "Asia/Kolkata"}}


class Claude:
    def __init__(self, api_key: str, roles: dict | None = None):
        if not api_key:
            raise ValueError("Add your Anthropic API key in Settings first.")
        self.client = anthropic.Anthropic(api_key=api_key, max_retries=3)
        self.roles = {**DEFAULT_ROLES, **(roles or {})}
        self.usage = {"input_tokens": 0, "output_tokens": 0, "web_searches": 0}

    def _track(self, msg):
        u = msg.usage
        self.usage["input_tokens"] += getattr(u, "input_tokens", 0) or 0
        self.usage["output_tokens"] += getattr(u, "output_tokens", 0) or 0
        stu = getattr(u, "server_tool_use", None)
        if stu is not None:
            self.usage["web_searches"] += getattr(stu, "web_search_requests", 0) or 0

    def create(self, role: str, system: str, messages: list, tools=None, tool_choice=None, max_tokens=16000):
        kw = dict(model=self.roles[role], system=system, messages=messages, max_tokens=max_tokens)
        if tools:
            kw["tools"] = tools
        if tool_choice:
            kw["tool_choice"] = tool_choice
        for attempt in range(3):
            try:
                with self.client.messages.stream(**kw) as stream:
                    msg = stream.get_final_message()
                self._track(msg)
                return msg
            except anthropic.RateLimitError:
                time.sleep(20 * (attempt + 1))
        raise RuntimeError("Claude rate limit: try again in a minute")

    def json_tool(self, role: str, system: str, content, name: str, description: str, schema: dict,
                  max_tokens=16000, extra_tools=None, history=None) -> dict:
        """Ask Claude to answer by calling `name`. Handles web search pauses when extra_tools include it.

        Models with always-on thinking (Opus 5.5, Fable 5.1) reject a forced tool_choice, so for those we use
        tool_choice "auto" plus an explicit instruction, and nudge if the model answers in text instead.
        """
        model = self.roles[role]
        tool = {"name": name, "description": description, "input_schema": schema}
        tools = [tool] + list(extra_tools or [])
        messages = list(history or []) + [{"role": "user", "content": content}]
        system = f"{system}\n\nAlways deliver your final answer by calling the `{name}` tool. Do not answer in plain text."

        def pick_choice(force: bool):
            return {"type": "tool", "name": name} if force and model not in NO_FORCED_TOOL else {"type": "auto"}

        choice = pick_choice(not extra_tools)
        for _ in range(8):
            try:
                msg = self.create(role, system, messages, tools=tools, tool_choice=choice, max_tokens=max_tokens)
            except anthropic.BadRequestError as e:
                if choice.get("type") in ("tool", "any") and "tool_choice" in str(e):
                    NO_FORCED_TOOL.add(model)
                    choice = {"type": "auto"}
                    continue
                raise
            for block in msg.content:
                if block.type == "tool_use" and block.name == name:
                    return block.input
            messages.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in msg.content]})
            if msg.stop_reason == "pause_turn":
                continue
            messages.append({"role": "user", "content": f"Now call the `{name}` tool with your complete final answer."})
            choice = pick_choice(True)
        raise RuntimeError(f"Claude did not return {name}")


def parse_json_loose(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)
