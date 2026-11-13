# Day 21: Automated quality gates for generated code

Branch `day-21-quality-gates`, issue #23. Four gates, all run on the generated tests too: ruff, mypy, a custom test gate, pre-commit.

## What I did
- **ruff** with a rule set I chose (E F W I B UP SIM PT C4 RUF) instead of the tool's default. Four rules ignored on purpose, each with its reason in `pyproject.toml`
  (`PT018` alone was 151 findings: `assert a and b` is used deliberately). 76 findings fixed (25 automatically, the rest by hand), none changed behaviour.
- **mypy** over `framework`, `ai_testgen`, `scripts` (`check_untyped_defs` on). 36 errors in 17 files, fixed by narrowing or annotating. Tests and generated tests are not type
  checked: they are fixture-driven and untyped by design, and annotating them would be noise.
- **A custom gate**, `scripts/check_tests.py`, for what AI-written tests get wrong and linters do not look at (AST based, 26 tests):
  QF001 fixed waits, QF002 assertions that cannot fail, QF003 an `expect(...)` that is never completed (`.to_be_visible` without the call), QF004 a test that checks nothing.
  An opt-out needs a rule id and a reason on the line, so an exception is a visible decision.
- **pre-commit**: ruff, mypy, the gate and a conflict-marker check, as local hooks through `uv run` (versions from `uv.lock`, nothing downloaded at commit time).
  I staged a file with `time.sleep` and `assert True`: the commit was refused with QF001 and QF002.

## What the gates found
- On the **generated tests**: nothing. They were already clean for ruff and for the gate (the codegen validator and `tests/test_lint.py` from Phase 2 catch the same classes).
  So today's gates protect future output; they did not repair past output, and I will not claim they did.
- On the rest of the repo: the ruff and mypy findings above. mypy found no real bug, but several honest ones (a `None` the type allowed and the code never checked, such as
  `healer` in `BasePage`).
- The gate's first run raised 24 findings: 22 in `framework/healing/sample_tests` (deliberately broken tests that exist to fail; excluded by name, with the reason in the
  code), 1 false positive (`get_logger(x) is get_logger(x)` is a real idempotence check, so a comparison of a call with itself no longer counts), 1 test whose check is
  `ast.parse` raising (opted out with a reason). Zero real defects.

## Limits
- QF004 trusts names: a call to `check_*`, `assert_*` or `verify_*` counts as a check without looking inside it.
- The gate is syntactic. It cannot tell a weak assertion from a strong one; that is what the Day 20 mutation check is for.
- `mypy` does not look at tests, so a type slip in a test helper is invisible to it.
- The hooks do not run the whole suite (too slow for a commit), so they missed what `tests/test_docstrings.py` caught on the full run: the new script's class had no docstring.
  The full suite stays the gate before a merge: 557 passed, 1 skipped, 2 xfailed (`-n 3`, reruns off).
