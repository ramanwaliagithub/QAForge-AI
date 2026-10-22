# MCP exploratory testing findings: Transfer Funds (Day 11)

Method: llama3.1:8b proposed edge cases from the **real page snapshot**; each case was executed through the Playwright MCP
server (`scripts/mcp_transfer_edge_cases.py`, each case run twice); results were checked by hand against the app and the
account balances. Raw data: `reports/mcp_edge_cases.json` (committed; re-run the script to regenerate).

## What the five cases showed

| Edge case | Model expected | ParaBank did | Verdict |
|---|---|---|---|
| Empty amount | reject | `Error!` page with **three** messages: "The amount cannot be empty.", "Please enter a valid amount." and "An internal error has occurred and has been logged." | Rejected with proper validation messages, **plus** a spurious internal error (defect). Test: `test_empty_amount_shows_an_error`. *Corrected on Day 12: the first version of this row listed only the internal error, because my snapshot digest did not surface the validation messages; Playwright's strict mode (`p.error` matched 3 elements) revealed them.* |
| Negative amount (-100) | reject | **accepted**, "Transfer Complete! -$100.00 has been transferred" | **App bug.** Test: `test_negative_amount_is_rejected` (strict xfail) |
| Decimal amount (100.50) | reject | accepted | **Model wrong.** Valid money. Test: `test_decimal_amount_is_accepted` |
| Same account for From and To | reject | accepted | Debatable (no spec). Not turned into a test. It is also the form's default, so it is easy to hit by accident |
| 1,000,000 ("maximum allowed amount") | accept | accepted | Model right by the letter but missed the point: the account held $515.50. See below |

## The big one: no overdraft protection
Checked on the overview page: before, account A = $515.50. After transferring $1,000,000 to account B: A = **-$999,584.50**
(available $0.00), B = $1,000,100.00. The transfer completes with no balance check at all.
Test: `test_transfer_larger_than_balance_is_rejected` (strict xfail). The model never proposed an "amount exceeds balance"
case, the most obvious banking edge case; the closest it got was "maximum allowed amount", expecting acceptance.

## Where the agent (LLM) was wrong or flaky
- **Infeasible proposals, every run:** it kept proposing "transfer from/to a non-existent account" with `index 2`, even when told
  the only valid values are 0 and 1 (and after a validation-error retry). Whole-answer validation failed 2 runs in a row; item-by-item
  validation (keep feasible cases, count the rest) fixed the pipeline. The page has no control that can select a non-existent account.
- **Boilerplate expectations:** 4 of 5 `expected` fields were the identical sentence "Reject transfer with error message", including
  the decimal case where it is wrong. The model pattern-matches "edge case => rejection".
- **Missed the balance dimension** entirely; it only reasoned about the amount field, because the snapshot does not show balances.
  Feeding it account balances in the prompt is the obvious next step.
- **Scoring is a keyword heuristic** (`expects_rejection`) on the model's own wording. It matched the model's text for all 5 cases,
  but it is an approximation; a real check needs the structured, checkable expectations proposed on Day 9.
- **Flakiness of the app under test: none.** Each case run twice gave identical outcomes (0 flaky of 5). 0 MCP tool errors.

## MCP and harness gotchas learned
- After every action the server returns a file path, not the snapshot; take a snapshot to read the result.
- ParaBank fills its account dropdowns asynchronously: wait before reading options, or you get an empty list.
- `browser_type` with empty text is pointless; skip typing for the empty-amount case.
- Refs inside frames are prefixed (`f1e34`).
- A shared test user is unsafe for tests that move money: one `$1,000,000` transfer left the account at -$999,584. Tests that
  change balances use the new `new_customer_page` fixture (fresh customer per test).

## Tests created by hand
`tests/test_transfer_edge_cases.py` (new `TransferPage` page object):
2 strict xfails documenting the bugs above, plus 2 passing tests (empty amount shows an error; decimal amount is accepted).
