"""Run generated tests and summarise pass rate and failure reasons.

Usage: uv run python -m scripts.run_generated [label]
Writes reports/testgen/<label>.json and prints a markdown table.
"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

label = sys.argv[1] if len(sys.argv) > 1 else "run"
out_dir = Path("reports/testgen")
out_dir.mkdir(parents=True, exist_ok=True)
junit = out_dir / f"{label}.xml"

subprocess.run(
    [sys.executable, "-m", "pytest", "ai_testgen/generated", "-m", "ai", "-q", "-p", "no:cacheprovider",
     f"--junitxml={junit}", "--tb=line", "-n", "3"],
    check=False, capture_output=True, text=True,
)

rows = []
for case in ET.parse(junit).getroot().iter("testcase"):
    problem = next((c for c in case if c.tag in ("failure", "error")), None)
    reason = ""
    if problem is not None:
        reason = (problem.get("message") or problem.text or "").strip().splitlines()[0][:160]
    rows.append({"test": case.get("classname", "").split(".")[-1], "passed": problem is None, "reason": reason})

passed = sum(r["passed"] for r in rows)
summary = {"label": label, "total": len(rows), "passed": passed, "pass_rate": round(passed / len(rows), 3) if rows else 0, "results": rows}
(out_dir / f"{label}.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"{label}: {passed}/{len(rows)} passed ({summary['pass_rate']:.0%})")
for r in rows:
    print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['test']}  {r['reason']}")
