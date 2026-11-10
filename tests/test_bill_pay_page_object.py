"""BillPayPage guards that need no browser."""
import pytest

from framework.pages import BillPayPage


def test_an_unknown_error_id_is_refused_instead_of_matching_nothing():
    """A mistyped id would give a locator that matches nothing, and `not_to_be_visible()` passes on that."""
    page = BillPayPage(None, "http://localhost:8080/parabank")
    with pytest.raises(ValueError, match="unknown bill pay error id"):
        page.field_error("verifyAccount-mismach")
