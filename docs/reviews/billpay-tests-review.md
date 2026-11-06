# Review: Bill Pay page object and 5 tests (adopted unedited on Day 18)

Reviewed on Day 20 with `docs/test-review-checklist.md`. Code under review: `framework/pages/bill_pay_page.py`, `tests/test_bill_pay.py`, and the two `ACCEPTED` entries
the agent added. Section A numbers were measured before any change.

## A. Measured
| Check | Result |
|---|---|
| 5 tests, serial and 3 x `-n 3`, reruns off | pass |
| Repo checks (locator quality, lint, docstrings, parse) | pass |
| Mutation check (`scripts/mutation_check.py`, 8 injected bugs) | **7 / 8 killed; `rejected_form_posts` survived** |
| Locator audit score | **2.56** (baseline before the page object: 2.58) |

## Findings (most severe first)
| # | Where | What is wrong | A failure it misses | Severity |
|---|---|---|---|---|
| 1 | `tests/test_bill_pay.py` rejection tests (empty, mismatch, non-numeric) | They show the message and that no confirmation appears. Nothing proves the rejected form sent **no request**. | A regression where validation shows its message but the form still posts the payment (the mutant `rejected_form_posts`): all three stay green. | misses a real bug |
| 2 | `bill_pay_page.py` `from_account` | CSS on the `name` attribute although the dropdown sits in a table row whose accessible name starts with "From account #:". Needs an `ACCEPTED` entry it does not deserve. | Breaks if the form binding is renamed; lowers the locator score. | weak |
| 3 | `bill_pay_page.py` `field_error` | Accepts any string. A mistyped id matches nothing, and `not_to_be_visible()` on it passes vacuously (the tests only use `to_be_visible()` today, so nothing fails yet). | A future negative assertion that can never fail. | weak, latent |
| 4 | `tests/test_locator_quality.py` | The `input[name='{}']` reason still says "registration inputs" (it is now shared with Bill Pay); `MIN_SCORE` comment says "current score is 2.58" (it is 2.56) and the floor was not raised after the page object landed. | A later change can lower the score unnoticed. | style, misleads |
| 5 | `bill_pay_page.py` error locators by id | `#validationModel-{}` is non-semantic. Not fixable cheaply: the visible texts repeat and the row's accessible name changes while an error shows. **Accepted, with its reason**, not fixed. | none found | accepted |

Not findings (checked): no sleeps or position locators; fixtures are right (`new_customer_page` only where money moves); no hard-coded balance (read from the UI);
waits on the asynchronous tables are web-first; the debit row check includes the amount; messages match the live page.

## Fixes (by hand)
1 add a request recorder to the three rejection tests; 2 locate the dropdown through its row and drop its `ACCEPTED` entry; 3 validate the id against a known list;
4 correct the reason, raise `MIN_SCORE` to the new score. Re-measured after the fixes: see `docs/notes/day20.md`.
