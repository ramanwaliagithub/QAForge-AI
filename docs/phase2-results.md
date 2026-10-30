# Phase 2 results: AI test generation and self-healing (Days 6-17)

Everything below was measured on this repository, with `llama3.1:8b` running locally through Ollama, against ParaBank in
local Docker. Raw evidence is committed in `reports/` (paths are given next to each table). Where a number is flattering
I say why it may be, and the limits are in section 6.

## The short version

| Question | Answer |
|---|---|
| Can a local 8B model turn user stories into **passing** UI tests? | **Barely: 1 of 15 (7%).** Valid, runnable code is easy (15/15); *correct expectations* are not. |
| Can it repair a broken locator? | **Yes, for the kind of break we tested.** On a fresh set written before the model ran: **7/7 correct, 0 wrong**; on the earlier sets, measured before each fix: 5/12 (42%) correct, 1 wrong. |
| Did healing help the generated tests? | **No: 0 of 14 failures could be healed**, and none should be. They fail on wrong expectations, not stale locators. |
| Is the suite stable? | **480 tests pass serially; 0 of 30 parallel runs failed** with reruns switched off (median 37 s). |
| What was found late? | Six defects of my own, listed in section 5. Each stayed hidden until I ran something in a way I never had before. |

## 1. How the numbers were produced

- **Model and app:** `llama3.1:8b` (temperature 0 unless stated), ParaBank in Docker (`docker compose up -d`), Python 3.14,
  Chromium headless, `pytest-xdist -n 3` for parallel runs.
- **Reruns are off for every measurement** (`--reruns=0`). The repo's default config keeps `--reruns 2` as a mitigation for a
  ParaBank session race (section 4); a measurement with reruns on would hide the failures it is supposed to count.
- **"Correct heal"** means the suggested locator resolves to the element a person would pick (`framework/healing/ground_truth.py`),
  not merely to *some* single element. A locator can match exactly one element and still be the wrong one.
- **Held-out** means: the cases and their right answers were committed before the model was run on them, and the suggester
  was not changed afterwards. A set stops being held-out the moment a result from it is used to change the prompt or the code.
  This is why healing is reported per set and never as one blended number (decision log, 2026-10-30).

## 2. Test generation (Days 6-9)

15 test cases from 3 stories (transfer funds, open account, bill pay), each turned into one pytest test.
Evidence: `reports/testgen/`, `ai_testgen/outputs/`, notes in `docs/notes/day07..09.md`.

| Setup | Valid code | Passed |
|---|---|---|
| Day 8: no page context | 15/15 | 0/15 |
| Day 9: no context, stricter rules (control) | 14/15 | 0/15 |
| Day 9: accessibility snapshot in the prompt | 13/15 | 0/15 |
| Day 9: list of real elements and selectors | 11/15 | 0/15 |
| Day 9: four verified example tests, no context | 15/15 | 0/15 |
| Day 9: examples **and** real elements | 15/15 | 2/15 |
| Day 9: + screen URL and "exactly one account" hint | 15/15 | 1/15 |
| **Day 17: committed tests, 5 runs, reruns off** | 15/15 | **1/15, the same 14 fail on every run** |

(The 2/15 and 1/15 rows differ by one test after a prompt edit; read it as "1-2 of 15", not as a regression.)

**What the 14 failures are** (`reports/phase2/generated.json`, five runs):

| Count | What the test got wrong |
|---|---|
| 9 | Asserts text the app never shows ("Invalid amount", "Payee Name: is required", ...). One of them uses a locator that matches three labels. |
| 2 | Acts on something that is not there: fills `#initialBalance` (ParaBank has no such field), or a `select_option` that times out. |
| 1 | `fill` on a link (`#newAccountId`). |
| 1 | API misuse (`ValueError: Unsupported type: str`; on one run in five a timeout instead). |
| 1 | An invented fixture key (`KeyError: 'account_ids'`). |

Reading: grounding and examples fixed *navigation, locators and code validity*. What remains is the assertions. The
Day 7 schema stores `expected` as free text, so the generator has nothing checkable to turn into an assertion and pastes
the prose into `get_by_text(...)`. The fix I believe in (and did not build) is to make expectations checkable in the schema (section 8).

