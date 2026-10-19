"""Deterministic walkthrough of ParaBank through Playwright MCP; writes a flow map.

Registers a customer, visits each menu page and records a digest per page.
Usage: uv run python -m scripts.mcp_walkthrough
"""
import asyncio
import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

from ai_testgen.mcp_session import find_ref, playwright_mcp, result_text, summarize_snapshot

load_dotenv()
BASE = os.getenv("BASE_URL", "http://localhost:8080/parabank")
OUT = Path("docs/notes/day10-mcp-walkthrough.md")
RAW = Path("reports/tmp/mcp")            # raw snapshots, git-ignored
MENU = ["Open New Account", "Accounts Overview", "Transfer Funds", "Bill Pay", "Find Transactions",
        "Update Contact Info", "Request Loan"]
FIELDS = ["First Name", "Last Name", "Address", "City", "State", "Zip Code", "Phone #", "SSN",
          "Username", "Password", "Confirm"]
VALUES = ["Mcp", "Explorer", "1 Test Street", "Testville", "CA", "90210", "5550100", "123-45-6789"]


async def main():
    user = f"mcp_{uuid.uuid4().hex[:8]}"
    values = VALUES + [user, "Passw0rd!", "Passw0rd!"]
    log, pages = [], []
    RAW.mkdir(parents=True, exist_ok=True)

    async with playwright_mcp() as s:
        async def act(tool, args, label):
            res = result_text(await s.call_tool(tool, args))
            snap = result_text(await s.call_tool("browser_snapshot", {}))
            (RAW / f"{len(log) + 1:02d}_{label.replace(' ', '_')}.yml").write_text(snap)
            err = "Error" if res.lstrip().startswith("### Error") else "ok"
            log.append({"step": len(log) + 1, "tool": tool, "label": label, "args": args, "result": err})
            return snap

        snap = await act("browser_navigate", {"url": f"{BASE}/index.htm"}, "open home")
        pages.append(("Home (logged out)", summarize_snapshot(snap)))

        snap = await act("browser_click", {"target": find_ref(snap, "link", "Register")}, "click Register")
        pages.append(("Registration form", summarize_snapshot(snap)))

        boxes = [find_ref(snap, "textbox", nth=i) for i in range(len(FIELDS) + 2)]
        # the page has 2 login textboxes (username, password) before the 11 registration fields
        fields = [{"name": FIELDS[i], "type": "textbox", "target": boxes[i + 2], "value": values[i]} for i in range(len(FIELDS))]
        snap = await act("browser_fill_form", {"fields": fields}, "fill registration form")
        snap = await act("browser_click", {"target": find_ref(snap, "button", "Register")}, "submit registration")
        pages.append(("After registration", summarize_snapshot(snap)))

        for item in MENU:
            snap = await act("browser_click", {"target": find_ref(snap, "link", item)}, f"menu {item}")
            pages.append((item, summarize_snapshot(snap)))

        snap = await act("browser_click", {"target": find_ref(snap, "link", "Log Out")}, "log out")
        pages.append(("After log out", summarize_snapshot(snap)))

    lines = ["# ParaBank flow map from a Playwright MCP walkthrough", "",
             f"Driven by `scripts/mcp_walkthrough.py` through the MCP server (new user `{user}`), {len(log)} tool calls.", "",
             "## Tool calls", "", "| # | tool | what | result |", "|---|---|---|---|"]
    lines += [f"| {e['step']} | `{e['tool']}` | {e['label']} | {e['result']} |" for e in log]
    lines += ["", "## Pages", ""]
    for name, d in pages:
        lines += [f"### {name}", "", f"- URL: `{d['url']}`  Title: {d['title']}",
                  f"- Headings: {d['headings'] or '-'}",
                  f"- Controls: {d['textboxes']} textboxes, {d['comboboxes']} dropdowns, buttons {d['buttons'] or '-'}",
                  f"- Text: {d['text'] or '-'}", ""]
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT}; errors: {sum(e['result'] == 'Error' for e in log)}/{len(log)}")
    print(json.dumps([e for e in log if e["result"] == "Error"], indent=1)[:800])


asyncio.run(main())
