"""Rank the locators in framework/pages by resilience: `uv run python -m scripts.locator_audit`."""
import sys
from collections import Counter
from pathlib import Path

from framework.locator_audit import TIER_SCORE, audit_paths, score

paths = sorted(Path("framework/pages").glob("*_page.py"))
findings = audit_paths(paths)
by_tier = Counter(f.tier for f in findings)

if "--verbose" in sys.argv or "-v" in sys.argv:
    for f in findings:
        pos = "  [position]" if f.position else ""
        print(f"{f.tier:9} {Path(f.file).name}:{f.line:<3} {f.call}({f.selector!r}){pos}")
    print()
print("tiers: " + ", ".join(f"{t}={by_tier.get(t, 0)}" for t in TIER_SCORE))
print(f"locators={len(findings)}  position-dependent={sum(f.position for f in findings)}  score={score(findings)} / 3.0")
