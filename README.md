# QAForge-AI

Learn AI for testing, testing of AI, and AI security by building one open-source project in 60 days.

## Goals

1. **AI for testing**: LLM-generated tests, MCP-driven exploration, self-healing locators.
2. **Testing of AI**: evals for LLM apps, RAG and agents (golden sets, judges, thresholds).
3. **Security of AI**: prompt injection, leakage and red-teaming of a local RAG app and agent.

See [PLAN.md](PLAN.md) for the day-by-day plan and decision log.

## Setup

```bash
uv sync                       # creates .venv and installs dependencies
docker compose up -d          # local ParaBank on http://localhost:8080/parabank
cp .env.example .env
uv run playwright install     # from Day 2
uv run pytest -q
```

## Status

Day 14 of 60: LLM locator suggestion with validation.

## Reports

```bash
uv run pytest -n 3                                  # writes allure-results/
allure generate allure-results -o allure-report --clean
allure open allure-report
```
Requires the Allure CLI (`brew install allure`).

## Local LLM

```bash
brew install ollama && ollama serve        # in another terminal
ollama pull llama3.1:8b && ollama pull nomic-embed-text
uv run python -m scripts.llm_hello
```

## Self-healing (opt-in)

```bash
uv run pytest --heal            # a broken locator in a page object is healed at run time (needs Ollama running)
```

- Off by default. With `--heal`, a click/fill/select that fails because its **locator** is wrong asks a local LLM for a
  replacement, validates it on the live page (exactly one match, right kind of element), and retries the action **once**.
- Assertion failures are never healed. Source files are never edited: proposals go to `reports/healing.json` for review.
- A test that only passed because of a heal is reported, not hidden: a `HealedLocatorWarning` (use
  `-W error::framework.healing.plugin.HealedLocatorWarning` to make CI fail on heals) plus a "self-healing" summary section.
- Flags: `--heal-allow-maybe` (also try ambiguous failures), `--heal-max-per-test N`. Details: `docs/notes/day15.md`.
