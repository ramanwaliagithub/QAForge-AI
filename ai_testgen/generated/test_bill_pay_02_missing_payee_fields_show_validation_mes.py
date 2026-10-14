import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_missing_payee_fields_show_validation_messages(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("SAVINGS")  # Open a new savings account to have a bill payee
    accounts.wait_for_url("account")
    accounts.click("Bill Pay")
    accounts.wait_for_url("billpay")
    accounts.fill("payee", "")  # Leave a required payee field blank
    accounts.click("Submit")
    expect(accounts.get_by_text("Error Message")).to_contain_text("is required")
