"""No unused imports, undefined names or other pyflakes findings anywhere in the repository (generated tests included)."""
from pathlib import Path

import pytest
from pyflakes.api import check
from pyflakes.reporter import Reporter

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = ("framework", "ai_testgen", "scripts", "tests")


class _Collect:
    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text.rstrip())

    def flush(self):
        pass


@pytest.mark.parametrize("folder", FOLDERS)
def test_pyflakes_is_clean(folder):
    out = _Collect()
    files = sorted((ROOT / folder).rglob("*.py"))
    for path in files:
        check(path.read_text(), str(path.relative_to(ROOT)), Reporter(out, out))
    assert not [line for line in out.lines if line], "\n".join(line for line in out.lines if line)


def test_conftest_pyflakes_is_clean():
    out = _Collect()
    check((ROOT / "conftest.py").read_text(), "conftest.py", Reporter(out, out))
    assert not [line for line in out.lines if line], "\n".join(out.lines)
