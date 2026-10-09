# QAForge-AI: 60-Day Daily Build Plan

> Learn AI for testing, testing of AI, and security of AI by building one open-source project, committing every day.

**Name options (pick one, then find/replace in this file):**
`QAForge-AI` (default) · `TestPilot-AI` · `AssureLab` · `QualityLens-AI` · `Sentinel-QA`

**Duration:** 60 working days (about 12 weeks at 5 days/week, or 60 calendar days if daily).
**Daily load:** 4-5 small tasks (about 2-3 hours). Finish them, then commit. That is a "done" day.

---

## Ground rules

1. One day = one commit minimum, but prefer several small, logical commits per day (one per task or feature) for a clean history. The commit message listed for a day is used for the final/summary commit.
2. Notes go in `docs/notes/dayNN.md` (3-5 lines: what I learned, what broke).
3. If a day overruns, finish it tomorrow and shift the plan. Never skip the commit.
4. Everything uses free/open-source tools. Local LLMs via **Ollama** (no API cost). A paid API key is optional.

## Decision log

Critical decisions are asked before building and recorded here.

| Date | Decision | Choice | Notes |
|---|---|---|---|
| 2026-10-05 | Project name | **QAForge-AI** | Matches GitHub repo |
| 2026-10-05 | Env tooling | **uv** (not plain venv+pip) | Installed via Homebrew; `uv sync`, `uv add`, `uv run`. Python 3.11 |
| 2026-10-05 | License | **Deferred** to Day 59 | |
| 2026-10-05 | Git workflow | **Branch per phase**, push daily to that branch, merge to `main` when the phase is complete | Branches: `phase-1-foundations`, `phase-2-ai-testgen`, ... Tag releases on `main` |
| 2026-10-07 | Test user for account tests | **Fresh user per run** | Registered in a session fixture with a unique username; each xdist worker registers its own |
| 2026-10-07 | Playwright fixtures | **Own fixtures**, not the pytest-playwright plugin | Keeps control and avoids name clashes; revisit if the plugin's tracing/screenshot options are wanted |
| 2026-10-06 | Git identity | `Raman Walia <walia.raman89@gmail.com>` | Set in repo-local git config |
| 2026-10-07 | Commit granularity | **Multiple small commits per day** | One per task where practical, each passing tests; push at end of day |
| 2026-10-09 | Local model | **llama3.1:8b** + nomic-embed-text | Default from plan; swap via `OLLAMA_MODEL` |
| 2026-10-05 | Remote | `https://github.com/ramanwaliagithub/QAForge-AI.git` | |

## Open-source stack

| Area | Tools |
|---|---|
| Language/test | Python 3.11+, pytest, pytest-playwright, pytest-xdist, allure-pytest |
| App under test | ParaBank (public demo), plus a small RAG chatbot you build in Phase 5 |
| Local LLMs | Ollama (llama3.1, qwen2.5, nomic-embed-text) |
| AI-assisted testing | Playwright MCP, MCP Python SDK, Claude Code/Copilot (optional) |
| Evals | promptfoo, DeepEval, Ragas |
| Observability | Langfuse (self-hosted via Docker), OpenTelemetry |
| RAG | ChromaDB, sentence-transformers |
| Red teaming | garak, PyRIT, promptfoo red team |
| CI | GitHub Actions |

## Target repo structure

```
qaforge-ai/
├── README.md
├── PLAN.md
├── pyproject.toml
├── .github/workflows/
├── docs/notes/
├── framework/            # Phases 1-3: pytest + Playwright base, self-healing
├── ai_testgen/           # Phase 2: LLM test generation
├── mcp_servers/          # Phase 5: custom QA MCP server
├── rag_app/              # Phase 5: app under test for RAG evals
├── evals/                # Phase 4: golden datasets, DeepEval, Ragas, promptfoo
├── redteam/              # Phase 6: garak, PyRIT, injection suites
└── reports/
```

## Phase map

| Phase | Days | Focus | Tier |
|---|---|---|---|
| 1 | 1-5 | Setup and foundations | Base |
| 2 | 6-17 | AI test generation and self-healing (Playwright MCP) | 1 |
| 3 | 18-24 | AI-assisted development workflows | 1 |
| 4 | 25-37 | LLM evals | 1 |
| 5 | 38-47 | Agentic AI/MCP and RAG | 2 |
| 6 | 48-53 | AI red teaming and security | 2 |
| 7 | 54-60 | LLMOps, CI gates, capstone | 3 |

