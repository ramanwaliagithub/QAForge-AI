from ai_testgen.grounding import (
    build_context, estimate_tokens, format_elements, load_snapshots, selector_for, trim_to_tokens,
)

ELEMENTS = [
    {"tag": "input", "type": "text", "id": "amount", "name": "input", "label": "Amount"},
    {"tag": "input", "type": "text", "id": "bf81510c-99d7-4022-b4c2-bb67be72ae6d", "name": "payee.phoneNumber", "label": "Phone #:"},
    {"tag": "select", "type": "select-one", "id": None, "name": "fromAccountId", "options": ["1", "2"]},
    {"tag": "input", "type": "submit", "value": "Transfer"},
    {"tag": "a", "text": "Log out"},
    {"tag": "div"},
]


def test_selector_prefers_stable_id_then_name_then_value():
    assert selector_for(ELEMENTS[0]) == "#amount"
    assert selector_for(ELEMENTS[1]) == "input[name='payee.phoneNumber']"  # uuid id is skipped
    assert selector_for(ELEMENTS[2]) == "select[name='fromAccountId']"
    assert selector_for(ELEMENTS[3]) == "input[value='Transfer']"
    assert selector_for(ELEMENTS[4]) == "a:has-text('Log out')"
    assert selector_for(ELEMENTS[5]) is None


def test_selector_uses_attribute_form_for_ids_with_dots():
    assert selector_for({"tag": "input", "id": "customer.firstName"}) == "[id='customer.firstName']"


def test_format_elements_includes_selector_label_options_and_skips_unselectable():
    out = format_elements(ELEMENTS)
    assert "selector: #amount" in out and "label: 'Phone #:'" in out and "never hardcode" in out
    assert len(out.splitlines()) == 5


def test_non_numeric_options_are_kept():
    el = {"tag": "select", "type": "select-one", "id": "type", "options": ["CHECKING", "SAVINGS"]}
    assert "options: ['CHECKING', 'SAVINGS']" in format_elements([el])


def test_trim_removes_bare_structure_lines():
    text = "- heading \"X\"\n- row:\n- cell\n  - cell \"A\":\n- textbox"
    assert trim_to_tokens(text) == '- heading "X"\n- textbox'


def test_trim_respects_budget_and_marks_truncation():
    text = "\n".join(f"- line number {i} with some padding text" for i in range(500))
    out = trim_to_tokens(text, max_tokens=100)
    assert estimate_tokens(out) <= 110
    assert out.endswith("... (truncated)")


def test_trim_leaves_small_input_untouched():
    assert trim_to_tokens("- a\n- b", 100) == "- a\n- b"


def test_build_context_modes():
    snap = {"path": "x.htm", "aria": '- heading "H"', "elements": ELEMENTS}
    assert build_context([snap], "none") == ""
    assert "Accessibility snapshot" in build_context([snap], "aria") and "selector:" not in build_context([snap], "aria")
    assert "selector: #amount" in build_context([snap], "elements")
    both = build_context([snap], "both")
    assert "Accessibility snapshot" in both and "selector: #amount" in both


def test_load_snapshots_unknown_story_is_empty():
    assert load_snapshots("nonexistent") == []
