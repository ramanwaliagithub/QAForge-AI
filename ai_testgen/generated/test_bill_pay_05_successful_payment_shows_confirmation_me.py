import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_successful_payment_shows_confirmation(logged_in_page, base_url, registered_user):
    logged_in_page.goto(f"{base_url}/paybills.htm")
    logged_in_page.locator("#payee.name").fill(registered_user["first_name"])
    logged_in_page.locator("#payee.address.street").fill("123 Main St")
    logged_in_page.locator("#payee.address.city").fill("Anytown")
    logged_in_page.locator("#payee.address.state").select_option(index=0)
    logged_in_page.locator("#payee.address.zip").fill("12345")
    logged_in_page.locator("#accountNumber").fill("1234567890")
    logged_in_page.locator("#amount").fill("100")
    logged_in_page.locator("input[value='Pay with Checking']").click()
    expect(logged_in_page.get_by_text("Bill Payment Complete")).to_be_visible()
    expect(logged_in_page.get_by_text(registered_user["first_name"])).to_be_visible()
    expect(logged_in_page.get_by_text("100")).to_be_visible()
    expect(logged_in_page.get_by_text("1234567890")).to_be_visible()
