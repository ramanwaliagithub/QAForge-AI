"""Bill Pay screen (/billpay.htm): the form is there, each kind of invalid input is refused with the right message, and a
valid payment is confirmed and takes the money out of the account (spec: specs/001-billpay-page-and-tests.md).

Validation is client-side, so the invalid-input tests send nothing to the server and may use the shared customer. The one
test that really pays uses `new_customer_page`, so it cannot change the balance other tests see.
"""
import re
from decimal import Decimal

from playwright.sync_api import expect

from framework.pages import AccountsPage, BillPayPage

# Valid data that works (checked against ParaBank 2026-11-03). Tests start from this and change only what they test.
VALID_PAYMENT = {
    "payee_name": "Electric Co",
    "address": "9 Grid Rd",
    "city": "Powertown",
    "state": "NV",
    "zip_code": "89101",
    "phone": "5550199",
    "account": "12345",
    "verify_account": "12345",
    "amount": "25.50",
}
AMOUNT = Decimal(VALID_PAYMENT["amount"])

# The "required" messages that apply to an empty form: error span id (after `validationModel-`) -> text.
REQUIRED_MESSAGES = {
    "name": "Payee name is required.",
    "address": "Address is required.",
    "city": "City is required.",
    "state": "State is required.",
    "zipCode": "Zip Code is required.",
    "phoneNumber": "Phone number is required.",
    "account-empty": "Account number is required.",
    "verifyAccount-empty": "Account number is required.",
    "amount-empty": "The amount cannot be empty.",
}


def _record_payment_requests(page) -> list[str]:
    """URLs of the payment requests the browser sends from now on. A rejected form must send none (CLAUDE.md T4)."""
    sent: list[str] = []
    page.on("request", lambda r: sent.append(r.url) if r.method == "POST" and "/bank/billpay" in r.url else None)
    return sent


def _payment(**changes: str) -> dict[str, str]:
    """The valid payment with some fields replaced."""
    return {**VALID_PAYMENT, **changes}


def _money(amount: Decimal) -> str:
    """An amount the way ParaBank shows it on the overview: $1,234.50."""
    return f"${amount:,.2f}"


def _overview_row(page, account: str):
    """The overview row of one account (its link text is the account number)."""
    return page.get_by_role("row").filter(has=page.get_by_role("link", name=account, exact=True))


def test_bill_pay_form_shows_every_field_and_the_customers_account(new_customer_page, base_url):
    bill_pay = BillPayPage(new_customer_page, base_url).open()
    expect(bill_pay.heading).to_be_visible()
    for name in BillPayPage.FIELDS:
        expect(bill_pay.field(name)).to_be_visible()
    expect(bill_pay.from_account.get_by_role("option")).to_have_count(1)


def test_empty_submit_requires_every_field(logged_in_page, base_url):
    bill_pay = BillPayPage(logged_in_page, base_url).open()
    sent = _record_payment_requests(logged_in_page)
    bill_pay.pay()
    for message_id, text in REQUIRED_MESSAGES.items():
        expect(bill_pay.field_error(message_id)).to_be_visible()
        expect(bill_pay.field_error(message_id)).to_have_text(text)
    expect(bill_pay.result_heading).not_to_be_visible()
    assert not sent, f"a rejected form sent a payment request: {sent}"


def test_mismatched_account_numbers_are_refused(logged_in_page, base_url):
    bill_pay = BillPayPage(logged_in_page, base_url).open()
    sent = _record_payment_requests(logged_in_page)
    bill_pay.pay(**_payment(verify_account="54321"))
    expect(bill_pay.field_error("verifyAccount-mismatch")).to_be_visible()
    expect(bill_pay.field_error("verifyAccount-mismatch")).to_have_text("The account numbers do not match.")
    expect(bill_pay.result_heading).not_to_be_visible()
    assert not sent, f"a rejected form sent a payment request: {sent}"


def test_non_numeric_amount_is_refused(logged_in_page, base_url):
    bill_pay = BillPayPage(logged_in_page, base_url).open()
    sent = _record_payment_requests(logged_in_page)
    bill_pay.pay(**_payment(amount="abc"))
    expect(bill_pay.field_error("amount-invalid")).to_be_visible()
    expect(bill_pay.field_error("amount-invalid")).to_have_text("Please enter a valid amount.")
    expect(bill_pay.result_heading).not_to_be_visible()
    assert not sent, f"a rejected form sent a payment request: {sent}"


def test_successful_payment_is_confirmed_and_debits_the_account(new_customer_page, base_url):
    page = new_customer_page
    payee = VALID_PAYMENT["payee_name"]

    # Before: the customer's only account and its balance, from the overview (its table fills in asynchronously).
    accounts = AccountsPage(page, base_url).open()
    expect(accounts.account_links).to_have_count(1)
    account = accounts.account_links.inner_text()
    expect(_overview_row(page, account)).to_contain_text("$")
    balance_before = Decimal(re.search(r"\$([\d,]+\.\d{2})", _overview_row(page, account).inner_text()).group(1).replace(",", ""))

    bill_pay = BillPayPage(page, base_url).open()
    expect(bill_pay.from_account).to_have_value(account)
    bill_pay.pay(**VALID_PAYMENT)

    expect(bill_pay.result_heading).to_be_visible()
    expect(bill_pay.result_message).to_have_text(
        f"Bill Payment to {payee} in the amount of {_money(AMOUNT)} from account {account} was successful."
    )

    # After: the balance is lower by exactly the amount, and the account's activity lists the debit.
    accounts.open()
    # to_have_text compares the row's text content, where the cells run together: "591099$490.00$490.00"
    expect(_overview_row(page, account)).to_have_text(re.compile(rf"^{account}{re.escape(_money(balance_before - AMOUNT))}\$"))
    page.get_by_role("link", name=account, exact=True).click()
    debit_row = page.get_by_role("row").filter(has_text=f"Bill Payment to {payee}")
    expect(debit_row).to_have_text(re.compile(rf"Bill Payment to {payee}\s*{re.escape(_money(AMOUNT))}"))
