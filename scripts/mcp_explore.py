"""Let a local LLM explore ParaBank through Playwright MCP and save the transcript.

Usage: uv run python -m scripts.mcp_explore [output.md]
"""
import asyncio
import os
import sys
import uuid
from pathlib import Path

import ollama
from dotenv import load_dotenv

from ai_testgen.explore_agent import render_transcript, run_agent, to_ollama_tools
from ai_testgen.mcp_session import playwright_mcp

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080/parabank")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/notes/day10-explore-transcript.md")

SYSTEM = (
    "You are a QA engineer exploring a web banking app by calling browser tools. "
    "ALWAYS respond with a tool call, never with a plan. Call one tool at a time and wait for its result. "
    "Element refs (like e12) exist only in a page snapshot you have actually received; never invent them. "
    "When you have explored enough, stop calling tools and write a short bulleted summary of the user flows you saw."
)
USERNAME = f"explore_{uuid.uuid4().hex[:8]}"
TASK = (
    f"Explore ParaBank at {BASE_URL}/index.htm. 1) Register a new customer (link 'Register'); use any plausible values "
    f"for all fields, username '{USERNAME}', password 'Passw0rd!'. 2) After registering, look at the left-hand menu and visit "
    "'Open New Account' and 'Transfer Funds'. 3) Then describe the main user flows and what each page lets a user do."
)

client = ollama.Client()


def llm_chat(messages, tools):
    resp = client.chat(model=MODEL, messages=messages, tools=tools, options={"temperature": 0, "num_ctx": 16384})
    msg = resp["message"]
    calls = [{"name": c["function"]["name"], "arguments": c["function"]["arguments"]} for c in (msg.get("tool_calls") or [])]
    return {"content": msg.get("content") or "", "tool_calls": calls}


async def main():
    async with playwright_mcp() as session:
        tools = to_ollama_tools((await session.list_tools()).tools)
        run = await run_agent(llm_chat, session, tools, SYSTEM, TASK, max_steps=25)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_transcript(run, f"Exploration transcript ({MODEL} via Playwright MCP)", TASK))
    print(f"steps={len(run.steps)} stopped={run.stopped} -> {OUT}")
    print(run.final[:1500])


asyncio.run(main())
