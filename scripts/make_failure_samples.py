"""Run the deliberately broken sample tests and keep the collected failure contexts.

Usage: uv run python -m scripts.make_failure_samples [tuned|heldout|heldout2|heldout3]
Writes JSON + PNG into framework/healing/samples/ (committed, used by tests and by the Day 14 suggester).
Each set writes into its own folder (samples, samples_heldout, samples_heldout2); see the test files for what each breaks.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from framework.healing.collector import load_failure_context

# which sample set to generate: (output folder, test file)
SETS = {
    "tuned": ("samples", "test_broken_locators.py"),
    "heldout": ("samples_heldout", "test_heldout_locators.py"),
    "heldout2": ("samples_heldout2", "test_heldout2_locators.py"),
    "heldout3": ("samples_heldout3", "test_heldout3_locators.py"),
}
WHICH = next((a for a in sys.argv[1:] if a in SETS), "tuned")
OUT = Path("framework/healing") / SETS[WHICH][0]
TESTS = "framework/healing/sample_tests/" + SETS[WHICH][1]
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
