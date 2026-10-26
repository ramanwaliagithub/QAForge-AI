import json
from pathlib import Path

import pytest

from framework.healing.collector import load_failure_context
from framework.healing.suggester import (
    build_prompt, format_elements, open_snapshot, should_attempt, suggest_locator,
)
from framework.llm_client import LLMResponse

SAMPLES = Path("framework/healing/samples")


def load(name):
    return load_failure_context(next(SAMPLES.glob(f"*test_sample_{name}.json")))


class Scripted:
    def __init__(self, *replies):
        self.replies, self.prompts = [json.dumps(r) if isinstance(r, dict) else r for r in replies], []

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        return LLMResponse(self.replies.pop(0), "fake", 0.0)


@pytest.fixture
def snapshot(browser):
    opened = []

    def _open(ctx):
        context, page = open_snapshot(browser, ctx)
        opened.append(context)
        return page

    yield _open
    for c in opened:
        c.close()


CSS_AMOUNT = {"strategy": "css", "css": "#amount", "reason": "id", "confidence": 0.9}


def test_guard_allows_only_locator_failures_by_default():
    assert should_attempt(load("id_renamed")) and should_attempt(load("locator_too_generic"))
    assert not should_attempt(load("wrong_text_on_found_element"))
    assert not should_attempt(load("expect_on_missing_element"))
    assert should_attempt(load("expect_on_missing_element"), allow_maybe=True)
    assert not should_attempt(load("wrong_text_on_found_element"), allow_maybe=True)


def test_prompt_contains_what_the_model_needs_and_no_placeholders_left():
    p = build_prompt(load("id_renamed"))
    assert 'locator("#amt")' in p and "fill" in p and "self.fill(self.amount, amount)" in p
    assert "ParaBank | Transfer Funds" in p and "textbox, NO accessible name; css=#amount" in p
    for placeholder in ("{locator}", "{action}", "{frames}", "{title}", "{url}", "{elements}"):
        assert placeholder not in p


def test_format_elements_describes_role_and_accessible_name():
    out = format_elements([
        {"tag": "input", "type": "text", "id": "amount", "visible": True},
        {"tag": "input", "id": "hidden_one", "visible": False},
        {"tag": "div", "visible": True},
        {"tag": "input", "type": "submit", "value": "Transfer", "visible": True},
        {"tag": "a", "text": "Log Out", "visible": True},
        {"tag": "a", "text": "Log Out", "visible": True},  # duplicate footer link
        {"tag": "select", "type": "select-one", "id": "fromAccountId", "text": "393852", "visible": True},
        {"tag": "input", "type": "text", "placeholder": "Search", "id": "q", "visible": True},
        {"tag": "h1", "text": "Transfer Funds", "visible": True},
    ])
    assert out.splitlines() == [
        "- textbox, NO accessible name; css=#amount",
        "- button name='Transfer'",
        "- link name='Log Out'",
        "- combobox, NO accessible name; css=#fromAccountId",   # the option text '393852' must not become its name
        "- textbox name='Search'",
        "- heading name='Transfer Funds'",
    ]


def test_css_hint_is_valid_css_for_dotted_ids_and_skips_generated_ids():
    from framework.healing.suggester import css_hint
    assert css_hint({"tag": "input", "id": "amount"}) == "#amount"
    assert css_hint({"tag": "input", "id": "customer.firstName", "name": "customer.firstName"}) == "[id='customer.firstName']"
    assert css_hint({"tag": "input", "id": "bf81510c-99d7-4022-b4c2-bb67be72ae6d", "name": "payee.phoneNumber"}) == "input[name='payee.phoneNumber']"
    assert css_hint({"tag": "input", "name": "username"}) == "input[name='username']"
    assert css_hint({"tag": "input"}) is None


def test_retry_feedback_lists_everything_already_rejected(snapshot):
    ctx = load("id_renamed")
    client = Scripted({"strategy": "css", "css": "#nope1"}, {"strategy": "css", "css": "#nope2"}, CSS_AMOUNT)
    r = suggest_locator(client, ctx, snapshot(ctx))
    assert r.healed and len(r.attempts) == 3
    assert 'Already rejected, do not repeat: locator("#nope1")' in client.prompts[1]
    assert 'locator("#nope1"); locator("#nope2")' in client.prompts[2]


