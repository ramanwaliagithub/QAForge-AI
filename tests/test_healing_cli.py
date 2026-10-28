import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from framework.healing.__main__ import main
from framework.healing.review import load_review

PAGE = '''class P:
    @property
    def amount(self):
        return self.page.locator("#amt")

    @property
    def submit(self):
        return self.page.get_by_role("button", name="Transfer Money", exact=True)

    def dynamic(self, n):
        return self.page.locator(f"input[name='{n}']")
'''
AMOUNT = ('locator("#amt")', 'locator("#amount")', "css", "fill")
BUTTON = ('get_by_role("button", name="Transfer Money", exact=True)', 'get_by_role("button", name="Transfer", exact=True)', "role", "click")
DYNAMIC = ("locator(\"input[name='first']\")", 'locator("#first")', "css", "fill")


def ev(failed, suggestion, strategy, action, test="t::a"):
    return dict(test_id=test, action=action, failed_locator=failed, suggestion=suggestion, outcome="healed", strategy=strategy,
                reason="r", confidence=0.9, attempts=1, verified=True, repaired_from=None, element={"tag": "input"})


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "pages").mkdir()
    (tmp_path / "pages" / "p.py").write_text(PAGE)
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "init")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write_events(repo, *events):
    (repo / "healing.json").write_text(json.dumps({"events": [ev(*e) for e in events]}))


def cli(*argv, answer=None, tty=True):
    out = io.StringIO()
    code = main(["--events", "healing.json", "--review", "review.json", "--roots", "pages", *argv], out=out,
                input_fn=lambda prompt: answer or "", isatty=tty)
    return code, out.getvalue()


def ids(repo):
    return {p["failed_locator"]: p["id"] for p in load_review(repo / "review.json")["proposals"]}


def page_text(repo):
    return (repo / "pages" / "p.py").read_text()


def test_report_writes_review_markdown_and_html_without_touching_source(repo):
    write_events(repo, AMOUNT, BUTTON)
    code, out = cli("report")
    assert code == 0 and "2 proposals (2 proposed" in out
    assert (repo / "review.json").exists() and (repo / "healing_review.md").exists() and (repo / "healing_review.html").exists()
    assert "No source file has been changed" in (repo / "healing_review.md").read_text()
    assert page_text(repo) == PAGE


def test_report_without_events_says_what_to_do(repo):
    code, out = cli("report")
    assert code == 2 and "pytest --heal" in out


def test_approving_and_rejecting_and_the_decisions_survive_a_new_report(repo):
    write_events(repo, AMOUNT, BUTTON)
    cli("report")
    i = ids(repo)
    assert cli("approve", i[AMOUNT[0]][:5], "--note", "ok")[0] == 0
    assert cli("reject", i[BUTTON[0]], "--note", "wrong")[0] == 0
    cli("report")  # a later run must not reset decisions
    p = {p["id"]: p for p in load_review(repo / "review.json")["proposals"]}
    assert p[i[AMOUNT[0]]]["status"] == "approved" and p[i[AMOUNT[0]]]["note"] == "ok"
    assert p[i[BUTTON[0]]]["status"] == "rejected" and p[i[BUTTON[0]]]["note"] == "wrong"


def test_approve_errors_are_reported_not_raised(repo):
    write_events(repo, AMOUNT)
    cli("report")
    assert cli("approve", "nope")[0] == 2
    assert cli("approve")[0] == 1


def test_approve_all_only_takes_verified_single_definition_proposals_above_the_score(repo):
    write_events(repo, AMOUNT, BUTTON, DYNAMIC)   # scores: role 1.00, css id 0.99, css built at run time 0.89 (no definition)
    cli("report")

    def statuses():
        return {p["failed_locator"]: p["status"] for p in load_review(repo / "review.json")["proposals"]}

    cli("approve", "--all", "--min-score", "1.0")
    assert statuses() == {BUTTON[0]: "approved", AMOUNT[0]: "proposed", DYNAMIC[0]: "proposed"}
    cli("approve", "--all", "--min-score", "0.95")
    assert statuses()[AMOUNT[0]] == "approved"
    cli("approve", "--all", "--min-score", "0.0")
    assert statuses()[DYNAMIC[0]] == "proposed", "no literal source definition: only a human may approve it"


def test_nothing_is_applied_unless_approved(repo):
    write_events(repo, AMOUNT)
    cli("report")
    code, out = cli("apply", "--yes")
    assert code == 0 and "no approved proposals" in out and page_text(repo) == PAGE
    cli("reject", ids(repo)[AMOUNT[0]])
    cli("apply", "--yes")
    assert page_text(repo) == PAGE


