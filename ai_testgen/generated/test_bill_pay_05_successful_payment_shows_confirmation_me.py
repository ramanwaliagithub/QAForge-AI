import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage, LoginPage


@pytest.mark.ai
def test_successful_payment_confirmation(logged_in_page, base_url):
    # Navigate to the Bill Payment page
    logged_in_page.click(logged_in_page.get_by_role("menuitem", name="Bill Payment"))
    
    # Enter valid payee information and account numbers
    bill_payment_page = logged_in_page.get_by_text("Bill Payment")
    bill_payment_page.click()
    bill_payment_page.fill(bill_payment_page.get_by_label("Payee"), "Payee Name")
    bill_payment_page.fill(bill_payment_page.get_by_label("Account"), "Account Number")
    
    # Enter a valid amount
    bill_payment_page.fill(bill_payment_page.get_by_label("Amount"), "100.00")
    
    # Submit the form
    bill_payment_page.click(bill_payment_page.get_by_role("button", name="Make Payment"))
    
    # Assert the expected result
    expect(logged_in_page.get_by_text("Bill Payment Complete")).to_be_visible()
    expect(logged_in_page.get_by_text("Payee Name")).to_be_visible()
    expect(logged_in_page.get_by_text("100.00")).to_be_visible()
    expect(logged_in_page.get_by_text("Account Number")).to_be_visible()
