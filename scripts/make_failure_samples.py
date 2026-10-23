"""Run the deliberately broken sample tests and keep the collected failure contexts.

Usage: uv run python -m scripts.make_failure_samples
Writes JSON + PNG into framework/healing/samples/ (committed, used by tests and by the Day 14 suggester).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from framework.healing.collector import load_failure_context

OUT = Path("framework/healing/samples")
OUT.mkdir(parents=True, exist_ok=True)
for old in list(OUT.glob("*.json")) + list(OUT.glob("*.png")):
    old.unlink()

env = {**os.environ, "FAILURE_DIR": str(OUT), "ACTION_TIMEOUT_MS": "3000", "EXPECT_TIMEOUT_MS": "3000"}
with tempfile.TemporaryDirectory() as allure_dir:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "framework/healing/sample_tests", "-q", "-p", "no:cacheprovider",
         "--reruns", "0", f"--alluredir={allure_dir}", "--tb=no"],
        env=env, capture_output=True, text=True,
    )
print(proc.stdout.strip().splitlines()[-1])

rows = []
for path in sorted(OUT.glob("*.json")):
    ctx = load_failure_context(path)
    e = ctx.error
    rows.append((path.stem.split("::")[-1].split("test_sample_")[-1], e.kind, e.heal_hint, e.raised_in, e.locator))
width = max(len(r[0]) for r in rows) if rows else 0
for name, kind, hint, where, locator in rows:
    print(f"{name:{width}}  {kind:26} hint={hint:8} in={where:11} {locator}")
print(json.dumps({"samples": len(rows), "failed_tests_expected": 5}))
