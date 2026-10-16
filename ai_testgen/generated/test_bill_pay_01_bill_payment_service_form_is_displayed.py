import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_bill_payment_service_form_is_displayed(logged_in_page, base_url):
    logged_in_page.goto(f"{base_url}/paybills.htm")
    expect(logged_in_page.get_by_role("heading", name="Bill Payment Service")).to_be_visible()
    expect(logged_in_page.get_by_text("Payee Name")).to_be_visible()
    expect(logged_in_page.get_by_text("Address")).to_be_visible()
    expect(logged_in_page.get_by_text("City")).to_be_visible()
    expect(logged_in_page.get_by_text("State")).to_be_visible()
    expect(logged_in_page.get_by_text("Zip")).to_be_visible()
    expect(logged_in_page.get_by_text("Phone")).to_be_visible()
    expect(logged_in_page.get_by_text("Account Number")).to_be_visible()
    expect(logged_in_page.get_by_text("Account Number")).to_be_visible()
    expect(logged_in_page.get_by_text("Amount")).to_be_visible()
    expect(logged_in_page.get_by_text("From Account")).to_be_visible()
