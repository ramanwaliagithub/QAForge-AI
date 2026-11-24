# AI-assisted development: my playbook (Phase 3, Days 18-24)

What I delegate to an AI, what I keep, and how I check what comes back. Every line is something I measured in this repo; the evidence is linked. Where I have one run and
not ten, it says so. Update it when a later experiment contradicts it.

## The loop
1. **Probe the real thing first** (the live page, the real failure). Facts go into the task with a date. An agent that has to discover a message text will sometimes get it wrong.
2. **Write a spec** (`specs/README.md`): goal, context, deliverables with exact names, numbered acceptance criteria, constraints, out of scope, verification commands, open questions.
3. **Give the agent the path, not a summary.** Do not rely on it remembering `CLAUDE.md`; tell it to read the file.
4. **Run the measured checks before reading any code** (`docs/test-review-checklist.md`, section A): passes alone, serially and in parallel with reruns off; repo checks; locator audit; the
   mutation check for the behaviour the tests are meant to catch.
5. **Then review by reading**, with the checklist, and write findings with a concrete failure each one would miss.
6. **Gates catch the rest, automatically** (ruff, mypy, `scripts/check_tests.py`, pre-commit). Gates catch the cheap mistakes; they do not judge a test's strength.

## What I delegate
- **Scaffolding to a known pattern**: a page object and tests copied from an existing page's style. With a spec, 5 of 5 tests passed, were stable and met every convention first time (Day 18).
- **Reading logs into a structured draft**: a bug report from a saved failure, 11 of 11 valid, about 5 s each (Day 23). The structure and steps are usable; the text over-claims.
- **Proposing, never deciding**: locator suggestions, edge cases, duplicates ("similar, take a look"). A person or a deterministic check decides.
- **Realistic-looking data, once**: a model writes a dataset, a person reads it, it is frozen in a file (Day 22).

## What I keep
- **What to test and what "correct" means.** Left to the agent, coverage is its choice (the vague run spent two of five tests on one payment, Day 18), and its triage is a guess: it
  was wrong on 5 of 11 failures, mostly calling a test mistake an app bug (Day 23). The model is never given the requirement; I have it.
- **Anything that must be unique, exact or repeatable**: usernames, money, boundary values, seeds. These come from code (Day 22).
- **The decision to file a bug, to heal a locator, or to change the app's expected behaviour.** Healing a wrong expectation hides the defect; none of the 13 failures that were wrong
  expectations should be healed (`docs/phase2-results.md`).
- **The rubric, before the scoring.** I commit the scorecard or the ground truth before looking at outputs (Days 18, 19, 23).

## What to distrust
- **A test that reads well.** The three rejection tests looked thorough and could not notice a form that shows its error *and* posts the payment. Only the mutation check showed it (Day 20).
  Reading found the smaller problems; measuring found the real one.
- **A spec's own mistakes.** An agent follows a spec faithfully, including my wrong assumption that the form fields had no accessible name (Day 18). State facts; mark design hints as hints.
- **A spec silently overrides `CLAUDE.md`.** If a spec waives a rule, it says so under Constraints (Day 19).
- **A rule that sounds responsible.** "Change only the files the task needs" made one agent leave a balance check out of its test. It now says what to do when another file lacks a helper (Day 19).
- **One run.** Every comparison here is n=1 per cell or n=3. They show what changed in these runs, not how often.
- **A threshold I did not measure.** My first guess for duplicate similarity (0.85) found none of 6 duplicate pairs (Day 23).
- **Triage by a model.** 6 of 11 right, and it never says "unclear". Do not route bugs by it.

## What instruction files do
They change *how* an agent works more than *what* it produces: with `CLAUDE.md` the agents mutation-tested their own tests (+55% and +96% time), and the output did not improve (mutants killed
8/8 to 6/8 and 7/8 to 7/8, Day 19). A rule that no test enforces is where a file earns its keep; style rules that a test already enforces add little. Keep the files short and in sync
(`tests/test_agent_instructions.py`), because a rule that points at a deleted file is followed faithfully.

## What gets automated, so it is not a matter of discipline
| Mistake | Check |
|---|---|
| Direct `locator.click()`, undocumented non-semantic locator, locator score drop | `tests/test_locator_quality.py` |
| Unused imports, undocumented public surface, unparsable file | `tests/test_lint.py`, `tests/test_docstrings.py`, `tests/test_sources_parse.py` |
| Fixed waits, assertions that cannot fail, an `expect` without a matcher, a test that checks nothing | `scripts/check_tests.py`, pre-commit |
| Lint, types | ruff, mypy, pre-commit |
| Rule files drifting apart or pointing at missing files | `tests/test_agent_instructions.py` |
| A test that cannot fail | the mutation check (`scripts/mutation_check.py`), run on purpose, not on every commit |

## Habits that paid for themselves
- Run the new thing against the live app before trusting the agent's report of it.
- When a number looks too good or too bad, probe the cause: an accented name returned HTTP 400, found while fixing my own wrong check (Day 22).
- Write down what the measurement could not show, next to the result (every `docs/notes/dayNN.md` has a Limits section).
- Say plainly when a gate found nothing: the Day 21 gates found no defect in the generated tests, so they protect future output, not past output.

## Open questions
- Does giving the model the user story fix its triage? Not tried.
- Do the instruction files help on a page the rules were not tuned on? Not tried: Day 19 was a tuned test.
- Is a frozen, reviewed dataset worth its upkeep? Not tried: none is committed yet.
