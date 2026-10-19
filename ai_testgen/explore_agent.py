"""A minimal exploration agent: a local LLM calls Playwright MCP tools to explore a web app.

Deliberately small (plan Day 41 builds the real agent loop): fixed step limit, tool allowlist,
old tool results shortened so the context window is not exhausted by page snapshots.
"""
import json
from dataclasses import dataclass, field

ALLOWED_TOOLS = (
    "browser_navigate", "browser_snapshot", "browser_click", "browser_type",
    "browser_fill_form", "browser_select_option", "browser_wait_for",
)
MAX_RESULT_CHARS = 5000   # newest tool result, in full up to this size
OLD_RESULT_CHARS = 300    # older tool results are cut to this


@dataclass
class Step:
    n: int
    tool: str | None = None
    args: dict | None = None
    result: str = ""
    note: str = ""        # model's text for this step


@dataclass
class AgentRun:
    steps: list[Step] = field(default_factory=list)
    final: str = ""
    stopped: str = ""     # "done" | "max_steps"


def to_ollama_tools(mcp_tools, allowed=ALLOWED_TOOLS) -> list[dict]:
    return [
        {"type": "function", "function": {"name": t.name, "description": (t.description or "").split("\n")[0],
                                           "parameters": t.input_schema}}
        for t in mcp_tools if t.name in allowed
    ]


def shorten_old_results(messages: list[dict], keep_last: int = 1) -> None:
    """Cut every tool message except the newest `keep_last` so snapshots do not pile up in context."""
    tool_idx = [i for i, m in enumerate(messages) if m["role"] == "tool"]
    for i in tool_idx[:-keep_last] if keep_last else tool_idx:
        if len(messages[i]["content"]) > OLD_RESULT_CHARS:
            messages[i]["content"] = messages[i]["content"][:OLD_RESULT_CHARS] + " ...[older result shortened]"


async def run_agent(llm_chat, session, tools: list[dict], system: str, task: str, max_steps: int = 20, call_tool=None) -> AgentRun:
    """`llm_chat(messages, tools) -> {"content": str, "tool_calls": [{"name":..., "arguments":...}]}`.

    `call_tool(name, args) -> str` defaults to calling the MCP session.
    """
    from ai_testgen.mcp_session import result_text

    async def default_call(name, args):
        return result_text(await session.call_tool(name, args))

    call = call_tool or default_call
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    run = AgentRun()
    for n in range(1, max_steps + 1):
        reply = llm_chat(messages, tools)
        calls = reply.get("tool_calls") or []
        messages.append({"role": "assistant", "content": reply.get("content") or "",
                         **({"tool_calls": [{"function": c} for c in calls]} if calls else {})})
        if not calls:
            run.final, run.stopped = reply.get("content") or "", "done"
            return run
        for c in calls:
            name, args = c["name"], c.get("arguments") or {}
            step = Step(n=n, tool=name, args=args, note=reply.get("content") or "")
            if name not in ALLOWED_TOOLS:
                step.result = f"Error: tool {name} is not allowed."
            else:
                try:
                    step.result = (await call(name, args))[:MAX_RESULT_CHARS]
                except Exception as e:  # a bad tool call should be shown to the model, not crash the run
                    step.result = f"Error: {type(e).__name__}: {e}"
            run.steps.append(step)
            messages.append({"role": "tool", "content": step.result, "tool_name": name})
        shorten_old_results(messages)
    run.stopped = "max_steps"
    return run


def render_transcript(run: AgentRun, title: str, task: str) -> str:
    lines = [f"# {title}", "", f"**Task:** {task}", "", f"Steps: {len(run.steps)}, stopped: {run.stopped}", ""]
    for s in run.steps:
        lines += [f"## Step {s.n}: `{s.tool}`", "", f"Args: `{json.dumps(s.args)}`", ""]
        if s.note:
            lines += [f"Model said: {s.note}", ""]
        snippet = s.result if len(s.result) < 700 else s.result[:700] + "\n...[truncated]"
        lines += ["```", snippet, "```", ""]
    lines += ["## Final answer", "", run.final or "(none)", ""]
    return "\n".join(lines)