---

# PHASE 1: Setup and Foundations (Days 1-5)

### Day 1: Repo and environment
- [x] Create GitHub repo `qaforge-ai`, clone, open in VS Code
- [x] Create venv via uv, `pyproject.toml`, install pytest, playwright, python-dotenv
- [x] Add `.gitignore`, `.env.example`, README skeleton with project goal
- [x] Paste this PLAN.md into the repo root
- Commit: `chore: init repo, venv, plan`

### Day 2: Playwright + pytest baseline
- [x] `playwright install`, write first test against ParaBank login page
- [x] Add `conftest.py` with browser/page fixtures
- [x] Configure `pytest.ini` (markers: smoke, ai, eval, redteam)
- [x] Run headed and headless, note differences
- Commit: `test: first playwright test on ParaBank`

### Day 3: Page objects and structure
- [x] Create `framework/pages/` with LoginPage and AccountsPage
- [x] Add a base page with wait/click helpers
- [x] Write 3 tests using the page objects (login valid/invalid, open account)
- [x] Add pytest-xdist and run in parallel
- Commit: `feat: page object layer and parallel run`

### Day 4: Reporting and logging
- [x] Add allure-pytest, generate a report
- [x] Screenshot and trace on failure via conftest hook
- [x] Add structured logging helper
- [x] Save sample report screenshot to `docs/`
- Commit: `feat: allure reporting, failure artifacts`

### Day 5: Local LLM setup
- [x] Install Ollama, pull `llama3.1:8b` (or `qwen2.5:7b`) and `nomic-embed-text`
- [x] Call the model from Python (`ollama` package), print a response
- [x] Learn: temperature, system prompt, context window (write 5 lines in notes)
- [x] Create `framework/llm_client.py` wrapper (swap-able for a hosted API later)
- Commit: `feat: ollama client wrapper`

---

# PHASE 2: AI Test Generation and Self-Healing (Days 6-17)

### Day 6: Prompting for test cases
- [ ] Write a prompt that turns a user story into test scenarios (Given/When/Then)
- [ ] Run it on 3 ParaBank stories (transfer funds, bill pay, open account)
- [ ] Compare outputs across temperatures 0 and 0.8
- [ ] Save prompts in `ai_testgen/prompts/`
- Commit: `feat: prompt templates for scenario generation`

### Day 7: Structured outputs
- [ ] Define a Pydantic model `TestCase` (title, steps, expected, priority)
- [ ] Force JSON output and validate; add retry on invalid JSON
- [ ] Write unit tests for the parser using canned LLM responses
- [ ] Notes: why structured output beats free text
- Commit: `feat: structured testcase schema and parser`

### Day 8: From scenarios to pytest code
- [ ] Prompt that converts a `TestCase` into a pytest-playwright test using your page objects
- [ ] Generate tests into `ai_testgen/generated/`
- [ ] Run them; record pass/fail rate
- [ ] Log every failure reason in notes
- Commit: `feat: LLM test code generator v1`

### Day 9: Grounding with page context
- [ ] Extract page DOM/accessibility snapshot with Playwright
- [ ] Feed the snapshot to the prompt so locators are real, not guessed
- [ ] Compare pass rate vs Day 8
- [ ] Add a small token-size trimmer for large DOMs
- Commit: `feat: DOM-grounded generation`

### Day 10: Playwright MCP intro
- [ ] Install and run `@playwright/mcp` locally
- [ ] Connect it to VS Code (Copilot/Claude Code) or any MCP client
- [ ] Ask the agent to explore ParaBank and describe flows
- [ ] Save the transcript and observations in `docs/notes/`
- Commit: `docs: playwright mcp exploration notes`

### Day 11: MCP-driven exploratory testing
- [ ] Ask the agent to find 5 edge cases on the transfer funds page
- [ ] Convert two of its findings into real pytest tests by hand
- [ ] Note where the agent was wrong or flaky
- [ ] Add findings to `docs/mcp-findings.md`
- Commit: `test: edge cases found via playwright mcp`

### Day 12: Accessibility-snapshot based locators
- [ ] Learn role/label/text-based locators vs CSS/XPath
- [ ] Refactor 5 fragile locators in the page objects
- [ ] Add a locator-quality checklist to docs
- [ ] Re-run suite for stability
- Commit: `refactor: resilient locators`

