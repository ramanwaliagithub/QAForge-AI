import json

import pytest

from framework.healing.collector import (
    FailureContext, capture_page_state, collect_failure_context, load_failure_context, slugify,
)
from framework.pages import TransferPage

HTML = """<html><head><title>Fixture page</title></head><body>
<h1>Transfer Funds</h1>
<input id="amount" name="amt" type="text">
<select id="from"><option>111</option></select>
<input type="submit" value="Transfer">
<a href="activity.htm?id=1">111</a>
</body></html>"""


def test_slugify_is_filesystem_safe_and_bounded():
    assert slugify("tests/test_x.py::test_a[param 1]") == "tests_test_x.py_test_a_param_1"
    assert len(slugify("a" * 500)) == 120
    assert slugify("///") == "test"


def test_capture_page_state_collects_url_title_aria_elements_html(page):
    page.set_content(HTML)
    state = capture_page_state(page)
    assert state.title == "Fixture page" and state.capture_errors == []
    assert 'heading "Transfer Funds"' in state.aria_snapshot
    by_id = {e.get("id"): e for e in state.elements if e.get("id")}
    assert by_id["amount"]["name"] == "amt" and by_id["amount"]["visible"] is True
    assert any(e.get("value") == "Transfer" for e in state.elements)
    assert any(e.get("href") == "activity.htm?id=1" for e in state.elements)
    assert "<h1>Transfer Funds</h1>" in state.html and state.html_truncated is False


def test_html_is_truncated_to_the_limit(page):
    page.set_content("<body>" + "<p>x</p>" * 5000 + "</body>")
    state = capture_page_state(page, max_html=1000)
    assert len(state.html) == 1000 and state.html_truncated is True


def test_capture_survives_a_closed_page(browser):
    ctx = browser.new_context()
    pg = ctx.new_page()
    ctx.close()
    state = capture_page_state(pg)  # must not raise
    assert state.capture_errors, "problems are recorded instead of raised"


def _real_locator_failure(page):
    """Produce a genuine Playwright timeout on a broken locator, with the exception object attached."""
    page.set_content(HTML)
    page.set_default_timeout(500)
    try:
        page.locator("#amt").fill("5")  # the real id is #amount
    except Exception as e:  # noqa: BLE001
        return e
    pytest.fail("expected a timeout")


def test_collect_failure_context_writes_json_and_screenshot(page, tmp_path):
    exc = _real_locator_failure(page)
    path = collect_failure_context(page, "tests/test_demo.py::test_fill_amount", exc, out_dir=tmp_path)

    assert path == tmp_path / "tests_test_demo.py_test_fill_amount.json"
    assert (tmp_path / "tests_test_demo.py_test_fill_amount.png").stat().st_size > 1000
    data = json.loads(path.read_text())
    assert data["schema"] == 1 and data["screenshot"].endswith(".png")
    assert data["error"]["kind"] == "locator_not_found" and data["error"]["heal_hint"] == "locator"
    assert data["error"]["locator"] == 'locator("#amt")' and data["error"]["action"] == "fill"
    assert data["page"]["title"] == "Fixture page"
    assert data["error"]["frames"][-1]["function"] == "_real_locator_failure"


def test_load_failure_context_round_trips(page, tmp_path):
    path = collect_failure_context(page, "t::x", _real_locator_failure(page), out_dir=tmp_path)
    ctx = load_failure_context(path)
    assert isinstance(ctx, FailureContext) and ctx.error.kind == "locator_not_found"
    assert ctx.page.elements and ctx.test_id == "t::x"


def test_load_rejects_unknown_schema(tmp_path):
    bad = tmp_path / "x.json"
    bad.write_text(json.dumps({"schema": 99}))
    with pytest.raises(ValueError, match="schema"):
        load_failure_context(bad)


def test_collector_never_raises(tmp_path):
    class Broken:  # a "page" that fails every call
        def __getattr__(self, name):
            raise RuntimeError("page is gone")

    # unwritable output dir and a broken page: still returns None/Path, never raises
    assert collect_failure_context(Broken(), "t::y", RuntimeError("x"), out_dir=tmp_path / "ok") is not None
    assert collect_failure_context(Broken(), "t::y", RuntimeError("x"), out_dir=__file__ + "/nope") is None
