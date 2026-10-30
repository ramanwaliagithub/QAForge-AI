"""`pytest --heal` end to end: real browser, real ParaBank, a replay model (canned answers), a subprocess per scenario."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

E2E = "framework/healing/sample_tests/test_heal_e2e.py"
AMOUNT = {"strategy": "css", "css": "#amount", "reason": "amount input", "confidence": 0.9}
BUTTON = {"strategy": "role", "role": "button", "name": "Transfer", "exact": True, "reason": "submit", "confidence": 0.8}
BAD = {"strategy": "css", "css": "#nothing-like-this"}


def source_fingerprint() -> str:
    """Hash of every Python source file that healing could conceivably touch."""
    h = hashlib.sha256()
    for root in ("framework", "tests", "ai_testgen", "conftest.py"):
        p = Path(root)
        for f in ([p] if p.is_file() else sorted(p.rglob("*.py"))):
            h.update(str(f).encode() + f.read_bytes())
    return h.hexdigest()


def run(tmp_path, args, replies=None, extra_env=None):
    replay = tmp_path / "replies.json"
    replay.write_text(json.dumps(replies or []))
    env = {**os.environ, "LLM_PROVIDER": "replay", "LLM_REPLAY_FILE": str(replay), "HEAL_REPORT": str(tmp_path / "healing.json"),
           "ACTION_TIMEOUT_MS": "2500", "EXPECT_TIMEOUT_MS": "2500", **(extra_env or {})}
    before = source_fingerprint()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *args, "-p", "no:cacheprovider", "--reruns", "0", f"--alluredir={tmp_path / 'allure'}", "--tb=short"],
        env=env, capture_output=True, text=True,
    )
    assert source_fingerprint() == before, "a source file was modified: healing must never edit source"
    report = tmp_path / "healing.json"
    return proc, (json.loads(report.read_text()) if report.exists() else None)


def test_heal_flag_heals_a_broken_locator_reports_it_and_edits_nothing(tmp_path):
    proc, report = run(tmp_path, [f"{E2E}::test_e2e_amount_id_renamed", "--heal"], [AMOUNT])
    out = proc.stdout
    assert "1 passed" in out and "HealedLocatorWarning" in out, out[-1500:]   # passed, but NOT silently
    assert "healed  locator(\"#amount\")" not in out and 'locator("#amt")  ->  locator("#amount")' in out
    assert "no source file was changed" in out
    (event,) = report["events"]
    assert report["summary"] == {"events": 1, "healed": 1}
    assert (event["outcome"], event["verified"], event["kind"], event["action"]) == ("healed", True, "locator_not_found", "fill")
    assert event["failed_locator"] == 'locator("#amt")' and event["suggestion"] == 'locator("#amount")'
    assert event["status"] == "proposed" and event["confidence"] == 0.9 and event["test_id"].endswith("test_e2e_amount_id_renamed")
    assert event["caller_frames"] and event["page_url"].endswith("/transfer.htm")


def test_without_the_flag_the_broken_locator_fails_and_no_report_is_written(tmp_path):
    proc, report = run(tmp_path, [f"{E2E}::test_e2e_amount_id_renamed"], [AMOUNT])
    assert "1 failed" in proc.stdout and "HealedLocatorWarning" not in proc.stdout and "self-healing" not in proc.stdout
    assert report is None


def test_an_assertion_failure_is_never_healed(tmp_path):
    # the replay file is EMPTY: if the model were asked anything it would raise, and the event would say "error"
    proc, report = run(tmp_path, [f"{E2E}::test_e2e_assertion_fails_with_a_working_page_object", "--heal"], [])
    assert "1 failed" in proc.stdout and "Transfer Done!" in proc.stdout
    assert report["summary"] == {"events": 0} and report["events"] == []


def test_when_no_suggestion_is_acceptable_the_test_fails_with_its_original_error(tmp_path):
    proc, report = run(tmp_path, [f"{E2E}::test_e2e_amount_id_renamed", "--heal"], [BAD, BAD, BAD])
    assert "1 failed" in proc.stdout and "#amt" in proc.stdout and "HealedLocatorWarning" not in proc.stdout
    assert report["summary"] == {"events": 1, "no_suggestion": 1}
    assert len(report["events"][0]["rejections"]) == 3


def test_events_from_xdist_workers_are_merged_into_one_report(tmp_path):
    proc, report = run(tmp_path, [f"{E2E}::test_e2e_amount_id_renamed", f"{E2E}::test_e2e_button_text_changed", "--heal", "-n", "2"],
                       [AMOUNT, BUTTON])
    assert "2 passed" in proc.stdout, proc.stdout[-1500:]
    assert report["summary"] == {"events": 2, "healed": 2}
    assert {e["action"] for e in report["events"]} == {"fill", "click"}


def test_warnings_can_be_made_errors_so_ci_can_refuse_healed_passes(tmp_path):
    proc, _ = run(tmp_path, [f"{E2E}::test_e2e_amount_id_renamed", "--heal", "-W", "error::framework.healing.plugin.HealedLocatorWarning"], [AMOUNT])
    assert "HealedLocatorWarning" in proc.stdout and "1 error" in proc.stdout, proc.stdout[-1200:]
