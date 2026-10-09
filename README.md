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
cp .env.example .env
uv run playwright install     # from Day 2
uv run pytest -q
```

## Status

Day 5 of 60: local LLM setup (Phase 1 complete).

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
