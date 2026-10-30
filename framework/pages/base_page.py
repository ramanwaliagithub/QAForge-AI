"""Base page object: navigation and the action helpers (click, fill, select_option) through which every
page object acts, which is also where self-healing hooks in.
"""

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page

from framework.healing import runtime
from framework.logging_utils import get_logger

log = get_logger("qaforge.pages")


class BasePage:
    """Shared helpers. Page objects keep locators and actions; tests keep assertions."""

    path = "/index.htm"

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def open(self):
        log.info("open", extra={"page": type(self).__name__, "path": self.path})
        self.page.goto(f"{self.base_url}{self.path}")
        return self

    def _act(self, action: str, locator: Locator, perform):
        """Wait for the element, then perform the action. If a healer is active (--heal) and the locator itself is the
        problem, retry ONCE with the healed locator; otherwise (and always when healing is off) fail as before."""
        try:
            # wait_for (not expect): a missing element is a locator problem and raises a Playwright timeout, which the
            # failure collector classifies as `locator_not_found`. expect() is reserved for assertions in tests.
            locator.wait_for(state="visible")
            log.info(action, extra={"locator": str(locator)})
            perform(locator)
        except PlaywrightError as exc:
            healer = runtime.current()
            proposal = healer.heal(self.page, action, locator, exc) if healer else None
            if proposal is None:
                raise
            log.info("retry_with_healed_locator", extra={"action": action, "locator": proposal.event.suggestion})
            try:
                perform(proposal.locator)
            except PlaywrightError as retry_error:
                healer.confirm(proposal, ok=False)
                raise exc from retry_error  # the original failure is the one worth reading
            healer.confirm(proposal, ok=True)

    def click(self, locator: Locator):
        self._act("click", locator, lambda loc: loc.click())

    def fill(self, locator: Locator, value: str):
        self._act("fill", locator, lambda loc: loc.fill(value))

    def select_option(self, locator: Locator, *args, **kwargs):
        self._act("select_option", locator, lambda loc: loc.select_option(*args, **kwargs))

    def wait_for_url(self, fragment: str):
        self.page.wait_for_url(f"**{fragment}*")

    @property
    def error_message(self) -> Locator:
        return self.page.locator("p.error")