### Day 13: Failure analysis (healing step 1)
- [ ] On test failure, capture error, DOM snapshot, screenshot
- [ ] Build `framework/healing/collector.py` to save these as JSON
- [ ] Deliberately break 3 locators to produce samples
- [ ] Write tests for the collector
- Commit: `feat: failure context collector`

### Day 14: Healing suggester
- [ ] Prompt the LLM with failure context to propose a new locator
- [ ] Validate the suggestion by checking it matches exactly one element
- [ ] Reject suggestions that match zero or many
- [ ] Measure: how many of your 3 broken locators were healed
- Commit: `feat: LLM locator suggestion with validation`

### Day 15: Safe self-healing loop
- [ ] Add a fixture that retries a step once with the healed locator
- [ ] Never auto-write to source; log proposals to `reports/healing.json`
- [ ] Add a flag `--heal` (off by default)
- [ ] Guard rail: skip healing for assertion failures (only locator failures)
- Commit: `feat: opt-in self-healing fixture`

### Day 16: Healing review report
- [ ] Generate a markdown/HTML report of proposed fixes (old vs new locator)
- [ ] Add confidence score and "approved/rejected" field
- [ ] Add a CLI `python -m framework.healing apply` that patches approved ones
- [ ] Try it end to end on a broken test
- Commit: `feat: healing review and apply CLI`

### Day 17: Phase 2 consolidation
- [ ] Run full suite with generated tests, record pass rate and healing rate
- [ ] Write `docs/phase2-results.md` with honest numbers and failure types
- [ ] Clean up code and add docstrings
- [ ] Tag release `v0.2-ai-testgen`
- Commit: `docs: phase 2 results, tag v0.2`

---

# PHASE 3: AI-Assisted Development Workflows (Days 18-24)

### Day 18: Specs that agents can execute
- [ ] Write a `specs/` folder format: goal, context, acceptance criteria, out of scope
- [ ] Write a spec for "BillPay page object + 5 tests"
- [ ] Give it to your AI coding tool; compare output to a vague prompt
- [ ] Notes: what made the spec work
- Commit: `docs: spec template and first spec`

### Day 19: Project context files
- [ ] Add `CLAUDE.md` / `.github/copilot-instructions.md` with conventions (naming, locators, no sleeps)
- [ ] Add a test-writing checklist
- [ ] Re-run Day 18 spec and compare quality
- [ ] Notes on what instructions had the most effect
- Commit: `docs: agent instruction files`

### Day 20: Reviewing AI-generated tests
- [ ] Build a review checklist (assertions meaningful? waits? independence? data?)
- [ ] Review the 5 generated tests from Day 18 against it
- [ ] List defects found (weak asserts, hardcoded data, hidden dependencies)
- [ ] Fix them by hand
- Commit: `docs: ai test review checklist, fixes`

### Day 21: Automated quality gates for generated code
- [ ] Add ruff + mypy (or pyright) config
- [ ] Add pre-commit hooks
- [ ] Add a custom check that bans `time.sleep` and empty assertions
- [ ] Run on all generated tests
- Commit: `chore: lint, type check, pre-commit, custom rules`

### Day 22: Test data with AI
- [ ] Generate realistic test data (names, accounts, amounts) via LLM with a schema
- [ ] Add Faker as the deterministic baseline; compare the two
- [ ] Create `framework/data/` factory with seeded randomness
- [ ] Notes: when AI data helps and when it hurts
- Commit: `feat: test data factory (faker + llm)`

### Day 23: AI bug report and triage helper
- [ ] Prompt: failure log + screenshot summary to a clear bug report
- [ ] Add duplicate detection by embedding similarity (nomic-embed-text)
- [ ] Run on 5 saved failures
- [ ] Save outputs in `reports/bugs/`
- Commit: `feat: ai bug report drafter`

### Day 24: Phase 3 consolidation
- [ ] Write `docs/ai-dev-workflow.md` (your personal playbook: what to delegate, what to review)
- [ ] Refactor anything messy
- [ ] Update README with architecture diagram (Mermaid)
- [ ] Tag `v0.3-workflow`
- Commit: `docs: ai dev workflow playbook, tag v0.3`

---

