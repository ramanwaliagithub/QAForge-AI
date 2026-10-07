import pytest
from playwright.sync_api import expect


@pytest.mark.smoke
def test_login_page_loads(login_page):
    expect(login_page.page).to_have_title("ParaBank | Welcome | Online Banking")
    expect(login_page.username).to_be_visible()
    expect(login_page.password).to_be_visible()
    expect(login_page.submit).to_be_visible()


@pytest.mark.smoke
def test_valid_login(login_page, registered_user):
    login_page.login(registered_user["username"], registered_user["password"])
    expect(login_page.logout_link).to_be_visible()
    expect(login_page.page.get_by_role("heading", name="Accounts Overview")).to_be_visible()


@pytest.mark.smoke
def test_invalid_login_shows_error(login_page):
    login_page.login("no_such_user", "wrong_password")
    # The public demo answers "could not be verified" or "internal error" for unknown users,
    # so assert on the error being shown, not its exact wording.
    expect(login_page.error_message).to_be_visible()