## 3. Self-healing (Days 13-16)

### 3.1 How accurate is the locator suggestion?

Evidence: `reports/healing/`. All rows: guard-eligible locator failures, the model's suggestion validated on the captured page.

| Set | State of the suggester | Cases | Correct | Wrong element | Not healed |
|---|---|---|---|---|---|
| Held-out sets 1-3 pooled, measured when written (Day 14) | before the fixes they exposed | 12 | 5 (**42%**) | 1 | 6 |
| Tuned set + sets 1-3, re-measured (Day 17) | after those fixes: **diagnosed, so optimistic** | 15 | 14 | 0 | 1 |
| **Set 4, T=0 (Day 17)** | committed before the first model run; suggester unchanged | 7 | **7** (95% interval 65-100%) | 0 | 0 |
| Set 4, T=0.7, three runs | same | 21 (7 distinct) | 21 | 0 | 0 |

Details that matter for set 4:
- 5 of 7 were valid on the first try. **3 of 7 only work because of a mechanical repair**: the model writes `#customer.address.street`
  (invalid CSS, the dots mean classes) and our code rewrites it to `[id='customer.address.street']` when an element with exactly
  that id exists. Two of those three first needed a rejected, invented id (`#customer.address.line1`).
  Without that repair set 4 would very likely have scored 4/7: in earlier sets the model rewrote a valid `[id='...']` into the
  invalid `#...` form every time it saw one. The repair is recorded on every proposal so a reviewer sees it.
- The fixes were derived from failures in sets 1-3, and set 4 contains the same families (registration fields, button labels,
  dropdown ids). It shows that *known* families no longer fail; it says little about unfamiliar kinds of change.
- Controls: two failures where no locator is at fault (an assertion on a found element). With the guard off, **2/2 would be
  "healed"** (the model happily finds some element that matches); with the guard on, 0 are attempted.

### 3.2 At run time (`pytest --heal`, Day 15)

With the real model driving the real fixture over the 17 sample tests: **13/13** locator failures were healed, verified by
retrying the step, and resolved to the correct element, 1.3-4.3 s each including the model call. The 4 that still fail do so by
design (2 assertion controls, 2 `expect()` waits inside page objects, which are not covered). These are the diagnosed samples,
so quote 3.1's set 4 as the accuracy figure and this as "the mechanism works end to end".

### 3.3 On the failures this phase actually produced (the "healing rate" that matters)

`reports/phase2/generated_heal.json`, `generated_probe.json`.

- Ran the 15 generated tests with `--heal`: **14 failed, 0 heal events.** None reached the healer: every failure is raised in the
  test body, and the generated tests call Playwright directly instead of going through a page object, while the healer is hooked
  into the page objects' `click`/`fill`/`select_option` only. **Healing changed the generated pass rate by exactly zero (1/15 -> 1/15).**
