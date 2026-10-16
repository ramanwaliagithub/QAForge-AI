"""Capture page snapshots of the screens under test: `uv run python -m scripts.capture_snapshots`."""
import os
import uuid

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from ai_testgen.grounding import STORY_PAGES, capture_page, save_snapshot
from framework.pages import RegisterPage

load_dotenv()
base_url = os.getenv("BASE_URL", "http://localhost:8080/parabank")
user = dict(first_name="Qa", last_name="Forge", street="1 Test Street", city="Testville", state="CA",
            zip_code="90210", phone="5550100", ssn="123-45-6789",
            username=f"snap_{uuid.uuid4().hex[:8]}", password="Passw0rd!")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    RegisterPage(page, base_url).open().register(**user)
    page.get_by_role("link", name="Log Out").wait_for()
    for path in sorted({p for pages in STORY_PAGES.values() for p in pages}):
        snap = capture_page(page, base_url, path)
        print(f"saved {save_snapshot(snap)}  ({len(snap['elements'])} elements)")
    browser.close()
