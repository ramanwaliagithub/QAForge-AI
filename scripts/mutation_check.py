"""Mutation check for a Bill Pay test suite: does it notice when the screen misbehaves?

Usage: uv run python -m scripts.mutation_check <checkout_dir> <label> [--out reports/day19]
Runs `tests/test_bill_pay.py` of the checkout once unmodified (it must pass) and once per mutant from
scripts/mutation_plugin/qaforge_mutants.py. A mutant is KILLED if at least one test fails. Survivors are blind spots.

Each mutant models a requirement of the Bill Pay story, specs/001 or CLAUDE.md. The list was fixed before any Day 19 arm was run.
Two of them (`payment_not_debited`, `payment_debited_twice`) model the spec's "takes the money out of the account"; the story given to the
vague prompts does not say so, so read those two as "extra", not "expected", for a run that never saw the spec.
"""
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent / "mutation_plugin"
TESTS = "tests/test_bill_pay.py"
# name -> the requirement it models. Names must match scripts/mutation_plugin/qaforge_mutants.py (tests/test_mutation_check.py).
MUTANTS = {
    "mismatch_hidden": "story: the two account numbers must match, and the customer is told when they do not",
    "city_required_hidden": "story: every payee field is required, with a message next to the field",
    "invalid_amount_text_changed": "story: the amount must be a number, with the right message",
    "rejected_form_posts": "CLAUDE.md T4: a rejected form must send nothing",
    "confirmation_amount_wrong": "story: the confirmation shows the amount paid",
    "confirmation_account_wrong": "story: the confirmation shows the from-account",
    "payment_not_debited": "spec 001: the payment takes the money out of the account",
    "payment_debited_twice": "spec 001: the account is debited by exactly the amount",
}


def build_command(junit: Path) -> list[str]:
    """The pytest command for one run: serial (the plugin patches this process), reruns off, plugin loaded by name."""
    return [sys.executable, "-m", "pytest", TESTS, "-q", "-p", "no:cacheprovider", "--reruns=0", "--tb=line",
            f"--junitxml={junit}", "-p", "qaforge_mutants"]


def failed_tests(junit: Path) -> list[str]:
    """Names of the tests that failed or errored in a junit file."""
    return sorted(case.get("name", "") for case in ET.parse(junit).getroot().iter("testcase")
                  if any(child.tag in ("failure", "error") for child in case))


def run(checkout: Path, mutant: str | None) -> list[str]:
    """Run the checkout's Bill Pay tests under one mutant (or none) and return the failing test names."""
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(filter(None, [str(PLUGIN_DIR), os.environ.get("PYTHONPATH")]))}
    env.pop("QAFORGE_MUTANT", None)
    if mutant:
        env["QAFORGE_MUTANT"] = mutant
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "run.xml"
        subprocess.run(build_command(junit), cwd=checkout, env=env, capture_output=True, text=True, check=False)
        return failed_tests(junit)


def main() -> None:
    """Run the baseline and every mutant against one checkout; write reports/<out>/<label>-mutation.json."""
    checkout, label = Path(sys.argv[1]).resolve(), sys.argv[2]
    out = Path(sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "reports/day19")
    baseline = run(checkout, None)
    if baseline:
        sys.exit(f"baseline is not green, nothing to mutate: {baseline}")
    results: dict[str, dict[str, Any]] = {}
    for name in MUTANTS:
        failing = run(checkout, name)
        results[name] = {"killed": bool(failing), "failing_tests": failing, "models": MUTANTS[name]}
        print(f"{name:30} {'KILLED  ' if failing else 'SURVIVED'} {', '.join(failing)}", flush=True)
    killed = sum(bool(r["killed"]) for r in results.values())
    report = {"label": label, "killed": killed, "total": len(results), "mutants": results}
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{label}-mutation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"\n{label}: {killed}/{len(results)} mutants killed")


if __name__ == "__main__":
    main()
