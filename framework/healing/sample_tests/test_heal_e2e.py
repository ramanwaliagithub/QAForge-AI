"""Tests run BY tests/test_healing_plugin.py in a subprocess to check `pytest --heal` end to end. Not run directly."""
from playwright.sync_api import expect

from framework.healing.sample_tests.test_broken_locators import AmountIdRenamed, SubmitTextChanged
from framework.pages import TransferPage


def test_e2e_amount_id_renamed(new_customer_page, base_url):
    """Broken locator; with --heal it should be healed and the transfer should complete."""
    transfer = AmountIdRenamed(new_customer_page, base_url).open().transfer("10")
    expect(transfer.success_heading).to_be_visible()


def test_e2e_button_text_changed(new_customer_page, base_url):
    transfer = SubmitTextChanged(new_customer_page, base_url).open().transfer("10")
    expect(transfer.success_heading).to_be_visible()


def test_e2e_assertion_fails_with_a_working_page_object(new_customer_page, base_url):
    """Nothing is wrong with any locator: the ASSERTION is wrong. Healing must never touch this."""
    transfer = TransferPage(new_customer_page, base_url).open().transfer("10")
    expect(transfer.success_heading).to_have_text("Transfer Done!")
