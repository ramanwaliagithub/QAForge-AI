import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.smoke
def test_open_savings_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    new_id = accounts.open_new_account("SAVINGS")
    expect(accounts.open_account_result).to_contain_text("Account Opened!")
    assert new_id.isdigit()

    accounts.open()
    expect(accounts.account_links.filter(has_text=new_id)).to_have_count(1)