# PHASE 4: LLM Evals (Days 25-37)

### Day 25: Why LLM testing is different
- [ ] Notes: non-determinism, subjective quality, metrics vs assertions
- [ ] Build a tiny target: `rag_app/` stub or a simple FastAPI `/ask` endpoint backed by Ollama
- [ ] Write 5 plain pytest checks on it (status, schema, latency) and see why they are not enough
- [ ] Define quality dimensions: correctness, faithfulness, safety, consistency
- Commit: `feat: sample llm service under test`

### Day 26: Golden datasets
- [ ] Create `evals/datasets/qa_golden.jsonl` with 20 question/expected-answer pairs
- [ ] Add metadata (category, difficulty, source)
- [ ] Write a loader and validator
- [ ] Notes: how to grow and version a dataset
- Commit: `feat: golden dataset v1`

### Day 27: Deterministic checks
- [ ] Implement exact, contains, regex, JSON-schema, and length checks
- [ ] Run the 20 cases through your service and score them
- [ ] Output results to CSV
- [ ] Identify cases where deterministic checks fail unfairly
- Commit: `feat: deterministic eval checks`

### Day 28: LLM-as-judge
- [ ] Write a judge prompt with a rubric (1-5 with reasons)
- [ ] Use a different model as judge than the one being tested
- [ ] Judge your 20 outputs; manually score 10 and compare
- [ ] Notes: judge bias and how to reduce it
- Commit: `feat: llm-as-judge scorer`

### Day 29: promptfoo basics
- [ ] Install promptfoo, create `promptfooconfig.yaml`
- [ ] Define providers (Ollama), prompts, and test cases with assertions
- [ ] Run `promptfoo eval` and open the viewer
- [ ] Compare two prompt versions side by side
- Commit: `feat: promptfoo config and first eval`

### Day 30: DeepEval basics
- [ ] Install DeepEval, configure a local model as the judge
- [ ] Write pytest-style tests with `AnswerRelevancy` and `GEval`
- [ ] Run them inside pytest
- [ ] Compare scores with your Day 28 judge
- Commit: `feat: deepeval pytest integration`

### Day 31: Hallucination and faithfulness
- [ ] Add context-grounded cases (answer must come from provided text)
- [ ] Implement a faithfulness metric (DeepEval or custom)
- [ ] Add 5 "trap" questions whose answer is not in the context
- [ ] Record hallucination rate
- Commit: `feat: faithfulness and hallucination tests`

### Day 32: Consistency and robustness
- [ ] Run each question 5 times; measure variance
- [ ] Paraphrase questions (via LLM) and check answer stability
- [ ] Add typo and noisy-input variants
- [ ] Report a consistency score
- Commit: `feat: consistency and robustness suite`

### Day 33: Bias and safety checks
- [ ] Build a small paired-prompt set (same question, different names/groups)
- [ ] Compare answers for tone and content differences
- [ ] Add refusal tests for clearly harmful requests
- [ ] Add toxicity check (DeepEval or a small classifier)
- Commit: `feat: bias and safety eval cases`

### Day 34: Regression suite for prompts
- [ ] Create two prompt versions (v1, v2); run the full suite on both
- [ ] Build a comparison script that flags regressions per case
- [ ] Store results in `evals/results/` with timestamp and git sha
- [ ] Notes: what counts as a regression when output is probabilistic
- Commit: `feat: prompt regression comparison`

### Day 35: Ragas intro
- [ ] Install Ragas, configure a local judge
- [ ] Compute faithfulness, answer relevancy, context precision on 10 samples
- [ ] Compare with your own metrics
- [ ] Notes: which metric you trust and why
- Commit: `feat: ragas metrics`

### Day 36: Thresholds and pass criteria
- [ ] Define pass thresholds per metric (e.g. faithfulness >= 0.8)
- [ ] Implement pass/fail logic using aggregate scores, not single cases
- [ ] Add confidence handling (re-run flaky cases N times)
- [ ] Write `evals/README.md` explaining the strategy
- Commit: `feat: eval thresholds and gating logic`

### Day 37: Phase 4 consolidation
- [ ] Generate a combined eval report (HTML or markdown)
- [ ] Update main README with eval results
- [ ] Review all eval code; add tests for scorers
- [ ] Tag `v0.4-evals`
- Commit: `docs: eval report, tag v0.4`

---

