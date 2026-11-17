"""Shared fixtures: browser and page (tracing, failure artifacts, failure collection), registered users,
page objects, and the --heal plugin.
"""

import os
import random
import re
import uuid
from pathlib import Path

import allure
import pytest
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright

from framework.data import DataFactory, seed_for_worker
from framework.healing.collector import DEFAULT_DIR, collect_failure_context
from framework.logging_utils import get_logger
from framework.pages import LoginPage, RegisterPage

pytest_plugins = ["framework.healing.plugin"]  # --heal: opt-in self-healing (see framework/healing/plugin.py)

load_dotenv()
log = get_logger("qaforge.tests")

# The shared public ParaBank demo is sometimes slow; Playwright's 5s default caused flaky failures.
expect.set_options(timeout=int(os.getenv("EXPECT_TIMEOUT_MS", "10000")))


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", default=False, help="Show the browser window")
    parser.addoption("--slowmo", type=int, default=0, help="Slow down actions by N ms")
    parser.addoption("--data-seed", type=int, default=None, help="Seed for generated test data (printed in the header; reuse it to replay a run)")


def pytest_configure(config):
    """Choose the data seed once, in the controller, so every xdist worker derives its own from the same base."""
    if not hasattr(config, "workerinput"):
        chosen = config.getoption("--data-seed")
        config._data_seed = random.SystemRandom().getrandbits(31) if chosen is None else chosen
    else:
        config._data_seed = config.workerinput["data_seed"]


def pytest_configure_node(node):
    node.workerinput["data_seed"] = node.config._data_seed


def pytest_report_header(config):
    return f"test data seed: {config._data_seed} (replay with --data-seed={config._data_seed})"


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("BASE_URL", "http://localhost:8080/parabank")


@pytest.fixture(scope="session")
def browser(request):
    """One Chromium per test session (headless unless `--headed`)."""
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
    if call.when == "call":
        item.excinfo_call = call.excinfo  # the exception object (None on pass); the failure collector needs it


ARTIFACTS_DIR = Path("test-results")


def collect_failure(request, page):
    """If the test body failed, write the failure context (error, page state, screenshot) for the healer."""
    excinfo = getattr(request.node, "excinfo_call", None)
    failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
    if failed and excinfo is not None:
        collect_failure_context(page, request.node.nodeid, excinfo.value, Path(os.getenv("FAILURE_DIR", DEFAULT_DIR)))


@pytest.fixture
def page(browser, request):
    """A fresh browser context and page per test, with tracing. On failure it saves a screenshot and trace (Allure and
    reports/failures) and the healing failure context.
    """
    context = browser.new_context()
    context.set_default_timeout(int(os.getenv("ACTION_TIMEOUT_MS", "15000")))  # fail bad locators in 15s, not 30s
    context.tracing.start(screenshots=True, snapshots=True, sources=False)
    page = context.new_page()
    yield page
    failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
    if failed:
        collect_failure(request, page)
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


def register_new_customer(browser, base_url, attempts: int = 3):
    """Register a brand-new customer through the UI in a fresh browser context.

    Returns (context, page, user); the page is logged in because registration logs the customer in.
    ParaBank sometimes rejects a brand-new username ("This username already exists") or stalls when several
    workers register at once, so retry with a new username instead of failing the test.
    """
    user = {
        "first_name": "Qa",
        "last_name": "Forge",
        "street": "1 Test Street",
        "city": "Testville",
        "state": "CA",
        "zip_code": "90210",
        "phone": "5550100",
        "ssn": "123-45-6789",
        "password": "Passw0rd!",
    }
    last_error = None
    for attempt in range(1, attempts + 1):
        user["username"] = f"qaforge_{uuid.uuid4().hex[:10]}"
        context = browser.new_context()
        context.set_default_timeout(int(os.getenv("ACTION_TIMEOUT_MS", "15000")))
        page = context.new_page()
        try:
            RegisterPage(page, base_url).open().register(**user)
            page.get_by_role("link", name="Log Out").wait_for(timeout=10_000)
            return context, page, user
        except PlaywrightTimeoutError as e:
            last_error = e
            log.warning("registration_retry", extra={"attempt": attempt, "username": user["username"]})
            context.close()
    raise RuntimeError(f"Could not register a test user after {attempts} attempts: {last_error}")


@pytest.fixture(scope="session")
def registered_user(browser, base_url):
    """A fresh ParaBank customer, created once per session (once per worker under xdist)."""
    context, _page, user = register_new_customer(browser, base_url)
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


@pytest.fixture
def new_customer_page(browser, base_url, request):
    """A page logged in as a brand-new customer (own context, own accounts).

    Use for tests that change balances, so they cannot pollute the shared `registered_user`.
    """
    context, page, _user = register_new_customer(browser, base_url)
    yield page
    collect_failure(request, page)
    context.close()


@pytest.fixture(scope="session")
def data_factory(request):
    """Seeded test data for this worker (Faker identities, unique usernames, money). The seed is in the report header."""
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    return DataFactory(seed=seed_for_worker(request.config._data_seed, worker_id))
