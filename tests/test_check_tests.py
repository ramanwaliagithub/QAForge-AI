"""The custom quality gate (scripts/check_tests.py): each rule catches what it names, lets good code through, and the repository is clean."""
import pytest

from scripts.check_tests import check_paths, check_source

HEAD = "from playwright.sync_api import expect\n\n\n"


def _rules(source, **kwargs):
    return [finding.rule for finding in check_source(source, **kwargs)]


@pytest.mark.parametrize(("body", "rule"), [
    ("import time\ndef test_x(page):\n    time.sleep(1)\n    expect(page).to_have_title('x')\n", "QF001"),
    ("from time import sleep\ndef test_x(page):\n    sleep(1)\n    assert page\n", "QF001"),
    ("def test_x(page):\n    page.wait_for_timeout(500)\n    assert page\n", "QF001"),
    ("def test_x():\n    assert True\n", "QF002"),
    ("def test_x():\n    assert 1\n", "QF002"),
    ("def test_x():\n    assert 'it works'\n", "QF002"),
    ("def test_x():\n    assert not False\n", "QF002"),
    ("def test_x(a):\n    assert a.total == a.total\n", "QF002"),
    ("def test_x(a):\n    assert a.ok or True\n", "QF002"),
    ("def test_x(page):\n    expect(page.get_by_text('Done'))\n", "QF003"),
    ("def test_x(page):\n    expect(page.get_by_text('Done')).to_be_visible\n", "QF003"),
    ("def test_x(page):\n    page.get_by_text('Done').click()\n", "QF004"),
    ("def test_x():\n    pass\n", "QF004"),
])
def test_each_rule_catches_what_it_names(body, rule):
    assert rule in _rules(HEAD + body)


@pytest.mark.parametrize("body", [
    "def test_x(page):\n    expect(page.get_by_text('Done')).to_be_visible()\n",
    "def test_x(a):\n    assert a.total == 5\n",
    "def test_x(get):\n    assert get('k') is get('k')\n",  # calling twice and comparing is a real idempotence check
    "def test_x():\n    with pytest.raises(ValueError):\n        int('x')\n",
    "def test_x(page):\n    assert_balance(page, '100')\n",
    "def test_x(page):\n    pytest.fail('not reachable')\n",
    "def helper(page):\n    page.click('x')\n",  # not a test function
])
def test_good_code_passes(body):
    assert _rules(HEAD + body) == []


def test_qf002_to_qf004_apply_to_test_files_only():
    source = "def helper():\n    expect('x')\n    assert True\n"
    assert _rules(source, is_test_file=False) == []
    assert _rules("import time\ndef helper():\n    time.sleep(1)\n", is_test_file=False) == ["QF001"]


def test_a_sleep_inside_a_string_is_not_a_sleep():
    assert _rules(HEAD + "def test_x():\n    code = 'time.sleep(1)'\n    assert 'sleep' in code\n") == []


def test_an_exception_needs_the_rule_id_and_a_reason():
    sleeping = "import time\ndef test_x():\n    time.sleep(1){}\n    assert 5 > 3\n"
    assert _rules(sleeping.format("  # qaforge: allow QF001 the app has no event to wait for")) == []
    assert _rules(sleeping.format("  # qaforge: allow QF001")) == ["QF001"]  # no reason
    assert _rules(sleeping.format("  # qaforge: allow QF002 wrong rule id")) == ["QF001"]
    assert _rules(sleeping.format("")) == ["QF001"]


def test_findings_say_where_and_what():
    finding = check_source("def test_x():\n    assert True\n", "tests/test_demo.py")[0]
    assert str(finding).startswith("tests/test_demo.py:2: QF002 ")


def test_the_repository_passes_its_own_gate():
    findings = check_paths(["framework", "tests", "ai_testgen/generated"])
    assert not findings, "\n".join(map(str, findings))


def test_the_gate_reads_the_generated_tests():
    """A gate that quietly scanned nothing would pass forever."""
    from scripts.check_tests import _files

    names = {path.name for path in _files(["ai_testgen/generated"])}
    assert any(name.startswith("test_bill_pay") for name in names) and len(names) >= 10
