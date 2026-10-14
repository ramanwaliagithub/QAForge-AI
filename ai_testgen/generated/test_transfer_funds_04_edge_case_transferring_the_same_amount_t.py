import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage


@pytest.mark.ai
def test_transfer_same_amount_same_account(logged_in_page, base_url):
    accounts = AccountsPage(logged_in_page, base_url)
    accounts.open_new_account("SAVINGS")  # Create a new savings account
    accounts.open_new_account("CHECKING")  # Create a new checking account

    # Navigate to the Transfer Funds page
    logged_in_page.click(get_by_role("button", name="Transfer Funds"))
    expect(logged_in_page).to_have_url(f"{base_url}/transferFunds.htm")

    # Enter a positive amount (e.g. 50)
    logged_in_page.fill(get_by_label("Transfer Amount"), "50")

    # Select the 'from' account
    logged_in_page.click(get_by_text("Select an account to transfer from"))
    logged_in_page.click(get_by_text("Checking 1234"))

    # Select the 'to' account
    logged_in_page.click(get_by_text("Select an account to transfer to"))
    logged_in_page.click(get_by_text("Savings 5678"))

    # Submit the transfer
    logged_in_page.click(get_by_role("button", name="Transfer Funds"))

    # Submit the transfer again
    logged_in_page.click(get_by_role("button", name="Transfer Funds"))

    # Assert the expected result
    expect(logged_in_page).to_have_url(f"{base_url}/transferFunds.htm")
    expect(logged_in_page).to_have_text("Transfer Complete!")
    expect(logged_in_page).to_have_text("50")
    expect(logged_in_page).to_have_text("1234")
    expect(logged_in_page).to_have_text("5678")
