import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage, BasePage


@pytest.mark.ai
def test_account_number_entries_do_not_match(logged_in_page, base_url):
    logged_in_page.wait_for_url('billpay.htm')
    page = logged_in_page

    # Enter different account numbers in the two account number fields
    page.locator('input[name="payee.accountNumber"]').fill('123456789')
    page.locator('input[name="verifyAccount"]').fill('987654321')

    # Submit the form
    page.locator('input[value="Send Payment"]').click()

    # Assert the expected result
    error_message = page.get_by_role('alert').get_text()
    expect(error_message).to_contain_text('Account numbers do not match')
