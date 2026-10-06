import pytest
from playwright.sync_api import expect


@pytest.mark.smoke
def test_login_page_loads(page, base_url):
    page.goto(f"{base_url}/index.htm")
    expect(page).to_have_title("ParaBank | Welcome | Online Banking")
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.get_by_role("button", name="Log In")).to_be_visible()


@pytest.mark.smoke
def test_invalid_login_shows_error(page, base_url):
    page.goto(f"{base_url}/index.htm")
    page.locator("input[name='username']").fill("no_such_user")
    page.locator("input[name='password']").fill("wrong_password")
    page.get_by_role("button", name="Log In").click()
    # The public demo answers "could not be verified" or "internal error" for unknown users,
    # so assert on the error being shown, not its exact wording.
    expect(page.locator("p.error")).to_be_visible()
