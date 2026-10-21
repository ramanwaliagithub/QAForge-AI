# Day 11
- Full findings and the model-vs-app table are in `docs/mcp-findings.md`.
- Pipeline: LLM proposes edge cases from the real page snapshot -> `scripts/mcp_transfer_edge_cases.py` executes them through Playwright MCP (twice each) -> compare model expectation with actual outcome.
- Biggest result: ParaBank accepts negative amounts and has no overdraft check ($1,000,000 transfer leaves the source at -$999,584.50). Both are now strict-xfail tests, so they flip loudly when fixed.
- The LLM was useful for ideas but unreliable as an oracle: wrong on the decimal case, used identical boilerplate for 4 of 5 expectations, proposed impossible "non-existent account" cases every run, and never thought of the balance check. A human (or ground-truth rules) must decide expected behaviour.
- Item-by-item validation of LLM output beat all-or-nothing: one infeasible item no longer discards the whole answer.
- Money-moving tests need isolation: new `new_customer_page` fixture registers a fresh customer per test.
