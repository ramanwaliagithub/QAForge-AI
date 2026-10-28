"""Transfer Funds edge cases found by exploratory testing (see docs/mcp-findings.md).

The two xfail tests describe the CORRECT behaviour that ParaBank currently violates. They are strict: if
ParaBank is ever fixed they XPASS and fail the run, which tells us to remove the marker.
"""
import pytest
from playwright.sync_api import expect

from framework.pages import AccountsPage, TransferPage


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ParaBank bug: a negative transfer amount is accepted")
def test_negative_amount_is_rejected(new_customer_page, base_url):
    transfer = TransferPage(new_customer_page, base_url).open()
    transfer.transfer("-100")
    # transfer() already waited for the result heading, so check it now instead of retrying for 10s
    assert not transfer.success_heading.is_visible(), "negative transfer was accepted"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="ParaBank bug: no balance check, a transfer can overdraw an account")
def test_transfer_larger_than_balance_is_rejected(new_customer_page, base_url):
    AccountsPage(new_customer_page, base_url).open_new_account("SAVINGS")  # second account to transfer to
    transfer = TransferPage(new_customer_page, base_url).open(accounts=2)
    transfer.transfer("1000000", from_index=0, to_index=1)
    assert not transfer.success_heading.is_visible(), "transfer larger than the balance was accepted"


def test_empty_amount_shows_an_error(new_customer_page, base_url):
    transfer = TransferPage(new_customer_page, base_url).open()
    transfer.transfer("")
    expect(transfer.error_heading).to_be_visible()
    expect(transfer.success_heading).not_to_be_visible()


def test_decimal_amount_is_accepted(new_customer_page, base_url):
    """The exploring model wrongly expected this to be rejected; it is valid money."""
    transfer = TransferPage(new_customer_page, base_url).open()
    transfer.transfer("100.50")
    expect(transfer.success_heading).to_be_visible()
    expect(new_customer_page.get_by_text("$100.50 has been transferred")).to_be_visible()
