# Day 17: Phase 2 consolidation

The full write-up with all numbers is `docs/phase2-results.md`. This note is how the day went and how to reproduce it.

## What I did
- **A fresh held-out set for healing** (`framework/healing/sample_tests/test_heldout4_locators.py`, 7 cases). I wrote the cases and their
  ground truth and committed them (with the captured samples) **before** running the model on them, so the final healing number could not be
  tuned by looking at it. One ground-truth entry was wrong (`input type="button"`, not `submit`); I fixed it from the captured page before
  any model run. Result: 7/7 correct, 0 wrong; 3 of the 7 depended on the mechanical dotted-id repair.
- **Measured the generated tests properly:** 5 runs with reruns off (1/15 pass, the same 14 fail every time) and one `--heal` run (0 heal events:
  the generated tests never go through a page object). Then `scripts/probe_generated_failures.py` asks what the guard and model would do
  with those real failures. That found a hole in the guard (below).
- **Measured suite stability** with `scripts/suite_stability.py`: 30 parallel runs, reruns off, 0 failing runs.
- **Cleanup:** 60 docstrings plus 6 module docstrings, pyflakes findings fixed (11), and three tests that keep it that way
  (`test_docstrings.py`, `test_lint.py`, `test_sources_parse.py`).

## Mistakes and what they taught me
- **The first 30-run loop was worthless** and cost four hours. I passed `--alluredir <dir>` as two arguments; with xdist, pytest then collected
  514 tests instead of 472, including the deliberately failing healing samples. Every run "failed". I only noticed because the run took 490 s
  instead of 38 s. The script now uses `--option=value`, defaults the selection to `tests`, records how many tests were collected and warns if
  that changes. Rule: **check the denominator before reading the numerator.**
- **`scripts/run_generated.py` had been broken since Day 12** (a trailing comma inside a comment). Day 12's note claimed it passed `--reruns 0`;
  I never ran it afterwards. I found it only because a docstring audit parsed every file. Now a test parses all of them.
- **A bare `uv run pytest` failed 8 tests**, on a clean `main` too (checked in a worktree). `asyncio.run()` cannot start on the main thread once a
  Playwright sync browser is alive. I had always used `-n`, which hid it. Fixed with a thread per coroutine and a regression test that fails without the fix.
- **The healing guard had a hole.** A strict-mode violation raised by `expect()` was classified as a locator problem, and the model "healed" an
  assertion onto the Bill Pay navigation link (one visible match, nothing to do with the check). New kind `assertion_strict_violation`
  (hint `maybe`, `page_object_precondition` inside a page object); the real message from the failure is the test fixture.
- A classifier test wrote a temporary file into `framework/pages/`; under xdist it could overlap with the tests that hash every source file.
  It now compiles in memory.

## Decisions
- "Healing rate" is reported per set, never blended; the primary figure is the held-out set written before the run (decision log, 2026-10-30).
- I did not build checkable expectations on Day 17. Consolidation measures the phase as it is; changing generation first would have moved the
  numbers I was about to record. It is the first item in "carried into later phases".

## Reproduce
```bash
docker compose up -d && ollama serve                         # ParaBank and the model
uv run python -m scripts.make_failure_samples heldout4       # recapture set 4 (needs ParaBank)
uv run python -m scripts.heal_eval day17_all_t0 0 1 all      # every set at T=0 (needs Ollama)
uv run python -m scripts.suite_stability suite 30            # about 19 minutes; do not edit .py files meanwhile
uv run python -m scripts.suite_stability generated 5 ai_testgen/generated -m ai
HEAL_REPORT=reports/phase2/generated_heal.json uv run pytest ai_testgen/generated -m ai --heal -n 3 --reruns=0
uv run python -m scripts.probe_generated_failures            # guard + model on the failures saved in reports/failures
```
