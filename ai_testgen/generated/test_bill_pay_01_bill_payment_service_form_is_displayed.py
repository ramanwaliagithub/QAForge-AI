import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_bill_payment_form(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("SAVINGS")  # Open a new savings account to have an account to pay from
    accounts.wait_for_url("accounts")
    accounts.click(get_by_role("button", name="Pay Bills"))
    bill_payment_page = AccountsPage(logged_in_page, base_url)
    expect(bill_payment_page.get_by_role("form")).to_be_visible()
    expect(bill_payment_page.get_by_label("Payee Name")).to_be_visible()
    expect(bill_payment_page.get_by_label("Address")).to_be_visible()
    expect(bill_payment_page.get_by_label("City")).to_be_visible()
    expect(bill_payment_page.get_by_label("State")).to_be_visible()
    expect(bill_payment_page.get_by_label("Zip")).to_be_visible()
    expect(bill_payment_page.get_by_label("Phone")).to_be_visible()
    expect(bill_payment_page.get_by_label("Account Number")).to_be_visible()
    expect(bill_payment_page.get_by_label("Account Number (again)")).to_be_visible()
    expect(bill_payment_page.get_by_label("Amount")).to_be_visible()
    expect(bill_payment_page.get_by_label("From Account")).to_be_visible()
