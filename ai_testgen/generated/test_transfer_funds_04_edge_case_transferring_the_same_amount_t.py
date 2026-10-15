import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_transfer_same_amount_same_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.wait_for_url("transfer.htm")
    amount_locator = page.locator("#amount")
    amount_locator.fill("50")
    from_account_locator = page.locator("#fromAccountId")
    from_account_locator.select_option(registered_user["account1"])
    to_account_locator = page.locator("#toAccountId")
    to_account_locator.select_option(registered_user["account2"])
    submit_locator = page.locator("input[value='Transfer']")
    submit_locator.click()
    expect(page.locator(".error-message")).not_to_be_visible()
    submit_locator.click()
    expect(page.locator(".error-message")).not_to_be_visible()
    expect(page.locator(".result")).to_contain_text(f"Transfer Complete! with amount 50 and account ids {registered_user['account1']} and {registered_user['account2']}")
