"""Every Python file in the repository must at least parse.

Scripts are not imported by the suite, so a syntax error in one (a comment that swallowed a comma broke
scripts/run_generated.py for several days) would otherwise go unnoticed until someone ran it.
"""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted(
    p for folder in ("scripts", "framework", "ai_testgen", "tests") for p in (ROOT / folder).rglob("*.py")
) + [ROOT / "conftest.py"]


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_file_parses(path):
    ast.parse(path.read_text(), filename=str(path))
