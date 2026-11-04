# Copilot instructions for QAForge-AI

pytest + Playwright (sync API) UI tests for ParaBank (local Docker, http://localhost:8080/parabank). The full version, with reasons, is `CLAUDE.md`; the
checklist is `docs/test-writing-checklist.md`. The rule ids below are the same in all three files.

## Run
- `uv run pytest -n 3` and `uv run pytest` must both pass; add `--reruns=0` to judge stability. Pass options as `--opt=value`, never `--opt value`.

## Page objects (`framework/pages/`)
- [P1] One `BasePage` subclass per page in `<name>_page.py`, exported from `framework/pages/__init__.py`; locators are properties; actions return `self`.
- [P2] Act only through `self.click`, `self.fill`, `self.select_option` (self-healing hooks in there).
- [P3] No assertions about product behaviour in a page object.
- [P4] Copy `transfer_page.py` and `tests/test_transfer_edge_cases.py`.

## Locators
- [L1] `get_by_role(name=...)` > label/text > form `name` attribute > hand-written `#id` > other CSS. Never generated ids, classes, XPath, `.nth()`, `.first`, `.last`.
- [L2] No accessible name? Try a labelled container (a ParaBank form field sits in a table row named by its label) before `name` or an id.
- [L3] Register every non-semantic selector in `ACCEPTED` in `tests/test_locator_quality.py` with a reason.
- [L4] A locator matches exactly one element, also while errors show. Repeated text breaks strict mode: count it.
- [L5] `exact=True` for a button or link whose name is a prefix of another.

## Tests
- [T1] `test_<behaviour>_<expected outcome>`; one behaviour per test.
- [T2] `expect(locator).to_...`; never `time.sleep` or `wait_for_timeout`.
- [T3] Assert the exact text the app shows. Never invent a message.
- [T4] A rejection test checks the message and that nothing happened (no confirmation, no request, no balance change).
- [T5] Tables and dropdowns load asynchronously: wait with `expect(...).to_have_count(...)` before reading text.
- [T6] Independent tests. `logged_in_page` is shared (never change its balance); `new_customer_page` is a fresh customer with one account.
- [T7] Data constants once per module; read balances and account numbers from the UI.
- [T8] Never write a passing test that depends on a known ParaBank bug; use `xfail(strict=True, raises=AssertionError)`.
- [T9] Break the test on purpose once and see it fail for the right reason.

## Code and done
- [C1] Docstrings: modules, public classes, public functions of 8+ lines in `framework/`, `scripts/`, `ai_testgen/`, `conftest.py`.
- [C2] pyflakes clean; every `.py` parses. [C3] No new dependency unless asked.
- [D1] Run the new tests with `--reruns=0` serially and with `-n 3`, plus the four repo checks, and say what you did not run.
- [D2] Change only the files the task needs. [D3] Given a spec, its Deliverables and Out of scope bind you.
