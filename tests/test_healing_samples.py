"""Regression tests on real failure contexts captured from deliberately broken tests (see scripts/make_failure_samples.py)."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from framework.healing.collector import load_failure_context

SAMPLES = Path("framework/healing/samples")


def sample(name: str):
    return load_failure_context(next(SAMPLES.glob(f"*test_sample_{name}.json")))


@pytest.mark.parametrize("name, kind, hint, where, locator", [
    ("id_renamed", "locator_not_found", "locator", "page_object", 'locator("#amt")'),
    ("button_text_changed", "locator_not_found", "locator", "page_object",
     'get_by_role("button", name="Transfer Money", exact=True)'),
    ("locator_too_generic", "strict_mode_violation", "locator", "page_object", 'locator("option")'),
    ("expect_on_missing_element", "assertion_element_missing", "maybe", "test",
     'get_by_role("heading", name="Transfer Completed!")'),
    ("wrong_text_on_found_element", "assertion", "no", "test", 'get_by_role("heading", name="Transfer Complete!")'),
])
def test_sample_is_classified_as_designed(name, kind, hint, where, locator):
    e = sample(name).error
    assert (e.kind, e.heal_hint, e.raised_in, e.locator) == (kind, hint, where, locator)


@pytest.mark.parametrize("name", ["id_renamed", "button_text_changed", "locator_too_generic",
                                  "expect_on_missing_element", "wrong_text_on_found_element"])
def test_sample_has_everything_a_healer_needs(name):
    ctx = sample(name)
    assert ctx.test_id.endswith(f"test_sample_{name}")
    assert ctx.page.url.startswith("http") and ctx.page.title
    assert ctx.page.aria_snapshot and ctx.page.elements and "<html" in ctx.page.html.lower()
    assert ctx.screenshot and (SAMPLES / ctx.screenshot).stat().st_size > 1000
    assert ctx.error.frames, "should point at project source lines"
    assert "Aria snapshot" not in ctx.error.message, "snapshot lives in page.aria_snapshot, not the message"


def test_the_answer_is_in_the_captured_page_for_the_renamed_id():
    """Day 14 needs the real element to be findable from the sample: the amount input is still there, id #amount."""
    elements = sample("id_renamed").page.elements
    assert any(e.get("id") == "amount" and e["visible"] for e in elements)
    assert not any(e.get("id") == "amt" for e in elements)


def test_the_answer_is_in_the_captured_page_for_the_changed_button_text():
    elements = sample("button_text_changed").page.elements
    assert any(e.get("value") == "Transfer" and e.get("type") == "submit" for e in elements)
    assert not any(e.get("value") == "Transfer Money" for e in elements)


def test_failing_frames_point_into_the_page_object_for_locator_failures():
    inner = sample("id_renamed").error.frames[-1]
    assert inner["file"] == "framework/pages/base_page.py" and "wait_for" in inner["code"]
    outer = [f["file"] for f in sample("id_renamed").error.frames]
    assert "framework/healing/sample_tests/test_broken_locators.py" in outer


def _run_pytest(args, failure_dir, tmp_path):
    env = {**os.environ, "FAILURE_DIR": str(failure_dir), "ACTION_TIMEOUT_MS": "2000", "EXPECT_TIMEOUT_MS": "2000"}
    return subprocess.run(
        [sys.executable, "-m", "pytest", *args, "-q", "-p", "no:cacheprovider", "--reruns", "0",
         f"--alluredir={tmp_path / 'allure'}", "--tb=no"],
        env=env, capture_output=True, text=True,
    )


def test_pytest_hook_writes_the_context_when_a_test_fails(tmp_path):
    out = tmp_path / "failures"
    proc = _run_pytest(["framework/healing/sample_tests/test_broken_locators.py::test_sample_id_renamed"], out, tmp_path)
    assert "1 failed" in proc.stdout
    files = sorted(p.name for p in out.iterdir())
    assert [Path(f).suffix for f in files] == [".json", ".png"]
    assert load_failure_context(next(out.glob("*.json"))).error.kind == "locator_not_found"


def test_pytest_hook_writes_nothing_when_tests_pass(tmp_path):
    out = tmp_path / "failures"
    proc = _run_pytest(["tests/test_logging_utils.py"], out, tmp_path)
    assert "passed" in proc.stdout and not out.exists()
