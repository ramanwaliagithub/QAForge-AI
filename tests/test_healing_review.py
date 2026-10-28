import json
from pathlib import Path

import pytest

from framework.healing.review import (
    build_proposals, decide, empty_review, load_review, merge_review, proposal_id, render_html, render_markdown,
    save_review, score_proposal, summary_counts,
)

PAGE = 'class P:\n    @property\n    def amount(self):\n        return self.page.locator("#amt")\n'


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "p.py").write_text(PAGE)
    return tmp_path


def event(test="t::a", failed='locator("#amt")', suggestion='locator("#amount")', outcome="healed", **kw):
    base = dict(test_id=test, action="fill", failed_locator=failed, suggestion=suggestion, outcome=outcome, strategy="css",
                reason="the amount input", confidence=0.9, attempts=1, verified=outcome == "healed", repaired_from=None,
                element={"tag": "input", "id": "amount"})
    return {**base, **kw}


def proposals(events, repo):
    return build_proposals(events, roots=("pages",), repo_root=repo)


def test_identical_heals_in_several_tests_become_one_proposal(repo):
    (p,) = proposals([event("t::a"), event("t::b"), event("t::a")], repo)
    assert p["count"] == 3 and p["tests"] == ["t::a", "t::b"] and p["id"] == proposal_id('locator("#amt")', 'locator("#amount")')
    assert p["status"] == "proposed" and p["decided_at"] is None
    assert p["definitions"] == [{"file": "pages/p.py", "line": 4, "text": 'return self.page.locator("#amt")'}]


def test_only_heals_become_proposals_not_skips_or_failures(repo):
    evs = [event(), event(outcome="skipped_guard", suggestion=None), event(outcome="no_suggestion", suggestion=None),
           event(outcome="error", suggestion=None)]
    assert len(proposals(evs, repo)) == 1


def test_different_suggestions_for_the_same_old_locator_are_separate_proposals(repo):
    ps = proposals([event(), event(suggestion='get_by_label("Amount")', strategy="label")], repo)
    assert len(ps) == 2 and ps[0]["id"] != ps[1]["id"]


def test_score_components_are_transparent_and_ordered_sensibly(repo):
    (strong,) = proposals([event(strategy="role", suggestion='get_by_role("textbox")')], repo)
    (weak,) = proposals([event(confidence=0.2, attempts=3, repaired_from='locator("#a.b")', failed='locator("#gone")')], repo)
    assert 0 <= weak["score"] < strong["score"] <= 1
    assert set(strong["score_breakdown"]) >= {"base", "retry_verified", "first_attempt", "semantic_locator", "one_source_definition"}
    assert strong["score_breakdown"]["one_source_definition"] == 0.1 and weak["score_breakdown"]["one_source_definition"] == 0.0
    assert weak["score_breakdown"]["harness_repair"] == -0.1


def test_the_models_self_reported_confidence_barely_moves_the_score(repo):
    (hi,) = proposals([event(confidence=1.0)], repo)
    (lo,) = proposals([event(confidence=0.0)], repo)
    assert 0 < hi["score"] - lo["score"] <= 0.1


def test_flags_say_why_a_proposal_cannot_just_be_applied(repo):
    (p,) = proposals([event(failed='locator("#built-at-runtime")', confidence=0.3, repaired_from="x")], repo)
    text = " ".join(p["flags"])
    assert "no_source_definition" in text and "non_semantic_locator" in text and "low_model_confidence" in text and "repaired_by_harness" in text
    (ok,) = proposals([event(strategy="role")], repo)
    assert ok["flags"] == []


def test_merge_keeps_human_decisions_and_applied_history(repo):
    review = merge_review(empty_review(), proposals([event(), event(failed='locator("#x")', suggestion='locator("#y")')], repo))
    a, b = review["proposals"]
    decide(review, [a["id"]], "approved", "looks right")
    b["status"], b["applied_at"], b["applied_diff"] = "applied", "2026-10-28T00:00:00+00:00", "DIFF"
    # a new run sees the same two proposals again, with updated facts
    again = proposals([event("t::new"), event("t::more"), event(failed='locator("#x")', suggestion='locator("#y")')], repo)
    merged = merge_review(review, again)
    by_id = {p["id"]: p for p in merged["proposals"]}
    assert by_id[a["id"]]["status"] == "approved" and by_id[a["id"]]["note"] == "looks right" and by_id[a["id"]]["count"] == 2
    assert by_id[b["id"]]["status"] == "applied" and by_id[b["id"]]["applied_diff"] == "DIFF"
    assert summary_counts(merged) == {"proposed": 0, "approved": 1, "rejected": 0, "applied": 1}


def test_decide_accepts_unique_prefixes_and_rejects_bad_input(repo):
    review = merge_review(empty_review(), proposals([event()], repo))
    pid = review["proposals"][0]["id"]
    decide(review, [pid[:4]], "rejected", "wrong element")
    assert review["proposals"][0]["status"] == "rejected" and review["proposals"][0]["decided_at"]
    with pytest.raises(KeyError):
        decide(review, ["zzzz"], "approved")
    with pytest.raises(ValueError, match="cannot set status"):
        decide(review, [pid], "applied")
    review["proposals"][0]["status"] = "applied"
    with pytest.raises(ValueError, match="already applied"):
        decide(review, [pid], "approved")


def test_review_file_round_trip_and_schema_check(tmp_path, repo):
    path = tmp_path / "r.json"
    assert load_review(path)["proposals"] == []
    review = merge_review(empty_review(), proposals([event()], repo))
    save_review(review, path)
    assert load_review(path)["proposals"][0]["failed_locator"] == 'locator("#amt")'
    path.write_text(json.dumps({"schema": 99}))
    with pytest.raises(ValueError, match="schema"):
        load_review(path)


def test_markdown_report_shows_old_new_diff_score_and_what_to_do(repo):
    review = merge_review(empty_review(), proposals([event(), event(failed='locator("#dyn")', suggestion='locator("#q")')], repo))
    md = render_markdown(review, [event(outcome="skipped_guard", suggestion=None)], roots=("pages",), repo_root=repo)
    assert "No source file has been changed" in md and "heuristic" in md
    assert "**Old:** `locator(\"#amt\")`" in md and "**New:** `locator(\"#amount\")`" in md
    assert "`pages/p.py:4`" in md and "```diff" in md and '+        return self.page.locator("#amount")' in md
    assert "apply` would refuse: no_match" in md          # the other proposal cannot be patched
    assert "Not proposals" in md and "1x skipped_guard" in md
    assert "approve <id>" in md


def test_html_report_escapes_everything_it_prints(repo):
    nasty = event(reason="<script>alert(1)</script>", test="t::<b>x</b>")
    review = merge_review(empty_review(), proposals([nasty], repo))
    page = render_html(review, roots=("pages",), repo_root=repo)
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "<b>x</b>" not in page and page.startswith("<!doctype html>") and "No source file has been changed" in page
