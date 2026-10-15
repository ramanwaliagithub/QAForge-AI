import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_select_account_not_owned_by_customer(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.wait_for_url("transfer.htm")
    amount_locator = page.locator("#amount")
    amount_locator.fill("50")
    from_account_locator = page.locator("#fromAccountId")
    from_account_locator.select_option(registered_user["account_ids"][0])  # Select an account not owned by the customer
    to_account_locator = page.locator("#toAccountId")
    to_account_locator.select_option(registered_user["account_ids"][1])  # Select the 'to' account
    submit_locator = page.locator("input[value='Transfer']")
    submit_locator.click()
    expect(page.locator(".error-message")).to_be_visible()
