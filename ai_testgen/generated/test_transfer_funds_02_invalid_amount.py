import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_invalid_transfer_amount(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.wait_for_url("accounts")
    accounts.open_new_account("SAVINGS")
    accounts.wait_for_url("accounts")
    accounts.open_new_account("CHECKING")
    accounts.wait_for_url("accounts")
    accounts.click(get_by_role("button", name="Transfer Funds"))
    accounts.fill(get_by_label("Transfer Amount"), "-50")
    accounts.fill(get_by_label("From Account"), "SAVINGS")
    accounts.fill(get_by_label("To Account"), "CHECKING")
    accounts.click(get_by_role("button", name="Transfer"))
    expect(accounts.error_message).to_contain_text("Invalid account number or transfer amount")
