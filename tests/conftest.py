import os
import re
import uuid
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from framework.pages import LoginPage, RegisterPage

load_dotenv()


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", default=False, help="Show the browser window")
    parser.addoption("--slowmo", type=int, default=0, help="Slow down actions by N ms")


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("BASE_URL", "https://parabank.parasoft.com/parabank")


@pytest.fixture(scope="session")
def browser(request):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not request.config.getoption("--headed"),
            slow_mo=request.config.getoption("--slowmo"),
        )
        yield browser
        browser.close()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Expose each phase's report on the item so fixtures can see if the test failed."""
    outcome = yield
    setattr(item, f"rep_{call.when}", outcome.get_result())


ARTIFACTS_DIR = Path("test-results")


@pytest.fixture
def page(browser, request):
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True, sources=False)
    page = context.new_page()
    yield page
    failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
    if failed:
        name = re.sub(r"[^\w.-]+", "_", request.node.nodeid)
        ARTIFACTS_DIR.mkdir(exist_ok=True)
        shot = page.screenshot(full_page=True)
        (ARTIFACTS_DIR / f"{name}.png").write_bytes(shot)
        allure.attach(shot, name="screenshot", attachment_type=allure.attachment_type.PNG)
        trace_path = ARTIFACTS_DIR / f"{name}.zip"
        context.tracing.stop(path=str(trace_path))
        allure.attach.file(str(trace_path), name="trace.zip", extension="zip")
    else:
        context.tracing.stop()
    context.close()


@pytest.fixture(scope="session")
def registered_user(browser, base_url):
    """A fresh ParaBank customer, created once per session (once per worker under xdist)."""
    user = {
        "first_name": "Qa",
        "last_name": "Forge",
        "street": "1 Test Street",
        "city": "Testville",
        "state": "CA",
        "zip_code": "90210",
        "phone": "5550100",
        "ssn": "123-45-6789",
        "username": f"qaforge_{uuid.uuid4().hex[:10]}",
        "password": "Passw0rd!",
    }
    context = browser.new_context()
    page = context.new_page()
    RegisterPage(page, base_url).open().register(**user)
    page.get_by_role("link", name="Log Out").wait_for()
    context.close()
    return user


@pytest.fixture
def login_page(page, base_url):
    return LoginPage(page, base_url).open()


@pytest.fixture
def logged_in_page(page, base_url, registered_user):
    LoginPage(page, base_url).open().login(registered_user["username"], registered_user["password"])
    page.get_by_role("link", name="Log Out").wait_for()
    return page
