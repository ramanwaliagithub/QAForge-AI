import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_amount_is_not_a_number(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.wait_for_url("accounts")
    accounts.click(get_by_role("button", name="Bill Payment"))
    accounts.fill(get_by_label("Amount"), "abc")
    accounts.click(get_by_role("button", name="Make Payment"))
    expect(logged_in_page.error_message).to_contain_text("Invalid amount")
