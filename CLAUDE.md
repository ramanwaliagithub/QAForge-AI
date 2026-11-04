# QAForge-AI: instructions for coding agents

pytest + Playwright (sync API) UI tests for ParaBank, with AI-assisted testing tools around them. Follow these rules and run
`docs/test-writing-checklist.md` before you say a test is done. Every rule comes from a mistake made in this repo; the reason is in the rule.

## Run it
- ParaBank must be up (`docker compose up -d`, http://localhost:8080/parabank). `uv sync` once.
- `uv run pytest -n 3` (parallel) and `uv run pytest` (serial) must both pass. Add `--reruns=0` when judging stability: the default
  `--reruns 2` hides flakes.
- One file: `uv run pytest tests/test_x.py -q --reruns=0`.
- Pass options as `--opt=value` (`--alluredir=dir`), never `--opt value`: with xdist a space-separated value is read as a test path and widens collection.
- Do not create or edit `.py` files while a test run is in progress: some healing tests hash every source file.

## Layout
`framework/pages/` page objects, `tests/` tests, `conftest.py` fixtures, `specs/` specs to implement (if one is given), `docs/` notes and
checklists, `reports/` committed evidence. `ai_testgen/` and `framework/healing/` are AI tooling: leave them alone unless asked.

## Rules

Page objects
- [P1] One class per page in `framework/pages/<name>_page.py`, subclass `BasePage`, export it from `framework/pages/__init__.py`. Locators are
  properties; one method per user action; an action returns `self`.
- [P2] Act only through `self.click`, `self.fill`, `self.select_option`. Self-healing hooks in there, and `tests/test_locator_quality.py` fails on a direct `locator.click()`.
- [P3] No assertions about product behaviour in a page object (waiting for the page to be usable inside `open()` is fine). A failure should say, in the test, what is wrong.
- [P4] Copy the style of `framework/pages/transfer_page.py` and `tests/test_transfer_edge_cases.py` instead of inventing a new one.

Locators
- [L1] Prefer `get_by_role(..., name=...)`, then label/text/placeholder, then the form `name` attribute, then a hand-written `#id`, then other CSS.
  Never a generated id (ParaBank's phone field id is a UUID), a class, `:nth-child`, XPath, `.nth()`, `.first` or `.last`.
- [L2] An element with no accessible name: look for a labelled container (in ParaBank forms each field sits in a table row whose accessible name
  starts with its label) before falling back to `name` or an id.
- [L3] Every non-semantic selector goes into `ACCEPTED` in `tests/test_locator_quality.py` with the reason; that test fails until it does.
- [L4] A locator must match exactly one element, also when errors are showing and fields are filled. Repeated text (messages, labels) is the usual cause of strict-mode violations: count it before you commit.
- [L5] Buttons and links: `exact=True` when one name is a prefix of another ("Transfer" vs "Transfer Funds").

Tests
- [T1] Name `test_<behaviour>_<expected outcome>`; one behaviour per test; a module docstring says what is covered.
- [T2] Web-first assertions: `expect(locator).to_...`. A plain `assert` only for values that are not on the page. Never `time.sleep` or `wait_for_timeout`.
- [T3] Assert what a user sees, with the exact text the app shows. Never invent a message: read it from the page or the spec. (In Phase 2, 9 of the 14 failing generated tests asserted text the app never shows.)
- [T4] A test that expects a rejection checks the message **and** that nothing happened (no confirmation, no request sent, no balance change). "The confirmation is not there" alone also passes while the page is just slow.
- [T5] ParaBank fills tables and dropdowns asynchronously. Wait with `expect(...).to_have_count(n)` or `not_to_have_count(0)` before reading `inner_text()`; never read straight after `goto`.
- [T6] Independence: each test opens its own page and creates what it needs. `logged_in_page` is a shared customer: never change its balance or accounts.
  `new_customer_page` is a fresh customer with exactly one account: use it to pay, transfer, open accounts or count accounts.
- [T7] Test data is a constant defined once per module. Never hard-code a balance or an account number: read it from the UI.
- [T8] Known ParaBank bugs (negative and zero amounts accepted, no overdraft check, a login/session race): do not write a passing test that depends on them.
  Describe the correct behaviour as `xfail(strict=True, raises=AssertionError)` like `tests/test_transfer_edge_cases.py`.
- [T9] Break it on purpose once: change one expected value and see the test fail for the right reason. A test that cannot fail is not a test.

Code
- [C1] A docstring on every module, public class and public function of 8 or more lines in `framework/`, `scripts/`, `ai_testgen/` and `conftest.py` (`tests/test_docstrings.py`). Type hints on public signatures.
- [C2] pyflakes clean (`tests/test_lint.py`); every `.py` file parses (`tests/test_sources_parse.py`).
- [C3] No new dependency unless asked. Comments explain why, not what.

Done means
- [D1] You ran the new tests with `--reruns=0`, serially and with `-n 3`, plus `tests/test_locator_quality.py tests/test_lint.py tests/test_docstrings.py tests/test_sources_parse.py`, and your
  report says what ran, what passed and what you did not run.
- [D2] You changed only the files the task needs. If a test needs a small helper that another file lacks (a locator on an existing page object, say), add it and list it
  in the report. Never drop a check just to avoid touching another file; if a bigger change seems needed, say so in the report.
- [D3] Given a spec, its Deliverables, Constraints and Out of scope bind you. Report any criterion you could not meet and which facts you verified yourself.

## Git
Issue, then branch `day-NN-<topic>`, small commits, a PR with `Closes #N`, merged with a merge commit. No co-author trailers or generated-by footers
on commits or PR descriptions. The decision log in `PLAN.md` has the details.
