# 001: BillPay page object and 5 tests

Status: ready        Checked against the app on: 2026-11-03 (local ParaBank in Docker, `http://localhost:8080/parabank`)

## Goal

Cover ParaBank's Bill Pay screen (`/billpay.htm`) with a page object that follows the other page objects in this repo and
five UI tests that check what a customer would check: the form is there, each kind of invalid input is refused with the right
message, and a valid payment is confirmed and really takes the money out of the account.

## Context

Read these first:
- `framework/pages/transfer_page.py`: the model to copy for a page object (properties for locators, one method per user action,
  **no assertions**, result heading waited for inside the action).
- `framework/pages/base_page.py`: `click`, `fill` and `select_option` are the only way a page object may act. They are also where
  self-healing hooks in.
- `tests/test_transfer_edge_cases.py`: the model for tests (assertions in the test, `new_customer_page` for tests that change a balance).
- `conftest.py`: fixtures `logged_in_page` (shared customer; do not change its balance) and `new_customer_page` (a brand-new
  customer with exactly one account; use it whenever a test changes a balance or counts accounts).
- `docs/locator-quality-checklist.md`: locator rules. They are enforced by `tests/test_locator_quality.py`.

Facts about the app that cannot be guessed:
- URL: `{base_url}/billpay.htm`. Heading "Bill Payment Service". Button "Send Payment" (an `input type=button`, role `button`).
- The form fields have no accessible name. Use the form `name` attribute (a stable contract), as `RegisterPage` does:

  | Field | `name` attribute | Label on screen |
  |---|---|---|
  | payee name | `payee.name` | Payee Name: |
  | address | `payee.address.street` | Address: |
  | city | `payee.address.city` | City: |
  | state | `payee.address.state` | State: |
  | zip code | `payee.address.zipCode` | Zip Code: |
  | phone | `payee.phoneNumber` | Phone #: |
  | account | `payee.accountNumber` | Account #: |
  | verify account | `verifyAccount` | Verify Account #: |
  | amount | `amount` | Amount: $ |
  | from account (a `<select>`) | `fromAccountId` | From account #: |

  The `<select>` has **no id**. `#fromAccountId` exists only on the confirmation page, where it is a `<span>` holding the account
  number, so do not use it for the dropdown.
- Validation is **client-side**: submitting does not leave the page and sends nothing. All 13 messages are in the DOM from the start with
  `display:none` (so a text locator finds them even when they are not shown: assert **visibility**, not presence). After "Send Payment"
  the ones that apply become visible. Each is a `<span class="error">` with a hand-written id.

  | Id | Text | Shown when |
  |---|---|---|
  | `validationModel-name` | Payee name is required. | payee name empty |
  | `validationModel-address` | Address is required. | address empty |
  | `validationModel-city` | City is required. | city empty |
  | `validationModel-state` | State is required. | state empty |
  | `validationModel-zipCode` | Zip Code is required. | zip code empty |
  | `validationModel-phoneNumber` | Phone number is required. | phone empty |
  | `validationModel-account-empty` | Account number is required. | account empty |
  | `validationModel-account-invalid` | Please enter a valid number. | account not numeric |
  | `validationModel-verifyAccount-empty` | Account number is required. | verify account empty |
  | `validationModel-verifyAccount-invalid` | Please enter a valid number. | verify account not numeric |
  | `validationModel-verifyAccount-mismatch` | The account numbers do not match. | the two entries differ |
  | `validationModel-amount-empty` | The amount cannot be empty. | amount empty |
  | `validationModel-amount-invalid` | Please enter a valid amount. | amount not a number (e.g. `abc`) |

  **"Account number is required." and "Please enter a valid number." each appear twice on the page** (account and verify account), so a
  locator by that text alone matches two elements and fails in strict mode. There is also a `p.error` with an internal-error text that is
  never shown in these flows; do not use `p.error`.
- After a valid payment the page stays on `/billpay.htm` and replaces the form with a confirmation (no navigation, so wait for the
  heading, not the URL):
  heading "Bill Payment Complete", then "Bill Payment to **{payee}** in the amount of **${amount}** from account **{account}** was successful."
  (the three values are in `<span id="payeeName">`, `<span id="amount">`, `<span id="fromAccountId">`), then "See Account Activity for more details."
  The amount is shown with two decimals ($25.50).
- A brand-new customer has one account. Paying 25.50 from it lowers its balance on `/overview.htm` by exactly 25.50, and the account's
  activity page lists a debit row whose transaction text is "Bill Payment to {payee}". The overview and activity tables fill in
  asynchronously: wait for the rows (web-first assertion), never read them straight after `goto`.
- The app accepts amounts of 0 and -5 and "successfully" pays them (checked 2026-11-03). That is an application bug, not a requirement:
  **do not write a test that depends on it** (see Out of scope).
- Valid data that works: payee "Electric Co", address "9 Grid Rd", city "Powertown", state "NV", zip "89101", phone "5550199",
  account "12345" (twice), amount "25.50".

## Deliverables

| Path | Change |
|---|---|
| `framework/pages/bill_pay_page.py` | create: `BillPayPage(BasePage)` |
| `framework/pages/__init__.py` | edit: export `BillPayPage` (add to the import and to `__all__`) |
| `tests/test_bill_pay.py` | create: exactly the 5 tests below |
| `tests/test_locator_quality.py` | edit **only if needed**: add an `ACCEPTED` entry, with the reason, for each non-semantic selector the page object uses |