- An offline probe then asked: *what would the guard and the model do if they were in the path?* Before today's fix the guard
  attempted 2 of the 14. One had no valid answer (the field does not exist). The other produced a **validated false heal**:
  for `expect(get_by_text("Account #:")).to_be_visible()`, which matched three labels, the model proposed the "Bill Pay"
  navigation link. It matches exactly one visible element and has nothing to do with the check; applied, the test would have
  passed for the wrong reason. This is the failure the Day 14 notes predicted ("DOM validation cannot tell a real fix from a
  plausible wrong one"), and the guard had a hole: a strict-mode violation raised by `expect()` was classed as a locator problem.
  It is now its own kind (`assertion_strict_violation`, hint `maybe`) and the guard refuses it by default. Re-running the
  probe: 1 of 14 attempted (the missing field), 0 validated suggestions.
- At most one of the 14 (the three-label locator) has a locator-level fix at all (`get_by_text("Account #:", exact=True)`). The other
  13 are wrong expectations or invented UI. Healing them would hide the defect, so "0 healed" is the correct outcome.

### 3.4 Review and apply (Day 16)

Proposals are grouped, scored (a transparent heuristic, not a probability: it saturates near 1.0, so the flags and the diff are the real
signal), shown as a diff, and only `approved` ones are applied, and only where the old locator is one unique literal in a clean file.
End to end on a stale locator committed to `TransferPage` on a throwaway branch: healed, approved, applied, and the file came
out identical to `main`.

## 4. Suite health (Days 12 and 17)

| Measurement | Result |
|---|---|
| Serial `uv run pytest`, reruns off | **480 passed, 1 skipped (a demo), 2 xfailed (known ParaBank bugs)**, 52 s |
| Parallel `-n 3`, **30 runs**, reruns off, 477 tests, collection checked identical every run | **0 runs with any failure**; median 37.4 s (26.9-38.7) |
| Day 12 baseline, before the registration-retry helper | about 5% of runs failed (4 of ~78) |

0 of 30 is **consistent with** an improvement but does not prove it: if the true rate were still 5%, 30 clean runs would happen
about one time in five (0.95^30 = 21%). The 95% upper bound on the per-run failure rate is about 10%. The cause of the old flakes,
a ParaBank bug where roughly 2.5% of failed logins return another customer's session under concurrency, is still in the app
(`scripts/repro_parabank_login_race.py`); the test code works around it and `pytest.ini` keeps `--reruns 2`, visible in the summary line.

## 5. Defects of my own that surfaced late

Each of these was invisible until something was run in a way I had not run it before.

1. **`scripts/run_generated.py` did not parse since Day 12.** A comment swallowed a comma. No test imported it. Found on Day 17 when
   I ran it for this report. Now every Python file is parsed by a test.
2. **A bare `uv run pytest` failed 8 tests since Day 10** (`asyncio.run()` with Playwright's event loop alive in the main
   thread). I had always used `-n`, which spread the tests across workers, and README's first command was the broken one. Fixed, with a
   regression test that fails without the fix.
3. **A hole in the healing guard** (3.3), found by probing the generated tests' real failures instead of my synthetic samples.
4. **My stability script measured the wrong test set for four hours.** A space-separated `--alluredir <dir>` made pytest widen
   collection (472 to 514 tests when I reproduced it), so every run included the deliberately failing samples. All of that data was discarded. The script
   now uses `--option=value`, records the collected count and warns when it changes; a test pins the command.
5. Day 11's strict `xfail` tests were hiding a broken locator (found Day 16): they now accept only `AssertionError`.
6. A classifier test wrote a temporary `.py` file into `framework/pages/` while other tests hash every source file to prove healing
   never edits source; the two could overlap under xdist. It now compiles in memory.

## 6. What these numbers do not show

- **One small model, three stories, one app.** 15 generated tests and 7 + 15 healing cases. Intervals are wide; the ground truth
  was written by me; ParaBank's pages are tiny (about 30 elements), so a real page would need candidate ranking.
- **Synthetic breaks.** Every healing sample is a rename I made. Real redesigns change structure, copy and behaviour together.
- **"The retry worked" is not "the right element".** Verification proves the action succeeded, not that it hit the intended element
  (the Bill Pay link is the example). The role constraint, the guard and the human review exist for this, and none of them is proof.
- **Coverage:** healing reaches `click`/`fill`/`select_option` in page objects. It does not reach `expect()` calls, waits inside page objects,
  or tests that use raw Playwright (all 15 generated tests).
- The suite's pass rate says the framework is stable; it says nothing about the *quality* of the generated tests, which pass or fail on content.

## 7. Findings about the application under test

Found with AI-assisted exploration (Playwright MCP, Days 10-11) and kept as tests or reproductions: ParaBank **accepts negative transfer
amounts**, has **no overdraft check** (a $1,000,000 transfer leaves the source at -$999,584.50), and has the **login/session race** above.
Both bugs are strict `xfail` tests that will flip loudly when fixed. Details: `docs/mcp-findings.md`.

## 8. Carried into later phases

- **Checkable expectations** in the test-case schema (`text_visible`, `url_contains`, `element_value`, taken only from the
  acceptance criteria) so codegen can map them to assertions mechanically. Probably worth more than a larger model; the Phase 4 evals
  are where its effect should be measured.
- **Generated tests through page objects**, or a thin locator helper they must use, so that healing can apply at all.
- The numbers here are a baseline for Phase 4 (evals), where "was this test generation any good?" needs a better answer than a pass rate.
