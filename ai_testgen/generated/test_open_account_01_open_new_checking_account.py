import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_open_checking_account(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/openaccount.htm")
    logged_in_page.locator("#type").select_option(index=0)
    logged_in_page.locator("#fromAccountId").select_option(index=0)
    logged_in_page.locator("input[value='Open New Account']").click()
    new_account_id = logged_in_page.locator("#newAccountId").text_content()
    expect(logged_in_page.locator("#resultPanel").get_by_text("Account Opened!")).to_be_visible()
    expect(logged_in_page.locator("#resultPanel").get_by_text("with a new checking account number")).to_be_visible()
    expect(logged_in_page.locator("#resultPanel").get_by_text(new_account_id)).to_be_visible()
    accounts = AccountsPage(logged_in_page, base_url)
    expect(accounts.accounts_table).to_contain_text(new_account_id)
