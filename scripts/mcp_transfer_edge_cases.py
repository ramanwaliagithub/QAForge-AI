"""Exploratory testing of Transfer Funds: LLM proposes edge cases, MCP executes them, we compare.

Usage: uv run python -m scripts.mcp_transfer_edge_cases
Writes docs/mcp-findings.md and reports/mcp_edge_cases.json.
"""
import asyncio
import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

from ai_testgen.edge_cases import classify_outcome, expects_rejection, propose_edge_cases
from ai_testgen.mcp_flows import McpActionError, account_options, act, goto, open_account, page_texts, register
from ai_testgen.mcp_session import find_ref, playwright_mcp
from framework.llm_client import get_client

load_dotenv()
BASE = os.getenv("BASE_URL", "http://localhost:8080/parabank")
REPEATS = 2


async def run_case(session, case, accounts):
    snap = await goto(session, f"{BASE}/transfer.htm")
    try:
        if case.amount:
            snap = await act(session, "browser_type", {"target": find_ref(snap, "textbox"), "text": case.amount})
        snap = await act(session, "browser_select_option",
                         {"target": find_ref(snap, "combobox", nth=0), "values": [accounts[case.from_index]]})
        snap = await act(session, "browser_select_option",
                         {"target": find_ref(snap, "combobox", nth=1), "values": [accounts[case.to_index]]})
        snap = await act(session, "browser_click", {"target": find_ref(snap, "button", "Transfer")})
    except McpActionError as e:
        return "tool-error", [str(e)[:200]]
    texts = page_texts(snap)
    return classify_outcome(texts), texts[:4]


async def main():
    client = get_client()
    async with playwright_mcp() as session:
        await register(session, BASE, f"edge_{uuid.uuid4().hex[:8]}")
        accounts = await open_account(session, BASE, "SAVINGS")
        assert len(accounts) == 2, f"expected 2 accounts, got {accounts}"
        snapshot = await goto(session, f"{BASE}/transfer.htm")
        proposal = propose_edge_cases(client, snapshot, n=5)
        cases = proposal.cases

        rows = []
        for case in cases:
            runs = [await run_case(session, case, accounts) for _ in range(REPEATS)]
            outcomes = [r[0] for r in runs]
            rows.append({
                "title": case.title, "amount": case.amount, "from": case.from_index, "to": case.to_index,
                "expected": case.expected, "model_expects": "rejected" if expects_rejection(case.expected) else "accepted",
                "outcomes": outcomes, "stable": len(set(outcomes)) == 1, "page_text": runs[0][1],
            })

    Path("reports").mkdir(exist_ok=True)
    Path("reports/mcp_edge_cases.json").write_text(json.dumps({"cases": rows, "infeasible_proposals": proposal.rejected}, indent=2) + "\n")
    wrong = [r for r in rows if r["outcomes"][0] != r["model_expects"]]
    print(f"infeasible proposals dropped: {[r['item'].get('title') for r in proposal.rejected]}")
    print(f"{len(rows)} cases; model's expectation matched the app in {len(rows) - len(wrong)}; flaky: {sum(not r['stable'] for r in rows)}")
    for r in rows:
        print(f"- {r['title']!r} amount={r['amount']!r} from={r['from']} to={r['to']} | model expects {r['model_expects']} | app {r['outcomes']}")
        print(f"    {r['page_text']}")


asyncio.run(main())
