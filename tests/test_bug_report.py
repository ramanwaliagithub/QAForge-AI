"""The bug report drafter with a scripted model (none is called): what the model is shown, and what is done with what it says."""
import json
from pathlib import Path

import pytest

from ai_testgen.bug_report import BugReport, DraftError, build_brief, draft_bug_report, read_test_source, ungrounded, visible_text
from framework.healing.collector import load_failure_context
from framework.llm_client import LLMResponse

SAMPLE = Path(__file__).resolve().parent.parent / "framework/healing/samples/framework_healing_sample_tests_test_broken_locators.py_test_sample_button_text_changed.json"
CTX = load_failure_context(SAMPLE)
SOURCE = "def test_x(page):\n    TransferPage(page).open().transfer('10')"

DRAFT = {"title": "Transfer button is not found by its name", "classification": "UI Change", "severity": "Minor",
         "summary": "The test waits for a button that has another name now.", "steps_to_reproduce": ["Open Transfer Funds", "Click the button"],
         "expected": "The test finds the button.", "actual": "Timeout waiting for the button.", "evidence": [],
         "suspected_cause": "", "next_action": "Update the locator."}


class Scripted:
    """Returns the given answers in order and remembers every prompt."""

    def __init__(self, *answers):
        self.answers, self.prompts = list(answers), []

    def generate(self, prompt, *, system=None, temperature=0.0, json_mode=False, num_ctx=None):
        self.prompts.append(prompt)
        answer = self.answers.pop(0)
        return LLMResponse(text=answer if isinstance(answer, str) else json.dumps(answer), model="scripted", latency_s=0.0)


def test_visible_text_keeps_what_a_user_reads_once_and_in_order():
    aria = '- heading "Transfer Funds" [level=1]\n- text: Amount\n- button "Transfer"\n- heading "Transfer Funds"\n- img'
    assert visible_text(aria) == "Transfer Funds | Amount | Transfer"


def test_visible_text_is_cut_at_the_limit():
    text = visible_text('- text: ' + 'x' * 100, limit=20)
    assert len(text) <= 24 and text.endswith("...")


def test_the_source_of_a_test_is_found_by_its_pytest_id_and_a_missing_one_is_said_to_be_missing():
    assert read_test_source("tests/test_data_models.py::test_a_valid_identity_is_accepted_and_untouched",
                            Path(__file__).resolve().parent.parent).startswith("def test_a_valid_identity")
    assert read_test_source("tests/nothing.py::test_x") == "(test source not available)"
    assert read_test_source("tests/test_bug_report.py::test_no_such_test", Path(__file__).resolve().parent.parent) == "(test source not available)"


def test_the_brief_holds_the_facts_and_not_the_screenshot():
    brief = build_brief(CTX, SOURCE)
    assert CTX.test_id in brief and "TimeoutError" in brief and SOURCE in brief and "Transfer Funds" in brief
    assert ".png" not in brief


def test_a_valid_draft_is_returned_with_its_labels_normalised():
    report, info = draft_bug_report(Scripted(DRAFT), CTX, SOURCE)
    assert isinstance(report, BugReport) and report.classification == "ui_change" and report.severity == "minor" and info["attempts"] == 1


def test_a_quote_that_is_not_in_the_failure_is_sent_back_naming_the_quote():
    brief = build_brief(CTX, SOURCE)
    invented = {**DRAFT, "evidence": ["Transfer Complete!", "TimeoutError"]}
    client = Scripted(invented, {**DRAFT, "evidence": ["TimeoutError"]})
    report, info = draft_bug_report(client, CTX, SOURCE)
    assert ungrounded(BugReport(**invented), brief) == ["Transfer Complete!"]
    assert "Transfer Complete!" in client.prompts[1] and info == {"attempts": 2, "dropped_quotes": []} and report.evidence == ["TimeoutError"]


def test_a_quote_still_invented_on_the_last_attempt_is_dropped_and_listed_not_kept():
    invented = {**DRAFT, "evidence": ["Transfer Complete!", "TimeoutError"]}
    report, info = draft_bug_report(Scripted(invented, invented), CTX, SOURCE, max_attempts=2)
    assert report.evidence == ["TimeoutError"] and info["dropped_quotes"] == ["Transfer Complete!"]


def test_quote_matching_ignores_case_and_spacing():
    brief = build_brief(CTX, SOURCE)
    assert ungrounded(BugReport(**{**DRAFT, "evidence": ["timeouterror"]}), brief) == []
    assert ungrounded(BugReport(**{**DRAFT, "evidence": ["TRANSFER   funds"]}), brief) == []


def test_bad_json_and_a_report_missing_fields_are_retried_with_the_problem_named():
    client = Scripted("Here is your bug report:", {"title": "x"}, DRAFT)
    report, info = draft_bug_report(client, CTX, SOURCE)
    assert info["attempts"] == 3 and report.title == DRAFT["title"]
    assert "rejected" in client.prompts[1] and "rejected" in client.prompts[2]


def test_a_model_that_never_produces_a_valid_report_ends_in_a_clear_error():
    with pytest.raises(DraftError, match="no valid bug report after 2 attempts"):
        draft_bug_report(Scripted("no", "still no"), CTX, SOURCE, max_attempts=2)


def test_an_unknown_classification_is_refused():
    with pytest.raises(ValueError, match="classification"):
        BugReport(**{**DRAFT, "classification": "my_fault"})
