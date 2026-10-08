import os

import pytest
from playwright.sync_api import expect


@pytest.mark.skipif(not os.getenv("DEMO_FAIL"), reason="set DEMO_FAIL=1 to see failure artifacts")
def test_deliberate_failure(login_page):
    """Fails on purpose to prove a screenshot and trace are saved."""
    expect(login_page.page).to_have_title("this title is wrong on purpose", timeout=1000)
