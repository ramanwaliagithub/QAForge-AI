"""The Day 18 scorecard must catch the things it claims to catch, on small known inputs."""
from scripts.spec_scorecard import REQUIRED_MEMBERS, REQUIRED_TESTS, parse_summary, rule_indicators, static_checks

INIT = 'from framework.pages.bill_pay_page import BillPayPage\n__all__ = ["BillPayPage"]\n'


def _page(extra_in_open: str = "", extra_method: str = "") -> str:
    members = "\n".join(f"    def {m}(self): ..." for m in sorted(REQUIRED_MEMBERS - {"path", "FIELDS", "open"}))
    return (f"class BillPayPage(BasePage):\n    path = '/billpay.htm'\n    FIELDS = {{}}\n"
            f"    def open(self):\n        {extra_in_open or 'pass'}\n{members}\n{extra_method}")


def _tests(names=REQUIRED_TESTS, body="expect(page).to_be_visible()", fixtures="new_customer_page") -> str:
    return "\n".join(f"def {n}({fixtures}):\n    {body}\n" for n in names)


def test_a_complete_implementation_passes_every_static_check():
    got = static_checks(_page(), _tests(), INIT)
    assert got["1_class_subclasses_basepage"] and got["1_missing_members"] == [] and got["1_exported_from_package"]
    assert got["2_assertions_in_page_object"] == 0 and got["6_banned_in_page_object"] == []
    assert got["4_names_match"] and got["4_test_functions"] == 5 and got["5_tests_without_expect"] == []
    assert got["6_banned_in_tests"] == [] and got["7_payment_test_uses_new_customer_page"]


def test_a_missing_file_is_reported_not_raised():
    got = static_checks(None, None, None)
    assert got == {"1_page_object_file": False, "4_tests_file": False}


def test_waiting_inside_open_is_allowed_but_an_assertion_elsewhere_is_not():
    assert static_checks(_page("expect(self.x).to_be_visible()"), _tests(), INIT)["2_assertions_in_page_object"] == 0
    bad = _page(extra_method="    def check(self):\n        assert self.page\n        expect(self.page).to_be_visible()")
    assert static_checks(bad, _tests(), INIT)["2_assertions_in_page_object"] == 2


def test_missing_members_and_missing_export_are_reported():
    page = "class BillPayPage(BasePage):\n    path = '/x'\n    def open(self): ...\n"
    got = static_checks(page, _tests(), "")
    assert "pay" in got["1_missing_members"] and "FIELDS" in got["1_missing_members"]
    assert got["1_exported_from_package"] is False


def test_banned_constructs_are_found_in_both_files():
    page = _page(extra_method="    def bad(self):\n        time.sleep(1)\n        return self.page.locator('x').first\n")
    tests = _tests(body="page.locator('//div').nth(1)\n    expect(page).to_be_visible()")
    got = static_checks(page, tests, INIT)
    assert len(got["6_banned_in_page_object"]) == 2
    assert len(got["6_banned_in_tests"]) >= 2 * 5 and any("xpath" in b for b in got["6_banned_in_tests"])


def test_tests_without_an_expect_and_wrong_names_are_reported():
    got = static_checks(_page(), _tests(names=[*REQUIRED_TESTS[:4], "test_other"], body="assert True"), INIT)
    assert got["4_names_match"] is False and got["4_missing_names"] == [REQUIRED_TESTS[4]]
    assert len(got["5_tests_without_expect"]) == 5
    assert got["7_payment_test_uses_new_customer_page"] is False  # the payment test is missing entirely


def test_payment_test_must_use_the_new_customer_fixture():
    got = static_checks(_page(), _tests(fixtures="logged_in_page"), INIT)
    assert got["7_payment_test_uses_new_customer_page"] is False


def test_parse_summary_reads_the_last_summary_line():
    assert parse_summary("....\n5 passed in 3.2s") == {"passed": 5, "failed": 0, "error": 0}
    assert parse_summary("x\n2 failed, 3 passed, 1 skipped in 9s") == {"passed": 3, "failed": 2, "error": 0}
    assert parse_summary("1 error in 0.5s") == {"passed": 0, "failed": 0, "error": 1}
    assert parse_summary("no summary") == {"passed": 0, "failed": 0, "error": 0}


def test_request_watching_is_found_directly_and_through_a_helper():
    src = (
        "def _sent(page):\n    page.on('request', lambda r: None)\n"
        "def test_a(page):\n    _sent(page)\n"
        "def test_b(page):\n    with page.expect_request('**/x'):\n        pass\n"
        "def test_c(page):\n    page.click('x')\n"
    )
    assert rule_indicators(src)["T4_tests_watching_requests"] == ["test_a", "test_b"]


def test_a_balance_written_into_a_test_is_reported_but_a_payment_amount_is_not():
    src = "A = '25.50'\nB = '$490.00'\nC = '515.50'\nD = '1,000.00'\nE = '5.50'\nF = 'abc'\n"
    assert rule_indicators(src)["T7_balance_like_literals"] == ["$490.00", "1,000.00", "515.50"]
