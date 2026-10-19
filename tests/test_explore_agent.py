import asyncio
from types import SimpleNamespace

from ai_testgen.explore_agent import (
    ALLOWED_TOOLS, OLD_RESULT_CHARS, parse_text_tool_call, run_agent, shorten_old_results, to_ollama_tools,
)


def scripted_llm(*replies):
    queue = list(replies)
    return lambda messages, tools: queue.pop(0)


async def fake_call(name, args):
    return f"ok:{name}:{args}"


def run(llm, **kw):
    return asyncio.run(run_agent(llm, None, [], "sys", "task", call_tool=fake_call, **kw))


def test_agent_calls_tools_then_stops_with_final_answer():
    llm = scripted_llm(
        {"content": "", "tool_calls": [{"name": "browser_navigate", "arguments": {"url": "http://x"}}]},
        {"content": "ParaBank has a login form.", "tool_calls": []},
    )
    r = run(llm)
    assert r.stopped == "done" and r.final == "ParaBank has a login form."
    assert r.steps[0].tool == "browser_navigate"
    assert r.steps[0].result.startswith("ok:browser_snapshot")  # observation after a page-changing action


def test_agent_stops_at_max_steps():
    llm = scripted_llm(*[{"content": "", "tool_calls": [{"name": "browser_snapshot", "arguments": {}}]}] * 3)
    r = run(llm, max_steps=3)
    assert r.stopped == "max_steps" and len(r.steps) == 3


def test_disallowed_tool_is_refused_not_executed():
    llm = scripted_llm({"content": "", "tool_calls": [{"name": "browser_run_code_unsafe", "arguments": {"code": "x"}}]},
                       {"content": "done", "tool_calls": []})
    r = run(llm)
    assert "not allowed" in r.steps[0].result
    assert "browser_run_code_unsafe" not in ALLOWED_TOOLS


def test_tool_errors_are_reported_to_the_model():
    async def boom(name, args):
        raise RuntimeError("element not found")

    llm = scripted_llm({"content": "", "tool_calls": [{"name": "browser_click", "arguments": {"target": "e1"}}]},
                       {"content": "done", "tool_calls": []})
    r = asyncio.run(run_agent(llm, None, [], "s", "t", call_tool=boom))
    assert "element not found" in r.steps[0].result and r.stopped == "done"


def test_old_tool_results_are_shortened_but_newest_kept():
    msgs = [{"role": "tool", "content": "a" * 1000}, {"role": "tool", "content": "b" * 1000}]
    shorten_old_results(msgs)
    assert len(msgs[0]["content"]) < 1000 and msgs[0]["content"].startswith("a" * OLD_RESULT_CHARS)
    assert len(msgs[1]["content"]) == 1000


def test_to_ollama_tools_filters_to_allowlist():
    tools = [SimpleNamespace(name="browser_click", description="Click\nmore", input_schema={"type": "object"}),
             SimpleNamespace(name="browser_evaluate", description="x", input_schema={})]
    out = to_ollama_tools(tools)
    assert [t["function"]["name"] for t in out] == ["browser_click"]
    assert out[0]["function"]["description"] == "Click"


def test_text_only_plan_before_any_tool_use_is_nudged():
    llm = scripted_llm(
        {"content": "I will navigate then click...", "tool_calls": []},
        {"content": "", "tool_calls": [{"name": "browser_navigate", "arguments": {"url": "http://x"}}]},
        {"content": "summary", "tool_calls": []},
    )
    r = run(llm)
    assert r.nudges == 1 and len(r.steps) == 1 and r.final == "summary"


def test_nudges_are_limited():
    llm = scripted_llm(*[{"content": "plan", "tool_calls": []}] * 3)
    r = run(llm)
    assert r.nudges == 2 and r.stopped == "done" and r.steps == []


def test_parse_text_tool_call():
    text = 'I will do this: {"name": "browser_click", "parameters": {"target": "e5"}}'
    assert parse_text_tool_call(text) == {"name": "browser_click", "arguments": {"target": "e5"}}
    assert parse_text_tool_call('{"name": "rm_rf", "parameters": {}}') is None
    assert parse_text_tool_call("just prose") is None


def test_text_tool_call_is_executed_and_snapshot_not_taken_for_errors():
    seen = []

    async def call(name, args):
        seen.append(name)
        return "### Error\nbad" if name == "browser_click" else "ok"

    llm = scripted_llm({"content": '{"name": "browser_click", "parameters": {"target": "e1"}}', "tool_calls": []},
                       {"content": "done", "tool_calls": []})
    r = asyncio.run(run_agent(llm, None, [], "s", "t", call_tool=call))
    assert seen == ["browser_click"] and r.steps[0].result.startswith("### Error")
