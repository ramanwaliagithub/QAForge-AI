"""Run a pytest selection many times with reruns OFF and report the flake rate per test.

Usage: uv run python -m scripts.suite_stability <label> <runs> [pytest args...]
Examples:
    uv run python -m scripts.suite_stability suite 30
    uv run python -m scripts.suite_stability generated 10 ai_testgen/generated -m ai
Writes reports/phase2/<label>.json. `--reruns 0` is forced: a stability number must not hide the failures that a
rerun would absorb. A run "fails" if any test failed or errored; xfail and skip do not count. Do not run this while the
machine is short of memory (browser launch timeouts pollute the numbers, see docs/notes/day12.md).
"""
import json
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

LABEL = sys.argv[1]
RUNS = int(sys.argv[2])
PYTEST_ARGS = sys.argv[3:]


def run_once(index: int) -> dict:
    """One pytest run: return its wall time, test count and the failing tests with their first error line."""
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "run.xml"
        started = time.monotonic()
        subprocess.run(
            [sys.executable, "-m", "pytest", *PYTEST_ARGS, "-q", "-p", "no:cacheprovider", "-n", "3", "--reruns", "0",
             f"--junitxml={junit}", "--alluredir", str(Path(tmp) / "allure"), "--tb=line"],
            capture_output=True, text=True, check=False,
        )
        seconds = round(time.monotonic() - started, 1)
        tests, failures = 0, []
        for case in ET.parse(junit).getroot().iter("testcase"):
            tests += 1
            problem = next((c for c in case if c.tag in ("failure", "error")), None)
            if problem is not None:
                text = (problem.get("message") or problem.text or "").strip().splitlines()
                failures.append({"test": f'{case.get("classname")}::{case.get("name")}', "reason": text[0][:200] if text else ""})
    return {"run": index, "seconds": seconds, "tests": tests, "failures": failures}


def main() -> None:
    """Run the selection RUNS times, print each run and write the aggregate report."""
    runs = []
    for i in range(1, RUNS + 1):
        result = run_once(i)
        runs.append(result)
        print(f"run {i:>3}/{RUNS}: {result['tests']} tests, {len(result['failures'])} failed, {result['seconds']}s", flush=True)

    failing_runs = [r for r in runs if r["failures"]]
    per_test = Counter(f["test"] for r in runs for f in r["failures"])
    reasons = {}
    for r in runs:
        for f in r["failures"]:
            reasons.setdefault(f["test"], Counter())[f["reason"]] += 1
    summary = {
        "label": LABEL, "pytest_args": PYTEST_ARGS, "runs": RUNS, "reruns": 0,
        "runs_with_any_failure": len(failing_runs),
        "run_failure_rate": round(len(failing_runs) / RUNS, 3),
        "tests_per_run": runs[0]["tests"] if runs else 0,
        "seconds_per_run_median": sorted(r["seconds"] for r in runs)[len(runs) // 2] if runs else 0,
        "failing_tests": [{"test": t, "failed_in_runs": n, "reasons": dict(reasons[t])} for t, n in per_test.most_common()],
        "per_run": runs,
    }
    out = Path("reports/phase2")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{LABEL}.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\n{LABEL}: {len(failing_runs)}/{RUNS} runs had at least one failure")
    for item in summary["failing_tests"]:
        print(f"  {item['failed_in_runs']:>3}x  {item['test']}")
        for reason, n in item["reasons"].items():
            print(f"         {n}x {reason}")


main()