def test_implicit_roles():
    from framework.healing.suggester import implicit_role
    assert implicit_role({"tag": "input", "type": "submit"}) == "button"
    assert implicit_role({"tag": "input", "type": "text"}) == "textbox" and implicit_role({"tag": "input"}) == "textbox"
    assert implicit_role({"tag": "input", "type": "checkbox"}) == "checkbox"
    assert implicit_role({"tag": "select"}) == "combobox" and implicit_role({"tag": "a"}) == "link"
    assert implicit_role({"tag": "div", "role": "alert"}) == "alert" and implicit_role({"tag": "div"}) is None


def test_candidates_are_narrowed_to_what_the_action_can_work_on():
    els = [
        {"tag": "a", "text": "Transfer Funds", "visible": True},
        {"tag": "input", "type": "text", "id": "amount", "visible": True},
        {"tag": "select", "type": "select-one", "id": "fromAccountId", "visible": True},
        {"tag": "input", "type": "submit", "value": "Transfer", "visible": True},
    ]
    assert format_elements(els, action="fill").splitlines() == ["- textbox, NO accessible name; css=#amount"]
    assert format_elements(els, action="select_option").splitlines() == ["- combobox, NO accessible name; css=#fromAccountId"]
    assert format_elements(els, action="click").splitlines() == ["- link name='Transfer Funds'", "- button name='Transfer'"]
    assert len(format_elements(els, action=None).splitlines()) == 4


def test_prompt_for_a_fill_lists_only_inputs():
    p = build_prompt(load("id_renamed"))
    listed = p.split("## Candidate elements on the page")[1].split("## Rules")[0]
    assert "css=#amount" in listed and "About Us" not in listed and "fromAccountId" not in listed


def test_heals_on_first_valid_suggestion(snapshot):
    ctx = load("id_renamed")
    client = Scripted(CSS_AMOUNT)
    r = suggest_locator(client, ctx, snapshot(ctx))
    assert r.healed and len(r.attempts) == 1 and r.source == 'locator("#amount")' and r.element["id"] == "amount"


def test_rejection_reason_is_fed_back_and_second_attempt_heals(snapshot):
    ctx = load("id_renamed")
    client = Scripted({"strategy": "css", "css": "#amnt"}, CSS_AMOUNT)
    r = suggest_locator(client, ctx, snapshot(ctx))
    assert r.healed and len(r.attempts) == 2
    assert "no element" in r.attempts[0].rejected_because
    assert 'rejected: Matches no element' in client.prompts[1] and 'locator("#amnt")' in client.prompts[1]
    assert "rejected" not in client.prompts[0]


def test_matching_many_elements_is_rejected(snapshot):
    ctx = load("locator_too_generic")
    client = Scripted({"strategy": "css", "css": "select"}, {"strategy": "css", "css": "#fromAccountId"})
    r = suggest_locator(client, ctx, snapshot(ctx))
    assert r.healed and r.attempts[0].validation.count == 2 and r.element["id"] == "fromAccountId"


def test_unusable_model_output_counts_as_an_attempt(snapshot):
    ctx = load("id_renamed")
    r = suggest_locator(Scripted("I think you should use the amount field", CSS_AMOUNT), ctx, snapshot(ctx))
    assert r.healed and r.attempts[0].error and "No JSON" in r.attempts[0].error


def test_gives_up_after_max_attempts_without_healing(snapshot):
    ctx = load("id_renamed")
    bad = {"strategy": "css", "css": "#nope"}
    r = suggest_locator(Scripted(bad, bad, bad), ctx, snapshot(ctx), max_attempts=3)
    assert not r.healed and len(r.attempts) == 3 and r.suggestion is None and r.source is None


def test_unique_but_wrong_element_for_the_action_is_not_healed(snapshot):
    ctx = load("id_renamed")  # fills text: the Transfer button is unique but wrong
    wrong = {"strategy": "role", "role": "button", "name": "Transfer"}
    r = suggest_locator(Scripted(wrong, CSS_AMOUNT), ctx, snapshot(ctx))
    assert r.healed and "fills text" in r.attempts[0].rejected_because and len(r.attempts) == 2