# PHASE 5: Agentic AI, MCP and RAG (Days 38-47)

### Day 38: Tool calling basics
- [ ] Implement function/tool calling with Ollama (or a hosted API)
- [ ] Create 2 tools: `get_account_balance` (mock) and `run_test`
- [ ] Log the model's tool choices and arguments
- [ ] Notes: where tool calls go wrong
- Commit: `feat: tool calling demo`

### Day 39: Build an MCP server
- [ ] Install the MCP Python SDK
- [ ] Build `mcp_servers/qa_server.py` exposing tools: `list_tests`, `run_test`, `get_last_report`
- [ ] Test with the MCP Inspector
- [ ] Document tool schemas
- Commit: `feat: qa mcp server v1`

### Day 40: Use your MCP server from an agent
- [ ] Connect the server to VS Code / Claude Code / another MCP client
- [ ] Ask: "run smoke tests and summarize failures"
- [ ] Add a `read_failure_artifacts` tool
- [ ] Record what the agent did well and badly
- Commit: `feat: mcp tools for failure artifacts`

### Day 41: Simple QA agent loop
- [ ] Build a minimal agent: plan, call tools, observe, stop (max steps)
- [ ] Task: "run failing tests, classify failures as product bug / flaky / locator"
- [ ] Add step limit and timeout guards
- [ ] Log every step to JSONL
- Commit: `feat: qa triage agent loop`

### Day 42: Testing the agent
- [ ] Write eval cases for the triage agent (known failures with expected class)
- [ ] Check tool-call correctness, not only final answer
- [ ] Add a trajectory assertion (e.g. must call `read_failure_artifacts` before classifying)
- [ ] Measure accuracy
- Commit: `test: agent trajectory and accuracy evals`

### Day 43: RAG foundations
- [ ] Notes: embeddings, chunking, top-k, reranking
- [ ] Install ChromaDB and sentence-transformers
- [ ] Ingest 10 documents (ParaBank docs or your own markdown) with 2 chunk sizes
- [ ] Query and inspect retrieved chunks
- Commit: `feat: chroma ingestion pipeline`

### Day 44: Build the RAG app under test
- [ ] Wire retrieval to Ollama generation in `rag_app/`
- [ ] Expose `/ask` returning answer plus sources
- [ ] Add a few intentionally weak settings (big chunks, low top-k) to break later
- [ ] Smoke test it
- Commit: `feat: rag app v1`

### Day 45: Retrieval quality tests
- [ ] Build a retrieval test set (question to expected source doc)
- [ ] Compute hit rate and MRR
- [ ] Compare two chunk sizes and top-k values
- [ ] Notes: retrieval failures vs generation failures
- Commit: `test: retrieval quality metrics`

### Day 46: End-to-end RAG evals
- [ ] Run DeepEval/Ragas on the full RAG app
- [ ] Add "no answer in docs" cases (should say it does not know)
- [ ] Add citation check (answer cites a real retrieved source)
- [ ] Report hit rate, faithfulness, and abstention rate
- Commit: `test: end-to-end rag evals`

### Day 47: Phase 5 consolidation
- [ ] Draw architecture (Mermaid) of MCP server, agent, and RAG app
- [ ] Update README with results
- [ ] Clean and test the code
- [ ] Tag `v0.5-agents-rag`
- Commit: `docs: architecture, tag v0.5`

---

# PHASE 6: AI Red Teaming and Security (Days 48-53)

> Only test systems you own. Use your local `rag_app/` and agent as targets.

### Day 48: OWASP Top 10 for LLM applications
- [ ] Read the OWASP LLM Top 10; write a one-line summary of each in notes
- [ ] Map each risk to your RAG app and agent (applies / does not apply)
- [ ] Create `redteam/threat-model.md`
- [ ] Pick the top 4 risks to test
- Commit: `docs: llm threat model`

### Day 49: Prompt injection tests
- [ ] Write direct injection cases (ignore instructions, reveal system prompt)
- [ ] Write indirect injection: plant instructions inside an ingested document
- [ ] Run against `rag_app/`; record success rate
- [ ] Save as a reusable pytest suite in `redteam/`
- Commit: `test: prompt injection suite`

