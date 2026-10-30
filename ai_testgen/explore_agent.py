"""A minimal exploration agent: a local LLM calls Playwright MCP tools to explore a web app.

Deliberately small (plan Day 41 builds the real agent loop): fixed step limit, tool allowlist,
old tool results shortened so the context window is not exhausted by page snapshots.
"""
import json
import re
from dataclasses import dataclass, field

ALLOWED_TOOLS = (
    "browser_navigate", "browser_snapshot", "browser_click", "browser_type",
    "browser_fill_form", "browser_select_option", "browser_wait_for",
)
# Playwright MCP returns only a file path for the snapshot after these actions, so the harness takes one itself
# and hands the model the page content (and its element refs) as the observation.
OBSERVE_AFTER = ("browser_navigate", "browser_click", "browser_type", "browser_fill_form", "browser_select_option")
MAX_RESULT_CHARS = 5000   # newest tool result, in full up to this size
OLD_RESULT_CHARS = 300    # older tool results are cut to this


@dataclass
class Step:
    """One tool call of the exploration agent: the tool, its arguments, the result and any text from the model."""

    n: int
    tool: str | None = None
    args: dict | None = None
    result: str = ""
    note: str = ""        # model's text for this step


@dataclass
class AgentRun:
    """A finished agent run: the steps, the final answer, why it stopped (`done` or `max_steps`) and how often it
    had to be nudged to call a tool.
    """

    steps: list[Step] = field(default_factory=list)
    final: str = ""
    stopped: str = ""     # "done" | "max_steps"
    nudges: int = 0       # times we had to tell the model to call a tool instead of writing a plan

NUDGE = ("Do not describe a plan. You have not looked at the page yet. Call exactly one tool now "
         "(start with browser_navigate), then wait for its result.")
MAX_NUDGES = 2


def to_ollama_tools(mcp_tools, allowed=ALLOWED_TOOLS) -> list[dict]:
    return [
        {"type": "function", "function": {"name": t.name, "description": (t.description or "").split("\n")[0],
                                           "parameters": t.input_schema}}
        for t in mcp_tools if t.name in allowed
    ]


_ALIASES = ("ref", "id", "element_ref", "element_id", "selector", "element")


def repair_args(args: dict, schema: dict) -> dict:
    """Fix argument names a small model gets wrong, using the tool's JSON schema.

    - drops arguments the schema does not know (the server rejects them);
    - if a required argument is missing, fills it from a common alias (`id`, `ref`, `selector`, ...).
    """
    props = (schema or {}).get("properties", {})
    if not props:
        return args
    fixed = {k: v for k, v in args.items() if k in props}
    for req in (schema or {}).get("required", []):
        if req not in fixed:
            alias = next((a for a in _ALIASES if a in args and a not in props), None)
            if alias:
                fixed[req] = args[alias]
    return fixed


def parse_text_tool_call(text: str, allowed=ALLOWED_TOOLS) -> dict | None:
    """llama-style models often write a tool call as JSON text instead of using the tool-call channel."""
    for m in re.finditer(r"\{.*\}", text or "", re.DOTALL):
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        args = data.get("parameters", data.get("arguments"))
        if data.get("name") in allowed and isinstance(args, dict):
            return {"name": data["name"], "arguments": args}
    return None


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
    schemas = {t["function"]["name"]: t["function"].get("parameters") for t in tools}
    messages = [{"role": "system", "content": system}, {"role": "user", "content": task}]
    run = AgentRun()
    for n in range(1, max_steps + 1):
        reply = llm_chat(messages, tools)
        calls = reply.get("tool_calls") or []
        if not calls:
            parsed = parse_text_tool_call(reply.get("content") or "")
            if parsed:
                calls, reply = [parsed], {**reply, "content": ""}
        messages.append({"role": "assistant", "content": reply.get("content") or "",
                         **({"tool_calls": [{"function": c} for c in calls]} if calls else {})})
        if not calls:
            if not run.steps and run.nudges < MAX_NUDGES:  # small models often "plan" in prose before ever acting
                run.nudges += 1
                messages.append({"role": "user", "content": NUDGE})
                continue
            run.final, run.stopped = reply.get("content") or "", "done"
            return run
        for c in calls:
            name, raw_args = c["name"], c.get("arguments") or {}
            args = repair_args(raw_args, schemas.get(name))
            step = Step(n=n, tool=name, args=args, note=reply.get("content") or "")
            if args != raw_args:
                step.note = (step.note + f" [args repaired from {json.dumps(raw_args)}]").strip()
            if name not in ALLOWED_TOOLS:
                step.result = f"Error: tool {name} is not allowed."
            else:
                try:
                    step.result = await call(name, args)
                    if name in OBSERVE_AFTER and not step.result.lstrip().startswith("### Error"):
                        step.result = await call("browser_snapshot", {})
                    step.result = step.result[:MAX_RESULT_CHARS]
                except Exception as e:  # a bad tool call should be shown to the model, not crash the run
                    step.result = f"Error: {type(e).__name__}: {e}"
            run.steps.append(step)
            messages.append({"role": "tool", "content": step.result, "tool_name": name})
        shorten_old_results(messages)
    run.stopped = "max_steps"
    return run


def render_transcript(run: AgentRun, title: str, task: str) -> str:
    """Render an agent run as a markdown transcript (results are cut to 700 characters)."""
    lines = [f"# {title}", "", f"**Task:** {task}", "",
             f"Steps: {len(run.steps)}, stopped: {run.stopped}, nudges: {run.nudges}", ""]
    for s in run.steps:
        lines += [f"## Step {s.n}: `{s.tool}`", "", f"Args: `{json.dumps(s.args)}`", ""]
        if s.note:
            lines += [f"Model said: {s.note}", ""]
        snippet = s.result if len(s.result) < 700 else s.result[:700] + "\n...[truncated]"
        lines += ["```", snippet, "```", ""]
    lines += ["## Final answer", "", run.final or "(none)", ""]
    return "\n".join(lines)
