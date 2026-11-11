# Test review checklist

For judging tests somebody else (a person or an agent) wrote. The writer's checklist is `docs/test-writing-checklist.md`; rule ids in brackets are in `CLAUDE.md`.
Do the measured checks first: they do not depend on how convincing the code reads. An AI-written test usually reads well.

## A. Measured (run these before reading anything)
- [ ] **Passes alone, serially, and 3 x `-n 3`, `--reruns=0`.** A pass that needs reruns is a flake. [D1]
- [ ] **Repo checks pass:** `tests/test_locator_quality.py`, `tests/test_lint.py`, `tests/test_docstrings.py`, `tests/test_sources_parse.py`.
- [ ] **Mutation check:** inject the app bugs the requirement describes and count how many the tests notice (`scripts/mutation_check.py` for Bill Pay). Every survivor is a finding.
- [ ] **Locator score** did not drop (`uv run python -m scripts.locator_audit`); each new non-semantic selector has a reason in `ACCEPTED`. [L1] [L3]

## B. Assertions (the usual place AI tests are weak)
- [ ] Each test ends with `expect(...)` on something a user sees, with the exact text the app shows, checked against the real page. [T2] [T3]
- [ ] **A negative test also proves nothing happened** (no request, no balance change), not only that a success message is absent. [T4]
- [ ] **Absence checks cannot pass vacuously:** `not_to_be_visible()` on a locator that matches nothing passes; is the locator proven to exist elsewhere?
- [ ] No `assert True`, no assertion on a value the test just set, no assertion that repeats the arrange step.
- [ ] Two checks on one element are not duplicates (`to_be_visible` + `to_have_text` are not: hidden elements still have text).

## C. Waits and timing
- [ ] No `time.sleep`, no `wait_for_timeout`, no `.first` / `.nth()` to dodge a strict-mode error. [T2] [L1]
- [ ] Asynchronous parts (tables, dropdowns) are waited for with a web-first assertion before they are read. [T5]
- [ ] A fix for a flake is a better wait, not a retry or a longer timeout.

## D. Independence and data
- [ ] Right fixture for the effect: shared customer for read-only tests, a fresh customer for anything that moves money. [T6]
- [ ] Order does not matter; nothing depends on another test having run or on leftover state.
- [ ] No hard-coded balance, account number, or generated id; constants defined once. [T7]
- [ ] Data cannot collide under `-n 3` (unique usernames come from fixtures).
- [ ] No passing test depends on a known app bug; a described-correct-behaviour test is a strict `xfail`. [T8]

## E. Scope and honesty
- [ ] Only the files the task needs changed; any extra helper is listed. [D2]
- [ ] The author's report matches what you can reproduce (commands, counts, "I did not run X").
- [ ] Facts in comments and docstrings are true today (a stale "current score is 2.58" misleads the next reader).

## How to write a finding
`file:line`, what is wrong, a **concrete failure it would miss** (the mutant, the case), severity (misses a real bug / weak / style), and the fix. A finding without
a failure scenario is an opinion.
