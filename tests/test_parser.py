import json

import pytest

from ai_testgen.parser import ParseError, parse_testcases

GOOD = {
    "title": "Valid transfer",
    "type": "happy",
    "priority": "high",
    "preconditions": "Customer has two accounts",
    "steps": ["Open Transfer Funds", "Enter amount 50", "Click Transfer"],
    "expected": "Transfer Complete! is shown",
}


def wrap(*cases):
    return json.dumps({"test_cases": list(cases)})


def test_parses_valid_object():
    cases = parse_testcases(wrap(GOOD))
    assert len(cases) == 1 and cases[0].title == "Valid transfer"
    assert cases[0].steps[1] == "Enter amount 50"


def test_parses_bare_list():
    assert len(parse_testcases(json.dumps([GOOD, GOOD]))) == 2


def test_strips_code_fences():
    assert len(parse_testcases(f"```json\n{wrap(GOOD)}\n```")) == 1


def test_tolerates_chatter_around_json():
    assert len(parse_testcases(f"Here you go:\n{wrap(GOOD)}\nHope this helps!")) == 1


def test_normalises_case_of_enums():
    case = parse_testcases(wrap({**GOOD, "type": "Negative", "priority": "HIGH"}))[0]
    assert (case.type, case.priority) == ("negative", "high")


def test_defaults_applied():
    minimal = {"title": "Minimal", "steps": ["do it"], "expected": "done"}
    case = parse_testcases(wrap(minimal))[0]
    assert (case.type, case.priority, case.preconditions) == ("happy", "medium", "")


@pytest.mark.parametrize(
    "text, fragment",
    [
        ("not json at all", "No JSON"),
        ('{"test_cases": [', "Invalid JSON"),
        (json.dumps({"test_cases": []}), "test_cases"),
        (wrap({**GOOD, "steps": []}), "steps"),
        (wrap({**GOOD, "priority": "urgent"}), "priority"),
        (wrap({"title": "No expected", "steps": ["x"]}), "expected"),
        (json.dumps({"something": "else"}), "test_cases"),
    ],
)
def test_invalid_output_raises_with_useful_message(text, fragment):
    with pytest.raises(ParseError) as exc:
        parse_testcases(text)
    assert fragment in str(exc.value)
