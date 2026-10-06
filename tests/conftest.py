import os

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

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


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