def test_dry_run_shows_the_diff_and_changes_nothing(repo):
    write_events(repo, AMOUNT)
    cli("report")
    cli("approve", ids(repo)[AMOUNT[0]])
    code, out = cli("apply", "--dry-run")
    assert code == 0 and '-        return self.page.locator("#amt")' in out and "dry run: not applied" in out
    assert page_text(repo) == PAGE and load_review(repo / "review.json")["proposals"][0]["status"] == "approved"


def test_without_yes_and_without_a_terminal_nothing_is_applied(repo):
    write_events(repo, AMOUNT)
    cli("report")
    cli("approve", ids(repo)[AMOUNT[0]])
    code, out = cli("apply", tty=False)
    assert "re-run with --yes" in out and page_text(repo) == PAGE


def test_the_interactive_prompt_must_say_yes(repo):
    write_events(repo, AMOUNT)
    cli("report")
    cli("approve", ids(repo)[AMOUNT[0]])
    code, out = cli("apply", answer="n")
    assert "skipped" in out and page_text(repo) == PAGE
    code, out = cli("apply", answer="y")
    assert "applied to pages/p.py:4" in out and 'locator("#amount")' in page_text(repo)


def test_apply_patches_marks_applied_and_stores_the_diff(repo):
    write_events(repo, AMOUNT)
    cli("report")
    cli("approve", ids(repo)[AMOUNT[0]])
    code, out = cli("apply", "--yes")
    assert code == 0 and "1 applied" in out and "next: git diff" in out and "ACCEPTED entry" in out   # css note
    assert page_text(repo) == PAGE.replace('locator("#amt")', 'locator("#amount")')
    (p,) = load_review(repo / "review.json")["proposals"]
    assert p["status"] == "applied" and p["applied_at"] and '+        return self.page.locator("#amount")' in p["applied_diff"]
    code, out = cli("apply", "--yes")  # nothing left to do, and a second run must not patch again
    assert "no approved proposals" in out
    cli("report")  # a new report keeps the applied proposal as history
    assert load_review(repo / "review.json")["proposals"][0]["status"] == "applied"


def test_two_fixes_in_one_file_are_both_applied(repo):
    write_events(repo, AMOUNT, BUTTON)
    cli("report")
    cli("approve", *ids(repo).values())
    code, out = cli("apply", "--yes")
    assert code == 0 and "2 applied" in out, out
    assert 'locator("#amount")' in page_text(repo) and 'name="Transfer", exact=True' in page_text(repo)


def test_a_dirty_file_is_refused_and_allow_dirty_overrides(repo):
    write_events(repo, AMOUNT)
    cli("report")
    cli("approve", ids(repo)[AMOUNT[0]])
    (repo / "pages" / "p.py").write_text(PAGE + "# work in progress\n")
    code, out = cli("apply", "--yes")
    assert code == 1 and "REFUSED (dirty)" in out and 'locator("#amt")' in page_text(repo)
    code, out = cli("apply", "--yes", "--allow-dirty")
    assert code == 0 and 'locator("#amount")' in page_text(repo) and "# work in progress" in page_text(repo)


def test_proposals_that_cannot_be_patched_safely_are_refused_with_a_reason(repo):
    (repo / "pages" / "q.py").write_text('class Q:\n    x = self.page.locator("#dup")\n    y = self.page.locator("#dup")\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "q")
    write_events(repo, DYNAMIC, ('locator("#dup")', 'locator("#new")', "css", "click"))
    cli("report")
    cli("approve", *ids(repo).values())
    code, out = cli("apply", "--yes")
    assert code == 1 and "REFUSED (no_match)" in out and "REFUSED (ambiguous)" in out and "0 applied, 2 refused" in out
    assert page_text(repo) == PAGE
    assert {p["status"] for p in load_review(repo / "review.json")["proposals"]} == {"approved"}, "refused ones stay approved, unapplied"


def test_it_runs_as_a_module(repo):
    write_events(repo, AMOUNT)
    proc = subprocess.run([sys.executable, "-m", "framework.healing", "--events", "healing.json", "--review", "review.json",
                           "--roots", "pages", "report", "--format", "md"], capture_output=True, text=True,
                          env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent)})
    assert proc.returncode == 0 and "1 proposals" in proc.stdout, proc.stderr
