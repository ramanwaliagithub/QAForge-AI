"""The scoring is only fair if every sample actually contains the element a person would pick, exactly once."""
from pathlib import Path

import pytest

from framework.healing.collector import load_failure_context
from framework.healing.ground_truth import HELDOUT, HELDOUT2, TUNED, matches
from framework.healing.suggester import open_snapshot
from framework.healing.suggestion import LocatorSuggestion, validate_suggestion

SETS = {"samples": TUNED, "samples_heldout": HELDOUT, "samples_heldout2": HELDOUT2}
CASES = [(d, name) for d, truths in SETS.items() for name in truths]


def _ctx(dir_name, name):
    return load_failure_context(next(Path("framework/healing", dir_name).glob(f"*_{name}.json")))


def _truth_as_css(truth):
    if "id" in truth:
        return f"#{truth['id']}"
    if "name" in truth:
        return f"[name='{truth['name']}']"
    return None


@pytest.mark.parametrize("dir_name, name", CASES)
def test_the_correct_answer_exists_in_the_captured_page(dir_name, name):
    truth = SETS[dir_name][name]
    elements = _ctx(dir_name, name).page.elements
    assert any(
        all(({"text": e.get("text")} | e).get(k) == v for k, v in truth.items()) for e in elements
    ), f"{name}: no captured element matches {truth}"


@pytest.mark.parametrize("dir_name, name", [c for c in CASES if _truth_as_css(SETS[c[0]][c[1]])])
def test_the_correct_answer_resolves_to_exactly_one_element(browser, dir_name, name):
    ctx = _ctx(dir_name, name)
    context, page = open_snapshot(browser, ctx)
    try:
        v = validate_suggestion(page, LocatorSuggestion(strategy="css", css=_truth_as_css(SETS[dir_name][name])))
        assert v.ok and matches(v.element, SETS[dir_name][name]), v
    finally:
        context.close()


def test_matches():
    assert matches({"id": "a", "tag": "input"}, {"id": "a"}) and not matches({"id": "b"}, {"id": "a"})
