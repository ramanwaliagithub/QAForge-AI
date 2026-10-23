"""Deliberately broken tests that generate realistic failure samples for the healing work.

NOT part of the normal suite (they all fail on purpose and live outside `testpaths`).
Generate the samples with:  uv run python -m scripts.make_failure_samples
"""
from playwright.sync_api import expect

from framework.pages import TransferPage


class AmountIdRenamed(TransferPage):
    """UI refactor: the amount input's id changed from #amount to #amt."""

    @property
    def amount(self):
        return self.page.locator("#amt")


class SubmitTextChanged(TransferPage):
    """UI copy change: the button now reads "Transfer Money"."""

    @property
    def submit_button(self):
        return self.page.get_by_role("button", name="Transfer Money", exact=True)


class FromAccountTooGeneric(TransferPage):
    """A locator that is too vague: `option` matches the options of both dropdowns."""

    @property
    def from_account(self):
        return self.page.locator("option")


# --- three broken locators (healing candidates) ---

def test_sample_id_renamed(new_customer_page, base_url):
    AmountIdRenamed(new_customer_page, base_url).open().transfer("10")


def test_sample_button_text_changed(new_customer_page, base_url):
    SubmitTextChanged(new_customer_page, base_url).open().transfer("10")


def test_sample_locator_too_generic(new_customer_page, base_url):
    FromAccountTooGeneric(new_customer_page, base_url).open().transfer("10")


# --- two controls that are NOT locator failures ---

def test_sample_expect_on_missing_element(new_customer_page, base_url):
    """Could be a renamed heading or an intentional change: ambiguous ("maybe")."""
    TransferPage(new_customer_page, base_url).open().transfer("10")
    expect(new_customer_page.get_by_role("heading", name="Transfer Completed!")).to_be_visible()


def test_sample_wrong_text_on_found_element(new_customer_page, base_url):
    """The element exists and shows different text: a possible product bug, never to be healed."""
    transfer = TransferPage(new_customer_page, base_url).open().transfer("10")
    expect(transfer.success_heading).to_have_text("Transfer Done!")
