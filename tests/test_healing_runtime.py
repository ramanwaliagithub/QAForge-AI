import json

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from framework.healing import runtime
from framework.healing.runtime import HealConfig, Healer
from framework.llm_client import LLMResponse
from framework.pages.base_page import BasePage

HTML = """<html><body>
<input id="amount" type="text">
<select id="acct"><option value="1">1</option><option value="2">2</option></select>
<input type="submit" value="Transfer" onclick="document.title='submitted'">
<input id="locked" type="text" disabled>
</body></html>"""


class Scripted:
    def __init__(self, *replies):
        self.replies = [json.dumps(r) if isinstance(r, dict) else r for r in replies]
        self.prompts = []

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        if not self.replies:
            raise RuntimeError("model is down")
        return LLMResponse(self.replies.pop(0), "fake", 0.0)


AMOUNT = {"strategy": "css", "css": "#amount", "reason": "the amount input", "confidence": 0.9}
BUTTON = {"strategy": "role", "role": "button", "name": "Transfer", "exact": True, "reason": "submit", "confidence": 0.8}
ACCT = {"strategy": "css", "css": "#acct", "reason": "dropdown", "confidence": 0.7}


@pytest.fixture
def po(page):
    page.set_content(HTML)
    page.set_default_timeout(600)
    return BasePage(page, "http://example.test")


def healer_with(client, **config):
    return Healer(lambda: client, HealConfig(**config))


def test_without_a_healer_failures_propagate_exactly_as_before(po):
    assert runtime.current() is None
    with pytest.raises(PlaywrightTimeoutError, match="#amt"):
        po.fill(po.page.locator("#amt"), "10")


def test_broken_fill_is_healed_and_retried_once(po):
    client = Scripted(AMOUNT)
    healer = healer_with(client)
    with runtime.use(healer):
        po.fill(po.page.locator("#amt"), "10")
    assert po.page.locator("#amount").input_value() == "10"
    (e,) = healer.events
    assert (e.outcome, e.verified, e.kind, e.heal_hint, e.action) == ("healed", True, "locator_not_found", "locator", "fill")
    assert e.failed_locator == 'locator("#amt")' and e.suggestion == 'locator("#amount")'
    assert e.confidence == 0.9 and e.status == "proposed" and e.attempts == 1 and e.element["id"] == "amount"
    assert e.caller_frames[-1]["function"] == "test_broken_fill_is_healed_and_retried_once"


def test_broken_button_and_dropdown_are_healed_too(po):
    healer = healer_with(Scripted(BUTTON, ACCT))
    with runtime.use(healer):
        po.click(po.page.get_by_role("button", name="Transfer Money", exact=True))
        po.select_option(po.page.locator("#account"), "2")
    assert po.page.title() == "submitted" and po.page.locator("#acct").input_value() == "2"
    assert [e.outcome for e in healer.events] == ["healed", "healed"]


def test_runtime_scope_is_restored_after_the_block():
    h = healer_with(Scripted())
    with runtime.use(h):
        assert runtime.current() is h
        with runtime.use(None):
            assert runtime.current() is None
        assert runtime.current() is h
    assert runtime.current() is None


def test_a_failed_retry_reraises_the_original_error_and_is_recorded(po):
    # #locked exists, is unique and is a text input, so validation passes; but it is disabled so the retry fails
    healer = healer_with(Scripted({"strategy": "css", "css": "#locked"}))
    with runtime.use(healer), pytest.raises(PlaywrightTimeoutError, match="#amt"):  # the ORIGINAL locator's error
        po.fill(po.page.locator("#amt"), "10")
    (e,) = healer.events
    assert e.outcome == "retry_failed" and e.verified is False and e.suggestion == 'locator("#locked")'


def test_nothing_acceptable_from_the_model_means_the_original_failure(po):
    bad = {"strategy": "css", "css": "#nope"}
    healer = healer_with(Scripted(bad, bad, bad))
    with runtime.use(healer), pytest.raises(PlaywrightTimeoutError, match="#amt"):
        po.fill(po.page.locator("#amt"), "10")
    (e,) = healer.events
    assert e.outcome == "no_suggestion" and e.attempts == 3 and len(e.rejections) == 3 and e.suggestion is None


def test_a_model_outage_never_changes_the_failure(po):
    healer = healer_with(Scripted())  # raises RuntimeError("model is down") on the first call
    with runtime.use(healer), pytest.raises(PlaywrightTimeoutError, match="#amt"):
        po.fill(po.page.locator("#amt"), "10")
    assert healer.events[0].outcome == "error" and "model is down" in healer.events[0].error_message


def test_guard_skips_failures_that_are_not_locator_problems(po):
    # the element exists but cannot take text: not_actionable (cause is ambiguous) -> not attempted by default
    client = Scripted(AMOUNT)
    healer = healer_with(client)
    with runtime.use(healer), pytest.raises(PlaywrightError, match="not an <input>"):
        po.fill(po.page.locator("#acct"), "x")
    (e,) = healer.events
    assert (e.kind, e.heal_hint, e.outcome) == ("not_actionable", "maybe", "skipped_guard")
    assert client.prompts == [], "the model must not even be asked"


def test_allow_maybe_opts_in_to_ambiguous_failures(po):
    healer = healer_with(Scripted(AMOUNT), allow_maybe=True)
    with runtime.use(healer):
        po.fill(po.page.locator("#acct"), "7")
    assert healer.events[0].outcome == "healed" and po.page.locator("#amount").input_value() == "7"


def test_assertions_in_a_test_are_never_healed(po):
    healer = healer_with(Scripted(AMOUNT))
    with runtime.use(healer), pytest.raises(AssertionError):
        expect(po.page.locator("#amt")).to_be_visible(timeout=300)  # a test assertion: no page-object action involved
    assert healer.events == []


def test_the_models_answer_is_cached_per_page_locator_and_action(po):
    client = Scripted(AMOUNT)  # only ONE answer: a second model call would raise "model is down"
    healer = healer_with(client)
    with runtime.use(healer):
        po.fill(po.page.locator("#amt"), "1")
        po.fill(po.page.locator("#amt"), "2")
    assert po.page.locator("#amount").input_value() == "2" and len(client.prompts) == 1
    assert [(e.outcome, e.from_cache) for e in healer.events] == [("healed", False), ("healed", True)]


def test_heals_per_test_are_bounded(po):
    healer = healer_with(Scripted(AMOUNT, ACCT), max_heals_per_test=1)
    healer.begin_test("t::budget")
    with runtime.use(healer):
        po.fill(po.page.locator("#amt"), "1")
        with pytest.raises(PlaywrightError):
            po.select_option(po.page.locator("#account"), "2")
    assert [e.outcome for e in healer.events] == ["healed", "budget_exhausted"]
    healer.begin_test("t::next")  # a new test gets a fresh budget
    with runtime.use(healer):
        po.select_option(po.page.locator("#account"), "2")
    assert healer.events[-1].outcome == "healed"


def test_the_client_is_only_created_when_a_heal_is_needed(po):
    created = []
    healer = Healer(lambda: created.append(1) or Scripted(AMOUNT))
    with runtime.use(healer):
        po.fill(po.page.locator("#amount"), "ok")  # a locator that works: no model needed
    assert created == [] and healer.events == []
    with runtime.use(healer):
        po.fill(po.page.locator("#amt"), "x")
    assert created == [1]
