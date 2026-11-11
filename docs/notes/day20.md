# Day 20: Reviewing AI-generated tests

Code reviewed: the Bill Pay page object and 5 tests an agent wrote from spec 001 and that I merged **unedited** on Day 18, so the review starts from a clean baseline.
Full findings: `docs/reviews/billpay-tests-review.md`. Checklist: `docs/test-review-checklist.md`.

## What I did
- Wrote the **reviewer's checklist**. Order matters: measured checks first (tests pass alone/serial/parallel, repo checks, mutation check, locator score), then assertions, waits,
  independence and data, then scope and honesty. An AI-written test reads convincingly, so a reading-only review is the weak one.
- Reviewed the five tests: **5 findings** (1 misses a real bug, 2 weak, 1 latent, 1 style, 1 accepted trade-off).
- Fixed four by hand; re-measured.

## Before and after
| | Before | After |
|---|---|---|
| Mutants killed (8 injected Bill Pay bugs) | 7 / 8 | **8 / 8** |
| Locator audit score | 2.56 | **2.60** (`MIN_SCORE` raised to 2.6) |
| Registered non-semantic exceptions for Bill Pay | 2 | 1 (`#validationModel-{}`, kept with its reason) |
| Full suite, reruns off | 499 passed | 522 passed (serial and `-n 3` agreed on Day 19; `-n 3` today) |

## What the review taught
- **The one real defect was something the tests did not say.** Three rejection tests looked thorough (message visible, no confirmation) and still could not notice a form that
  shows its error *and* posts the payment. Only the mutation check made that visible; reading the code did not. This is the checklist's B2 item, and it is why section A comes first.
- **Most of the rest was small**: a locator that had a better semantic option, a latent vacuous-pass trap, stale comments. None would have failed a run today.
- **The agent's report was accurate.** Everything it claimed (counts, files, facts) reproduced; the weakness was in what it chose to check, not in what it said.
- **Where I disagreed with an earlier plan:** the Day 18 note said to replace the id-based error locator with row-based locators. I looked and did not: the visible texts repeat and a row's
  accessible name changes while an error shows, so the semantic version would be more fragile. Kept, registered with its reason.

## Limits
Eight mutants I wrote; one reviewer (me), who also wrote the mutants and the checklist. The mutation check is specific to Bill Pay.