### Day 50: Data leakage and excessive agency
- [ ] Test whether the system prompt or private docs can be extracted
- [ ] Test whether the agent can be tricked into calling a tool it should not
- [ ] Add allow-list and confirmation guard to the MCP server's risky tool
- [ ] Re-test after the fix
- Commit: `fix: tool guard rails, leakage tests`

### Day 51: Automated scanning with garak
- [ ] Install garak, point it at your local model/endpoint
- [ ] Run a limited probe set (promptinject, encoding, leakreplay)
- [ ] Review the report; note false positives
- [ ] Save the summary in `reports/`
- Commit: `chore: garak scan and summary`

### Day 52: promptfoo red team + PyRIT intro
- [ ] Run `promptfoo redteam` against your app with a few plugins
- [ ] Try a basic PyRIT orchestrator (multi-turn attack) on the local model
- [ ] Compare findings across tools
- [ ] Note which found unique issues
- Commit: `chore: promptfoo redteam and pyrit experiments`

### Day 53: Phase 6 consolidation
- [ ] Add mitigations (input filtering, output checks, stricter system prompt) and re-run
- [ ] Write `docs/redteam-report.md` (before/after numbers)
- [ ] Add a `redteam` pytest marker to the suite
- [ ] Tag `v0.6-redteam`
- Commit: `docs: redteam report, tag v0.6`

---

# PHASE 7: LLMOps, CI Gates and Capstone (Days 54-60)

### Day 54: CI for the classic suite
- [ ] Create GitHub Actions workflow: lint, type check, smoke tests, upload allure/trace artifacts
- [ ] Cache pip and Playwright browsers
- [ ] Add a status badge to README
- [ ] Make it pass on a PR
- Commit: `ci: github actions for tests and lint`

### Day 55: Eval gate in CI
- [ ] Add a workflow job that runs a small eval subset (use a tiny model or mocked judge for CI speed)
- [ ] Fail the build if metrics fall below thresholds
- [ ] Post a summary table to the PR (job summary)
- [ ] Test by degrading a prompt and watching the gate fail
- Commit: `ci: eval quality gate`

### Day 56: Observability with Langfuse
- [ ] Run Langfuse via Docker Compose
- [ ] Instrument the RAG app and agent for traces
- [ ] Inspect a slow or bad trace; note cost/latency per step
- [ ] Add trace IDs into eval reports
- Commit: `feat: langfuse tracing`

### Day 57: Cost, latency and drift tracking
- [ ] Record latency and token counts per eval run
- [ ] Store history in a CSV/SQLite; plot a trend chart
- [ ] Add a "model changed" comparison (swap the Ollama model, compare scores)
- [ ] Notes: how you would detect drift in production
- Commit: `feat: eval history and model comparison`

### Day 58: Capstone integration
- [ ] One command (`make demo` or a script) that: generates tests, runs them, heals, evals the RAG app, runs red-team subset, builds a report
- [ ] Fix integration bugs
- [ ] Record a short terminal demo (asciinema or GIF)
- [ ] Update README quick start
- Commit: `feat: end-to-end demo pipeline`

### Day 59: Documentation and portfolio polish
- [ ] Finalize README: problem, architecture, results, limits, how to run
- [ ] Write `docs/lessons-learned.md` (honest failures and trade-offs)
- [ ] Add LICENSE and CONTRIBUTING
- [ ] Add 3 screenshots (allure, promptfoo viewer, Langfuse trace)
- Commit: `docs: final readme, lessons learned, license`

### Day 60: Release and story
- [ ] Tag `v1.0`
- [ ] Draft a LinkedIn post and a 2-minute interview walkthrough (problem, design, numbers, trade-offs)
- [ ] Add the project to your resume with 3 measurable bullets from your own results
- [ ] Plan next steps (more apps, more evals, contribute to promptfoo/DeepEval)
- Commit: `release: v1.0`

---

## Quick reference: daily routine

1. `git pull` and open today's section.
2. Do the 4-5 tasks; write 3-5 lines in `docs/notes/dayNN.md`.
3. `pytest -q` (or the relevant suite) must run before the commit.
4. `git add -A && git commit -m "<message>" && git push`
5. Tick the checkboxes in this file (it is part of the commit).

## If you fall behind

- Protect the core: Days 6-17 (AI test generation), 25-37 (evals), and 48-53 (red teaming).
- Compress Phase 3 (Days 18-24) to 3 days and Phase 7 to 4 days. That gives a **minimum 50-day path**.
