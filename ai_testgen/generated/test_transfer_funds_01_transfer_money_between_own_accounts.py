import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_transfer_money_between_own_accounts(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.wait_for_url("accounts")
    accounts.open_new_account("SAVINGS")
    accounts.open_new_account("CHECKING")
    accounts.wait_for_url("transferFunds")
    accounts.fill("amount", "50")
    accounts.click("fromAccount")
    accounts.click("toAccount")
    accounts.click("submit")
    expect(logged_in_page).to_have_url("transferFunds")
    expect(logged_in_page).to_have_title("Transfer Funds")
    expect(logged_in_page).to_have_text("Transfer Complete!")
    expect(logged_in_page).to_have_text("50")
    expect(logged_in_page).to_have_text("SAVINGS")
    expect(logged_in_page).to_have_text("CHECKING")
