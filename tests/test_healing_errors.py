"""Classification tests use the real error texts Playwright produced (captured on 2026-10-23)."""
import pytest

from framework.healing.errors import KIND_HINT, analyze_exception, classify_message, clean_message

TIMEOUT = "playwright._impl._errors.TimeoutError"
PWERR = "playwright._impl._errors.Error"
ASSERT = "builtins.AssertionError"

ID_MISSING = 'Locator.fill: Timeout 2000ms exceeded.\nCall log:\n  - waiting for locator("#amt")\n'
ROLE_CHANGED = 'Locator.click: Timeout 2000ms exceeded.\nCall log:\n  - waiting for get_by_role("button", name="Transfer Money")\n'
EXPECT_MISSING = (
    'Locator expected to be visible\nActual value: None\nError: element(s) not found \nCall log:\n'
    '  - Expect "to_be_visible" get_by_role("heading", name="Transfer Completed!") with timeout 1500ms\n'
    '  - waiting for get_by_role("heading", name="Transfer Completed!")\n\nAria snapshot:\n- link:\n  - /url: admin.htm'
)
EXPECT_WRONG = (
    "Locator expected to have text 'Wire Funds'\nActual value: \n\t\t\tTransfer Funds\n\t\t \nCall log:\n"
    '  - Expect "to_have_text" get_by_role("heading", name="Transfer Funds") with timeout 1500ms\n'
    '  - waiting for get_by_role("heading", name="Transfer Funds")\n'
    '    16 × locator resolved to <h1 class="title">Transfer Funds</h1>\n'
)
STRICT = (
    'Locator.click: Error: strict mode violation: locator("option") resolved to 2 elements:\n'
    '    1) <option value="1">1</option> aka locator("#fromAccountId")\n\nCall log:\n  - waiting for locator("option")\n'
)
NOT_ACTIONABLE = (
    'Locator.fill: Error: Element is not an <input>, <textarea> or [contenteditable] element\nCall log:\n'
    '  - waiting for locator("#fromAccountId")\n    - locator resolved to <select class="input" id="fromAccountId">…</select>\n'
    '    - fill("x")\n'
)


@pytest.mark.parametrize("exc_type, message, kind, locator, action", [
    (TIMEOUT, ID_MISSING, "locator_not_found", 'locator("#amt")', "fill"),
    (TIMEOUT, ROLE_CHANGED, "locator_not_found", 'get_by_role("button", name="Transfer Money")', "click"),
    (ASSERT, clean_message(EXPECT_MISSING), "assertion_element_missing",
     'get_by_role("heading", name="Transfer Completed!")', "to_be_visible"),
    (ASSERT, EXPECT_WRONG, "assertion", 'get_by_role("heading", name="Transfer Funds")', "to_have_text"),
    (PWERR, STRICT, "strict_mode_violation", 'locator("option")', "click"),
    (PWERR, NOT_ACTIONABLE, "not_actionable", 'locator("#fromAccountId")', "fill"),
    (ASSERT, "assert 1 == 2", "assertion", None, None),
    (TIMEOUT, "Page.wait_for_url: Timeout 5000ms exceeded.", "timeout_other", None, "wait_for_url"),
    (f"builtins.RuntimeError", "boom", "other", None, None),
])
def test_classify_message(exc_type, message, kind, locator, action):
    got_kind, got_locator, got_action, _ = classify_message(exc_type, message)
    assert (got_kind, got_locator, got_action) == (kind, locator, action)


def test_timeout_is_extracted():
    assert classify_message(TIMEOUT, ID_MISSING)[3] == 2000
    assert classify_message(ASSERT, "assert 1 == 2")[3] is None


def test_clean_message_drops_aria_snapshot_ansi_and_truncates():
    cleaned = clean_message("\x1b[31mred\x1b[0m failure\nAria snapshot:\n- link: x")
    assert cleaned == "red failure"
    assert len(clean_message("x" * 5000)) == 1500


def test_heal_hint_only_allows_locator_problems():
    assert KIND_HINT["locator_not_found"] == "locator" and KIND_HINT["strict_mode_violation"] == "locator"
    assert KIND_HINT["assertion"] == "no"  # a changed value on a found element may be a real bug: never heal
    assert KIND_HINT["assertion_element_missing"] == "maybe"


def test_analyze_exception_collects_project_frames():
    def helper():
        raise AssertionError("assert 1 == 2")

    try:
        helper()
    except AssertionError as e:
        info = analyze_exception(e)
    assert info.kind == "assertion" and info.heal_hint == "no"
    assert info.frames[-1]["function"] == "helper"
    assert info.frames[-1]["file"] == "tests/test_healing_errors.py"
    assert info.frames[-1]["code"] == 'raise AssertionError("assert 1 == 2")'
