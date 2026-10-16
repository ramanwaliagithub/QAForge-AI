import pytest
from playwright.sync_api import expect


@pytest.mark.ai
def test_update_profile_shows_confirmation(logged_in_page, base_url):
    logged_in_page.goto(f"{base_url}/updateprofile.htm")
    logged_in_page.locator("[id='customer.firstName']").fill("Changed")
    logged_in_page.locator("input[value='Update Profile']").click()
    expect(logged_in_page.get_by_role("heading", name="Profile Updated")).to_be_visible()


@pytest.mark.ai
def test_update_profile_requires_first_name(logged_in_page, base_url):
    logged_in_page.goto(f"{base_url}/updateprofile.htm")
    logged_in_page.locator("[id='customer.firstName']").fill("")
    logged_in_page.locator("input[value='Update Profile']").click()
    expect(logged_in_page.get_by_text("First name is required.")).to_be_visible()
