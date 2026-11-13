# Test-writing checklist

For the person or agent writing a test. Go through it top to bottom before saying a test is done. The ids in brackets are the rules in
`CLAUDE.md` (the reviewer's checklist, for judging someone else's tests, is a separate document).

## 1. Before writing
- [ ] I opened the page (or read the spec's facts) and know the real labels, messages and their order. I invented no text. [T3]
- [ ] I know which parts load asynchronously (tables, dropdowns) and what to wait for. [T5]
- [ ] I know which fixture gives the right customer: the shared one (read-only) or a fresh one (may change balances). [T6]
- [ ] I read one existing page object and one existing test as the model. [P4]

Before saying a test is done, `uv run python -m scripts.check_tests` (see `scripts/check_tests.py`) must print nothing; the pre-commit hook runs it for you.

## 2. Locators
- [ ] Semantic first (role + name, label, text); no class, generated id, XPath, `.nth()`, `.first`, `.last`. [L1]
- [ ] Where there is no accessible name I tried a labelled container before CSS. [L2]
- [ ] Each locator matches exactly one element, also with errors showing and fields filled. [L4]
- [ ] Each non-semantic selector is registered in `ACCEPTED` with a reason. [L3]
- [ ] Buttons and links use `exact=True` where one name is a prefix of another. [L5]

## 3. The test
- [ ] The name says the behaviour and the outcome; the test checks one behaviour. [T1]
- [ ] It ends with `expect(...)` on something the user sees, using the exact text the app shows. [T2] [T3]
- [ ] A rejection test checks the message and that nothing happened (no confirmation, no request, no balance change). [T4]
- [ ] No `time.sleep`, no `wait_for_timeout`. [T2]
- [ ] It passes alone, in any order and in parallel; it creates what it needs. [T6]
- [ ] No hard-coded balance or account number; data constants are defined once. [T7]
- [ ] It does not rely on a known ParaBank bug; if it describes correct behaviour the app violates, it is a strict `xfail`. [T8]
- [ ] I broke it on purpose once (changed an expected value) and it failed for the right reason. [T9]

## 4. Before saying done
- [ ] Serial and `-n 3`, `--reruns=0`, three times in a row. [D1]
- [ ] `tests/test_locator_quality.py`, `tests/test_lint.py`, `tests/test_docstrings.py`, `tests/test_sources_parse.py` pass. [C1] [C2]
- [ ] Only the files the task needs are changed. [D2]
- [ ] My report says what I ran, what I did not run, what I assumed, and which criteria I could not meet. [D1] [D3]
