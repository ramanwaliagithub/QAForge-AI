# Day 19: Project context files

Question for the day: do instruction files (`CLAUDE.md`, Copilot instructions, a checklist) make an agent's output better, and which instructions did the work?
Short answer from this experiment: **they changed how the agents worked far more than what they produced, and one rule made the output worse.**

## What I did
- **`CLAUDE.md`** (63 lines): how to run, layout, and 24 rules with ids (`[P1]` page objects, `[L1]` locators, `[T1]` tests, `[C1]` code, `[D1]` done). Most rules carry
  the mistake they come from.
- **`.github/copilot-instructions.md`**: the same rule ids, shorter, for Copilot (which does not follow links, so the rules are inline).
- **`docs/test-writing-checklist.md`**: the writer's checklist, each item citing a rule id. (Day 20 builds the reviewer's checklist.)
- **`tests/test_agent_instructions.py`**: the three files must define the same rule ids, the checklist may cite only rules that exist and must cover every rule that is not a code
  or page-object rule, every path they mention must exist, they must stay under 90 / 60 lines, and none may credit a tool. I broke each condition on purpose to see the test fail.

## The experiment: 2 x 2
Day 18 gave two cells (vague prompt, spec; no context files). Today I added the other two: the **same two prompts**, from the **same two base commits**, with only the three context files added.
One run per cell, same model, own worktree, same operating notes.
- **Delivery:** a subagent in a worktree does not auto-load that worktree's `CLAUDE.md`, so each prompt got one extra sentence telling it to read the file (and that its Git section did not apply to the run).
  This tests the content of the rules, not the loading mechanism.
- **This is a tuned test, not a held-out one.** Rules L2 (look for a labelled container) and T4 (a rejection test checks that nothing was sent) were written *after* reading the Day 18 vague run, which
  did exactly those things. Any improvement on spec 001 in those two dimensions was expected and says nothing about other pages.
- **Scoring** (all four arms with one script version; the two Day 18 arms rescored from reconstructed checkouts and reproduced their Day 18 numbers): the Day 18 scorecard plus rule indicators, and a **new
  mutation check** (`scripts/mutation_check.py`). It injects eight app misbehaviours into the Bill Pay screen one at a time (a plugin outside the checkout patches the browser contexts) and
  counts how many the tests notice. The eight were fixed before the Day 19 arms were run; the harness itself was debugged on the Day 18 spec arm. Evidence: `reports/day19/`.

## Results

| Arm | Mutants killed | Locator audit (baseline 2.58) | Non-semantic selectors | Files outside deliverables | Rejection tests that watch requests | Effort (harness-reported) |
|---|---|---|---|---|---|---|
| vague, no context (Day 18) | **8 / 8** | 2.70 | 0 | 1 (`accounts_page.py`) | 3 | 26 calls, ~97k tokens, 6.3 min |
| vague + context | **6 / 8** | 2.74 | 0 | 0 | 3 | 24 calls, ~103k tokens, 9.7 min |
| spec, no context (Day 18) | **7 / 8** | 2.56 | 3 | 0 | 0 | 17 calls, ~78k tokens, 4.3 min |
| spec + context | **7 / 8** | 2.60 | 2 | 0 | 0 | 22 calls, ~100k tokens, 8.3 min |

All four: 5/5 tests pass serially and three times with `-n 3`, all repo checks pass, no banned constructs, every test ends in `expect`, no balance written into a test, payment tests on `new_customer_page`.
Survivors: spec runs let `rejected_form_posts` survive (no request check); vague + context lets `payment_not_debited` and `payment_debited_twice` survive (no balance check).
Read the last two mutants as "extra" for the vague prompts: the story they were given does not say the payment must debit the account; the spec does.

## Which instructions mattered (and how sure I am)

| Rule | What happened | Evidence |
|---|---|---|
| **T9** break it on purpose | The biggest change in behaviour. Both context agents ran ten-odd single-value mutations of their own tests; neither Day 18 agent mentioned any. It shows in the code (the spec run added a guard so a mistyped error id cannot make `not_to_be_visible()` pass vacuously) and in the time (+55% and +96%). **No measurable gain on my eight mutants**, but the Day 18 arms already killed 7 and 8 of 8, so this is a ceiling effect, not proof that T9 does nothing. | self-reported + code; kill counts measured |
| **D2** change only the files the task needs | The one harmful rule. The vague + context agent says it left the balance out of its payment test *because* a balance reader would mean editing `AccountsPage` (rule D2). The Day 18 vague run had added exactly that helper and tested the balance. Scope improved (0 outside files), coverage dropped (6/8). **Reworded after the run:** a small helper may be added and listed; never drop a check to avoid touching a file. The new wording is untested. | the agent's own stated reason; kill count measured |
| **L2** labelled container before CSS | Applied where the spec allowed it: the spec run found the From dropdown through its table row, so one non-semantic selector disappeared (3 to 2, audit 2.56 to 2.60). The vague arm already did this without being told (2.70 to 2.74). | measured |
| **L2, T4 vs the spec** | The spec fixed the inputs to `name` attributes and asked only for "no confirmation" in rejection tests. The spec run read both documents and followed the spec each time (it said so). **A spec silently overrides the context file.** New rule in `specs/README.md` and a line in the template: a spec says which `CLAUDE.md` rules it waives. | agent report + code |
| **T4** nothing was sent | No effect: the vague arm did it with and without the rule, the spec arm was blocked by the spec. | measured |
| **D1** say what you ran and did not run | The reports became more checkable (for example "I did not run the full suite serially"). Not scored. | read |
| T1, T3, T5, T6, T7 | No signal: all four arms already complied (no invented message text, async waits, right fixtures, no hard-coded balance). Page-object, locator-register, lint and docstring rules are enforced by tests anyway, so there was nothing for the file to add. | measured |

## What this cannot show
- **One run per cell, one model.** The 8/8 vs 6/8 gap is one agent choosing to include a balance test or not; run-to-run variance could produce it. The agent's stated reason makes D2 the likely cause, which is not the same as proof.
- **Ceiling:** eight mutants that I wrote, five of them killed by every arm. The check separates "has a request check" and "has a balance check"; it is not a general measure of test strength.
- **Tuned on this task** (above). No held-out page was tried.
- **Self-reported behaviour** (T9, D1) is what the agents said they did; only the artifacts and the kill counts are measured.
- The agent reads `CLAUDE.md` because the prompt says to. Whether a real session attends to it as closely is not tested.

## Defects in my own work, found by the experiment
- Rule D2 as first written (above).
- Two spec-versus-context conflicts that I had not noticed in my own spec (L2 for the inputs, T4).
- Test docstring in the vague + context run cites "CLAUDE.md T8": instruction ids leak into code comments. Harmless, but a rename of a rule would orphan it.

## Carried to Day 20
- Review the adopted Day 18 tests with the review checklist; add "mutation score" as a column (`scripts/mutation_check.py` already scores any Bill Pay suite).
- Decide whether D2's new wording works: the next agent task that needs a helper in another file is the test.
- Spec 001 still waives L2 and T4 without saying so; leave it as the experiment's input, and use the new template line from spec 002 on.
