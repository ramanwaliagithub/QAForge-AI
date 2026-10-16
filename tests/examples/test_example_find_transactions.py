import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_find_by_amount_rejects_empty_amount(logged_in_page, base_url):
    logged_in_page.goto(f"{base_url}/findtrans.htm")
    logged_in_page.locator("#findByAmount").click()
    expect(logged_in_page.get_by_text("Invalid amount")).to_be_visible()
