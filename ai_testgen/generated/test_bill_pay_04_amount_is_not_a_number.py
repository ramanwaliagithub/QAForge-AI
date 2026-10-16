import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_amount_is_not_a_number(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/payees.htm")
    logged_in_page.locator("#payeeName").click()
    logged_in_page.locator("#payeeName").fill("Test Payee")
    logged_in_page.locator("#findPayees").click()
    logged_in_page.locator("#payeeList").locator("text=Test Payee").click()
    logged_in_page.locator("#amount").fill("abc")
    logged_in_page.locator("input[value='Make Payment']").click()
    expect(logged_in_page.get_by_text("Invalid amount")).to_be_visible()