Public interface of the page object (names and signatures are fixed; bodies are yours):
```python
class BillPayPage(BasePage):
    path = "/billpay.htm"
    FIELDS: dict[str, str]                       # keyword name -> form `name` attribute, e.g. {"payee_name": "payee.name", ...}
    def open(self) -> "BillPayPage": ...         # returns once the form is usable (the From dropdown lists an account)
    def fill_payment(self, **values: str) -> "BillPayPage": ...   # keys are the FIELDS names; omitted fields stay empty
    def submit(self) -> "BillPayPage": ...       # clicks "Send Payment"
    def pay(self, **values: str) -> "BillPayPage": ...            # fill_payment + submit
    def field_error(self, message_id: str) -> Locator: ...        # ONE visible-checkable error span, e.g. "verifyAccount-mismatch"
    @property
    def result_heading(self) -> Locator: ...     # "Bill Payment Complete"
    @property
    def result_message(self) -> Locator: ...     # the "Bill Payment to ... was successful." paragraph
    @property
    def from_account(self) -> Locator: ...       # the From account dropdown
```
`field_error` takes the part of the id after `validationModel-` and returns a locator that matches exactly one element.

## Acceptance criteria

1. `BillPayPage` exists in `framework/pages/bill_pay_page.py`, subclasses `BasePage`, has the interface above and is importable as
   `from framework.pages import BillPayPage`.
2. The page object contains no assertions and no `expect(...)` on product behaviour (waiting for the form to be usable inside `open` is allowed).
3. The page object acts only through `self.click`, `self.fill`, `self.select_option`.
4. `tests/test_bill_pay.py` contains exactly the five tests named below; `pytest --collect-only tests/test_bill_pay.py` reports 5.
5. Each test ends with at least one web-first assertion (`expect(...)`) on something a user can see; none relies on the absence of an error
   alone to pass. "No result shown" is checked together with the message that should be shown.
6. No `time.sleep`, no `wait_for_timeout`, no `.nth()`, `.first`, `.last`, no XPath, no CSS class or structural selectors other than the
   hand-written `validationModel-*` ids.
7. Tests are independent: each opens its own page, none depends on another's side effects, and the one that changes a balance uses
   `new_customer_page`.
8. Test data is defined once per module (a constant or a small helper), not repeated in every test.
9. `tests/test_bill_pay.py` passes three times in a row with `-n 3 --reruns=0`.
10. The existing checks still pass: `tests/test_locator_quality.py`, `tests/test_lint.py`, `tests/test_docstrings.py`, `tests/test_sources_parse.py`.
11. No file outside the Deliverables table is changed.

Tests (name: what it asserts):
- `test_bill_pay_form_shows_every_field_and_the_customers_account`: uses `new_customer_page`. The heading "Bill Payment Service" is visible, all nine
  input fields are visible, and the From dropdown lists exactly one account.
- `test_empty_submit_requires_every_field`: submitting an empty form shows the nine "required" messages that apply to an empty form (name, address,
  city, state, zip, phone, account, verify account, amount) as visible, and no confirmation.
- `test_mismatched_account_numbers_are_refused`: all fields valid but the verify account differs: "The account numbers do not match." is visible and
  there is no confirmation.
- `test_non_numeric_amount_is_refused`: all fields valid but the amount is `abc`: "Please enter a valid amount." is visible and there is no confirmation.
- `test_successful_payment_is_confirmed_and_debits_the_account`: uses `new_customer_page`. Pay the valid data. The confirmation shows the payee, `$25.50` and
  the number of the account the money came from; then, on the overview, that account's balance is lower by exactly 25.50 than before the payment, and its
  activity lists "Bill Payment to Electric Co".

## Constraints

- Follow `docs/locator-quality-checklist.md`. The form fields and the validation spans have no accessible name, so those selectors are non-semantic:
  register each one in `ACCEPTED` in `tests/test_locator_quality.py` with a reason (the test fails until you do). Prefer a semantic locator everywhere
  one exists (the heading, the button, the confirmation text).
- Reuse `AccountsPage` or plain Playwright in the test for reading the overview and activity. Do not copy its code into `BillPayPage`.
- Docstring on the module, the class and every public method of 8 or more lines (`tests/test_docstrings.py` enforces it). Type hints on the interface above.
- No new dependency.

## Out of scope

- Amounts of 0, negative amounts and "payment larger than the balance". ParaBank accepted 0 and -5 when checked on 2026-11-03; the
  overdraft case is the same class of bug as on Transfer (`docs/mcp-findings.md`) and was not checked for Bill Pay.
- Tests for the other nine fields being non-numeric, phone/zip formats, or long values.
- Changing any existing page object, fixture, test, or `conftest.py`. If you think one needs a change, say so in your report.
- The `ai_testgen/` folder, the healing code, `README.md`, `PLAN.md`, `docs/`.
- Parametrizing the five tests into more than five collected items.

## Verification

```bash
uv run pytest tests/test_bill_pay.py -q --reruns=0 -p no:cacheprovider            # expect: 5 passed
for i in 1 2 3; do uv run pytest tests/test_bill_pay.py -q --reruns=0 -n 3 -p no:cacheprovider; done   # expect: 5 passed, three times
uv run pytest tests/test_locator_quality.py tests/test_lint.py tests/test_docstrings.py tests/test_sources_parse.py -q --reruns=0   # expect: all passed
git status --short                                                                # expect: only the Deliverables paths
```

## Open questions

- How `field_error` finds exactly one element is left to you. Say which locator you chose and why it is unique.
- If a criterion cannot be met as written, say which one and what you did instead; do not change the spec.
