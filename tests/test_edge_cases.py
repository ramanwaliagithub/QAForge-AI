import json

import pytest

from ai_testgen.edge_cases import (
    EdgeCaseError, classify_outcome, expects_rejection, parse_edge_cases, propose_edge_cases,
)
from framework.llm_client import LLMResponse

CASE = {"title": "Negative amount", "amount": "-5", "from_index": 0, "to_index": 1, "expected": "The transfer is rejected"}


def test_parse_edge_cases_object_list_and_chatter():
    assert parse_edge_cases(json.dumps({"edge_cases": [CASE]})).cases[0].amount == "-5"
    assert len(parse_edge_cases("Sure! " + json.dumps({"edge_cases": [CASE, CASE]})).cases) == 2


def test_infeasible_cases_are_collected_not_fatal():
    p = parse_edge_cases(json.dumps({"edge_cases": [CASE, {**CASE, "title": "Unknown account", "to_index": 2}]}))
    assert len(p.cases) == 1 and len(p.rejected) == 1
    assert "to_index" in p.rejected[0]["why"] and p.rejected[0]["item"]["title"] == "Unknown account"


@pytest.mark.parametrize("text", ["no json", '{"edge_cases": []}', '{"edge_cases": [{"title": "x"}]}',
                                  json.dumps({"edge_cases": [{**CASE, "from_index": 5}]})])
def test_parse_edge_cases_rejects_bad_output(text):
    with pytest.raises(EdgeCaseError):
        parse_edge_cases(text)


class Scripted:
    def __init__(self, *outs):
        self.outs, self.prompts = list(outs), []

    def generate(self, prompt, **kw):
        self.prompts.append(prompt)
        return LLMResponse(self.outs.pop(0), "fake", 0.0)


def test_propose_retries_with_feedback_and_truncates_to_n():
    client = Scripted("garbage", json.dumps({"edge_cases": [CASE] * 7}))
    result = propose_edge_cases(client, "SNAP", n=5)
    assert len(result.cases) == 5 and "rejected" in client.prompts[1] and "SNAP" in client.prompts[0]


def test_propose_reports_rejected_items():
    reply = json.dumps({"edge_cases": [CASE, {**CASE, "from_index": 3}]})
    result = propose_edge_cases(Scripted(reply), "SNAP", n=5)
    assert len(result.cases) == 1 and len(result.rejected) == 1


@pytest.mark.parametrize("expected, rejects", [
    ("The transfer is rejected with an error message", True),
    ("The transfer should not be allowed", True),
    ("The app should show a validation error", True),
    ("The transfer is accepted and balances update", False),
    ("The transfer should be successful", False),
])
def test_expects_rejection(expected, rejects):
    assert expects_rejection(expected) is rejects


def test_classify_outcome():
    assert classify_outcome(["Transfer Complete!", "$5 has been transferred"]) == "accepted"
    assert classify_outcome(["Error!", "An internal error has occurred"]) == "rejected"
    assert classify_outcome(["Amount: $"]) == "other"
