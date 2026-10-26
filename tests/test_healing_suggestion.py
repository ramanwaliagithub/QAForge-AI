import json
from pathlib import Path

import pytest

from framework.healing.collector import load_failure_context
from framework.healing.suggestion import (
    LocatorSuggestion, SuggestionParseError, build_locator, intended_action, parse_suggestion, render_locator,
    validate_suggestion,
)

SAMPLES = Path("framework/healing/samples")


def load(name):
    return load_failure_context(next(SAMPLES.glob(f"*test_sample_{name}.json")))


@pytest.fixture
def snapshot_page(browser):
    """Loads a captured DOM as a static page: JS off and offline, so what we count is exactly what was captured."""
    contexts = []

    def open_snapshot(ctx):
        c = browser.new_context(java_script_enabled=False, offline=True)
        contexts.append(c)
        p = c.new_page()
        p.set_content(ctx.page.html)
        return p

    yield open_snapshot
    for c in contexts:
        c.close()


def S(**kw):
    return LocatorSuggestion(**kw)


# ---- schema and rendering ----

@pytest.mark.parametrize("kw, source", [
    (dict(strategy="role", role="button", name="Transfer", exact=True), 'get_by_role("button", name="Transfer", exact=True)'),
    (dict(strategy="role", role="textbox"), 'get_by_role("textbox")'),
    (dict(strategy="label", text="Amount"), 'get_by_label("Amount")'),
    (dict(strategy="text", text="Transfer Funds", exact=True), 'get_by_text("Transfer Funds", exact=True)'),
    (dict(strategy="placeholder", text="Search"), 'get_by_placeholder("Search")'),
    (dict(strategy="css", css="#amount"), 'locator("#amount")'),
])
def test_render_locator(kw, source):
    assert render_locator(S(**kw)) == source
    assert render_locator(S(**kw), prefix="self.page.") == "self.page." + source


@pytest.mark.parametrize("kw", [
    dict(strategy="role"), dict(strategy="label"), dict(strategy="css"),
    dict(strategy="css", css="//div"), dict(strategy="css", css="xpath=//a"), dict(strategy="css", css="nth=0"),
    dict(strategy="role", role="button", confidence=2),
])
def test_invalid_suggestions_are_rejected(kw):
    with pytest.raises(ValueError):
        S(**kw)


def test_parse_suggestion_tolerates_chatter_and_explains_failures():
    ok = parse_suggestion('Sure: {"strategy": "css", "css": "#amount", "reason": "id", "confidence": 0.9}')
    assert ok.css == "#amount" and ok.confidence == 0.9
    for bad, fragment in [("no json", "No JSON"), ("{bad", "No JSON"), ('{"strategy": "role"}', "needs a role"),
                          ('{"strategy": "magic"}', "strategy")]:
        with pytest.raises(SuggestionParseError, match=fragment):
            parse_suggestion(bad)


def test_model_output_is_never_executed():
    """A hostile 'locator' is just data: it is quoted into source and passed to Playwright, never eval'd."""
    s = S(strategy="text", text='"); import os; os.system("x"); ("')
    assert render_locator(s) == 'get_by_text("\\"); import os; os.system(\\"x\\"); (\\"")'


# ---- intent ----

def test_intended_action_reads_the_failing_source_lines():
    assert intended_action(load("id_renamed").error) == "fill"
    assert intended_action(load("button_text_changed").error) == "click"
    assert intended_action(load("locator_too_generic").error) == "select_option"


# ---- validation against the captured DOM ----

def test_good_suggestion_for_renamed_id_matches_exactly_one(snapshot_page):
    ctx = load("id_renamed")
    v = validate_suggestion(snapshot_page(ctx), S(strategy="css", css="#amount"), ctx.error.locator, "fill")
    assert v.ok and v.count == 1 and v.element["id"] == "amount"


def test_role_suggestion_for_changed_button_text(snapshot_page):
    ctx = load("button_text_changed")
    v = validate_suggestion(snapshot_page(ctx), S(strategy="role", role="button", name="Transfer", exact=True),
                            ctx.error.locator, "click")
    assert v.ok and v.element["value"] == "Transfer" and v.element["type"] == "submit"


def test_zero_matches_rejected(snapshot_page):
    ctx = load("id_renamed")
    v = validate_suggestion(snapshot_page(ctx), S(strategy="css", css="#amnt"), ctx.error.locator, "fill")
    assert not v.ok and v.count == 0 and "no element" in v.reason


def test_many_matches_rejected(snapshot_page):
    ctx = load("locator_too_generic")
    v = validate_suggestion(snapshot_page(ctx), S(strategy="css", css="select"), ctx.error.locator, "select_option")
    assert not v.ok and v.count == 2 and "exactly one" in v.reason


def test_same_locator_as_the_failed_one_rejected(snapshot_page):
    ctx = load("id_renamed")
    v = validate_suggestion(snapshot_page(ctx), S(strategy="css", css="#amt"), ctx.error.locator, "fill")
    assert not v.ok and "Same locator" in v.reason


def test_fragile_css_rejected_even_if_it_matches_one(snapshot_page):
    ctx = load("id_renamed")
    v = validate_suggestion(snapshot_page(ctx), S(strategy="css", css="a[href*='admin']"), None, None)
    assert not v.ok and "fragile" in v.reason


def test_unique_but_wrong_kind_of_element_rejected(snapshot_page):
    ctx = load("id_renamed")  # the test fills text; the Transfer button is unique but cannot take text
    v = validate_suggestion(snapshot_page(ctx), S(strategy="role", role="button", name="Transfer"), ctx.error.locator, "fill")
    assert not v.ok and v.count == 1 and "fills text" in v.reason


def test_unknown_role_from_the_model_is_a_rejection_not_a_crash(snapshot_page):
    ctx = load("id_renamed")  # Playwright does not raise for an unknown role, it just matches nothing
    v = validate_suggestion(snapshot_page(ctx), S(strategy="role", role="not-a-role"), None, None)
    assert not v.ok and v.count == 0


def test_a_selector_that_playwright_cannot_parse_is_a_rejection_not_a_crash(snapshot_page):
    ctx = load("id_renamed")
    v = validate_suggestion(snapshot_page(ctx), S(strategy="css", css="input[[["), None, None)
    assert not v.ok and "invalid" in v.reason.lower()
