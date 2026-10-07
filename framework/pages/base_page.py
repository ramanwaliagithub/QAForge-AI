from playwright.sync_api import Locator, Page, expect


class BasePage:
    """Shared helpers. Page objects keep locators and actions; tests keep assertions."""

    path = "/index.htm"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def open(self):
        self.page.goto(f"{self.base_url}{self.path}")
        return self

    def click(self, locator: Locator):
        expect(locator).to_be_visible()
        locator.click()

    def fill(self, locator: Locator, value: str):
        expect(locator).to_be_visible()
        locator.fill(value)

    def wait_for_url(self, fragment: str):
        self.page.wait_for_url(f"**{fragment}*")

    @property
    def error_message(self) -> Locator:
        return self.page.locator("p.error")
