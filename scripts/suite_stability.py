"""Run a pytest selection many times with reruns OFF and report the flake rate per test.

Usage: uv run python -m scripts.suite_stability <label> <runs> [pytest args...]
Examples:
    uv run python -m scripts.suite_stability suite 30
    uv run python -m scripts.suite_stability generated 10 ai_testgen/generated -m ai
With no pytest args the selection is `tests` (the suite). Writes reports/phase2/<label>.json. `--reruns 0` is forced: a
stability number must not hide the failures that a rerun would absorb. A run "fails" if any test failed or errored;
xfail and skip do not count. The number of collected tests is printed and recorded, and a change between runs is
reported: a selection that silently widens makes every number meaningless (see docs/notes/day17.md).
Do not edit source files while it runs (the healing e2e tests hash them), and do not run it while the machine is short
of memory (browser launch timeouts pollute the numbers, see docs/notes/day12.md).
"""
import json
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


def build_command(pytest_args: list[str], junit: Path, allure_dir: Path) -> list[str]:
    """The pytest command for one run.

    Options use the `--name=value` form on purpose: a space-separated `--alluredir <dir>` is parsed as a path argument
    (xdist workers re-parse it after the controller created the directory), which widened collection from 472 to 514
    tests and made every run of the first attempt fail on the deliberately broken samples.
    """
    selection = pytest_args or ["tests"]
    return [sys.executable, "-m", "pytest", *selection, "-q", "-p", "no:cacheprovider", "-n", "3", "--reruns=0",
            f"--junitxml={junit}", f"--alluredir={allure_dir}", "--tb=line"]


def count_collected(pytest_args: list[str]) -> int:
    """How many tests the selection collects (so a widened or empty selection is visible before any run)."""
    with tempfile.TemporaryDirectory() as tmp:
        cmd = build_command(pytest_args, Path(tmp) / "c.xml", Path(tmp) / "allure")
        out = subprocess.run([*cmd, "--collect-only"], capture_output=True, text=True, check=False).stdout
    for line in reversed(out.strip().splitlines()):
        if "collected" in line:
            return int(line.split()[0])
    return 0


def run_once(index: int, pytest_args: list[str]) -> dict:
    """One pytest run: return its wall time, test count and the failing tests with their first error line."""
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "run.xml"
        started = time.monotonic()
        subprocess.run(build_command(pytest_args, junit, Path(tmp) / "allure"), capture_output=True, text=True, check=False)
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
    """Run the selection N times, print each run and write the aggregate report."""
    label, n_runs, pytest_args = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    collected = count_collected(pytest_args)
    print(f"selection: {pytest_args or ['tests']}  collects {collected} tests", flush=True)
    runs = []
    for i in range(1, n_runs + 1):
        result = run_once(i, pytest_args)
        runs.append(result)
        flag = "" if result["tests"] == collected else f"  WARNING: ran {result['tests']} tests, collected {collected}"
        print(f"run {i:>3}/{n_runs}: {result['tests']} tests, {len(result['failures'])} failed, {result['seconds']}s{flag}", flush=True)

    failing_runs = [r for r in runs if r["failures"]]
    per_test = Counter(f["test"] for r in runs for f in r["failures"])
    reasons = {}
    for r in runs:
        for f in r["failures"]:
            reasons.setdefault(f["test"], Counter())[f["reason"]] += 1
    summary = {
        "label": label, "pytest_args": pytest_args or ["tests"], "runs": n_runs, "reruns": 0, "collected": collected,
        "collection_stable": all(r["tests"] == collected for r in runs),
        "runs_with_any_failure": len(failing_runs),
        "run_failure_rate": round(len(failing_runs) / n_runs, 3),
        "seconds_per_run_median": sorted(r["seconds"] for r in runs)[len(runs) // 2] if runs else 0,
        "failing_tests": [{"test": t, "failed_in_runs": n, "reasons": dict(reasons[t])} for t, n in per_test.most_common()],
        "per_run": runs,
    }
    out = Path("reports/phase2")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{label}.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"\n{label}: {len(failing_runs)}/{n_runs} runs had at least one failure")
    for item in summary["failing_tests"]:
        print(f"  {item['failed_in_runs']:>3}x  {item['test']}")
        for reason, n in item["reasons"].items():
            print(f"         {n}x {reason}")


if __name__ == "__main__":
    main()
