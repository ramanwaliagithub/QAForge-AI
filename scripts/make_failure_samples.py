"""Run the deliberately broken sample tests and keep the collected failure contexts.

Usage: uv run python -m scripts.make_failure_samples [heldout]
Writes JSON + PNG into framework/healing/samples/ (committed, used by tests and by the Day 14 suggester).
With `heldout`: framework/healing/sample_tests/test_heldout_locators.py -> framework/healing/samples_heldout/.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from framework.healing.collector import load_failure_context

HELDOUT = "heldout" in sys.argv
OUT = Path("framework/healing/samples_heldout" if HELDOUT else "framework/healing/samples")
TESTS = "framework/healing/sample_tests/" + ("test_heldout_locators.py" if HELDOUT else "test_broken_locators.py")
OUT.mkdir(parents=True, exist_ok=True)
for old in list(OUT.glob("*.json")) + list(OUT.glob("*.png")):
    old.unlink()

env = {**os.environ, "FAILURE_DIR": str(OUT), "ACTION_TIMEOUT_MS": "3000", "EXPECT_TIMEOUT_MS": "3000"}
with tempfile.TemporaryDirectory() as allure_dir:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TESTS, "-q", "-p", "no:cacheprovider",
         "--reruns", "0", f"--alluredir={allure_dir}", "--tb=no"],
        env=env, capture_output=True, text=True,
    )
print(proc.stdout.strip().splitlines()[-1])

rows = []
for path in sorted(OUT.glob("*.json")):
    ctx = load_failure_context(path)
    e = ctx.error
    rows.append((path.stem.rsplit("test_", 1)[-1], e.kind, e.heal_hint, e.raised_in, e.locator))
width = max(len(r[0]) for r in rows) if rows else 0
for name, kind, hint, where, locator in rows:
    print(f"{name:{width}}  {kind:26} hint={hint:8} in={where:11} {locator}")
print(json.dumps({"samples": len(rows)}))
