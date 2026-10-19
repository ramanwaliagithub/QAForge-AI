# Day 10: Playwright MCP intro

## Setup
- `@playwright/mcp` (v0.0.83) runs with `npx -y @playwright/mcp@latest --headless --isolated`. It is a stdio MCP server exposing 25 browser tools (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`, `browser_select_option`, `browser_find`, `browser_network_requests`, ...).
- For any MCP-capable editor or client the config is: `{"mcpServers": {"playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}}}`.
- I connected from **Python** with the MCP SDK (`ai_testgen/mcp_session.py`) instead of an editor, so the whole thing is scriptable and testable. Writing the client myself also shows what the protocol looks like: `initialize`, `list_tools`, `call_tool`.
- The server writes `.playwright-mcp/` (snapshots, console logs) in the working directory; git-ignored.

## How the MCP "sees" a page (the important idea)
- Tools act on **element refs** from an accessibility snapshot (YAML with `[ref=e12]`), not on CSS selectors. Refs inside frames are prefixed (`f1e34`), which broke my first parser.
- After `navigate`/`click` the server returns only a **file path** to the snapshot, not its content; you must call `browser_snapshot` to get the content. There is no inline option (`--snapshot-mode` is only `full`/`none`).
- ParaBank's inputs are unnamed in the snapshot (`textbox [ref=..]`), so they are found by order, the same weakness that hurt label-based generation on Day 9.

## Exploration by a local LLM agent (llama3.1:8b + MCP): did not work
Transcript: `day10-explore-transcript.md` (final attempt). Four iterations of the harness, each fixing the previous failure:
1. **Planned instead of acting:** 0 tool calls, invented refs (`e1`, `e11`) for pages it never saw. Fix: nudge it to call a tool.
2. **Never saw the page:** `navigate` returns a file path only. Fix: the harness takes a snapshot after every page-changing action and gives that to the model.
3. **Wrong argument names** (`selector`/`id` instead of `target`), then wrote a tool call as plain text. Fix: parse text tool calls; repair arguments against the tool schema.
4. **Still wrong:** it passes CSS-like strings (`link:contains('Register')`, `a:contains('Register')`) instead of the refs it was shown, and finally calls a tool that does not exist (`browser_fill`).

Lesson: a small local model can read the snapshot but cannot reliably do ref-based tool calling, even with a forgiving harness. The harness (`ai_testgen/explore_agent.py`: step limit, tool allowlist, shortened old results, nudge, argument repair; 13 unit tests) is reusable for the Day 41 agent. Likely fixes there: a bigger model, or hiding refs behind simple tools such as `click_link("Register")` implemented by our own MCP server (Day 39).

## Exploration that worked: deterministic walkthrough
`scripts/mcp_walkthrough.py` finds refs itself (`find_ref(snapshot, "link", "Register")`) and drives the real server: register a customer, visit all 7 menu pages, log out. **12 tool calls, 0 errors.** Result: `day10-mcp-walkthrough.md` (digest per page: headings, control counts, buttons).

Flows seen: registration (auto-login), open new account (type + funding account), accounts overview, transfer funds, bill pay (9 textboxes + from-account), find transactions (4 search methods: id, date, date range, amount), update contact info (7 fields), request loan, log out.

## "Ask the agent to describe flows"
`scripts/mcp_describe_flows.py` gives the digest to llama3.1:8b: `day10-llm-flow-summary.md`. Checked against the walkthrough:
- Correct: registration, open account, transfer, bill pay, update info, loan; it said the digest does not show how to navigate between pages (true: my digest omitted the menu links).
- Wrong or thin: "Find Transactions by date range" only. The page has 4 search methods, but my digest kept only 6 paragraphs and 4 identically named buttons. It faithfully repeated a lossy input. It also missed Accounts Overview and log out, and listed "Login" which the walkthrough did not exercise.
- Takeaway: LLM summaries are only as good as the digest. For Day 11 (edge cases on transfer funds) give the model the real snapshot of the page, not a digest.

## Next (Day 11)
Find 5 edge cases on Transfer Funds, convert 2 to real pytest tests by hand, and log where the agent was wrong or flaky in `docs/mcp-findings.md`.
