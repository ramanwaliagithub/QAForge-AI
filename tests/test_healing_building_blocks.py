import json

import pytest

from framework.healing.definitions import find_definitions
from framework.healing.errors import stack_frames
from framework.llm_client import ReplayClient, get_client


def test_replay_client_returns_answers_in_order_then_fails_loudly(tmp_path):
    f = tmp_path / "r.json"
    f.write_text(json.dumps(["one", {"strategy": "css", "css": "#a"}]))
    c = ReplayClient(str(f))
    assert c.generate("p").text == "one"
    assert json.loads(c.generate("p").text)["css"] == "#a"  # non-string answers are serialised
    with pytest.raises(RuntimeError, match="exhausted after 2 calls"):
        c.generate("p")


def test_get_client_selects_replay_from_the_environment(tmp_path, monkeypatch):
    f = tmp_path / "r.json"
    f.write_text('["x"]')
    monkeypatch.setenv("LLM_PROVIDER", "replay")
    monkeypatch.setenv("LLM_REPLAY_FILE", str(f))
    assert get_client().generate("p").text == "x"


def test_find_definitions_locates_literal_locators_and_not_built_ones():
    hits = find_definitions('locator("#amount")')
    assert hits and hits[0]["file"] == "framework/pages/transfer_page.py" and "#amount" in hits[0]["text"]
    assert find_definitions('locator("#definitely-not-in-the-code")') == []
    assert find_definitions(None) == []
    # f-string locators are built at run time, so the expanded text is not in the source
    assert find_definitions('locator("input[name=\'customer.firstName\']")') == []


def helper_that_reports_its_callers():
    return stack_frames()


def test_stack_frames_show_the_callers_and_skip_the_healing_machinery():
    frames = helper_that_reports_its_callers()
    assert [f["function"] for f in frames[-2:]] == [
        "test_stack_frames_show_the_callers_and_skip_the_healing_machinery", "helper_that_reports_its_callers"]
    assert frames[-1]["file"] == "tests/test_healing_building_blocks.py"
    assert not any(f["file"].startswith("framework/healing/") for f in frames)
