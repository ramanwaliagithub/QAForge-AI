import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_zero_initial_deposit_amount(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("CHECKING")
    accounts.fill(accounts.get_by_label("Initial Deposit").locator, "0")
    accounts.click(accounts.get_by_label("Submit").locator)
    expect(accounts.error_message).to_contain_text("The initial deposit must be greater than 0")
