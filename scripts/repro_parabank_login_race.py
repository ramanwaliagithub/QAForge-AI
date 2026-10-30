"""Reproduce a ParaBank race: a FAILED login sometimes returns another customer's logged-in session.

Needs local ParaBank (`docker compose up -d`). Usage:
    uv run python -m scripts.repro_parabank_login_race [attempts_per_thread]

Two threads submit logins with an unknown user while two other threads log in as a real customer.
Outcome per bad login: `error` (correct), `leaked_session` (the page shows a Log Out link, i.e. it is logged in
as somebody), or `other`. Observed on 2026-10-22: 2 `leaked_session` out of 80 bad logins (~2.5%); with only
bad logins, or bad logins plus registrations, 0 of 100.
"""
import collections
import os
import sys
import threading
import uuid

from playwright.sync_api import sync_playwright

from framework.pages import RegisterPage

BASE = os.getenv("BASE_URL", "http://localhost:8080/parabank")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
results, lock, user = collections.Counter(), threading.Lock(), {}


def _login(page, username, password):
    page.goto(f"{BASE}/index.htm")
    page.locator("input[name='username']").fill(username)
    page.locator("input[name='password']").fill(password)
    page.get_by_role("button", name="Log In").click()
    page.wait_for_load_state()


def bad_logins(browser, n):
    """Try `n` logins with an unknown user, each in its own browser context, and count the outcomes."""
    for _ in range(n):
        ctx = browser.new_context()
        page = ctx.new_page()
        _login(page, "no_such_user", "wrong_password")
        outcome = ("leaked_session" if page.get_by_role("link", name="Log Out").count()
                   else "error" if page.locator("p.error").count() else "other")
        with lock:
            results[outcome] += 1
        ctx.close()


def good_logins(browser, n):
    for _ in range(n):
        ctx = browser.new_context()
        _login(ctx.new_page(), user["name"], "Passw0rd!")
        ctx.close()


def in_own_browser(fn, n):  # Playwright's sync API is not thread-safe: one playwright + browser per thread
    with sync_playwright() as p:
        browser = p.chromium.launch()
        fn(browser, n)
        browser.close()


with sync_playwright() as p:
    browser = p.chromium.launch()
    user["name"] = "race_" + uuid.uuid4().hex[:8]
    page = browser.new_page()
    RegisterPage(page, BASE).open().register(
        first_name="Qa", last_name="Forge", street="1 St", city="C", state="CA", zip_code="90210",
        phone="555", ssn="123-45-6789", username=user["name"], password="Passw0rd!")
    page.wait_for_load_state()
    browser.close()

threads = [threading.Thread(target=in_own_browser, args=(fn, N)) for fn in (bad_logins, bad_logins, good_logins, good_logins)]
[t.start() for t in threads]
[t.join() for t in threads]
print(dict(results))
