"""The documented surface stays documented: modules, public classes and non-trivial public functions need a docstring.

Tiny functions (up to 7 lines), properties, `...` stubs, private names and tests are exempt: a one-line body usually explains itself.
"""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"generated", "sample_tests"}
MIN_LINES = 8


def _sources():
    files = [ROOT / "conftest.py"]
    for folder in ("framework", "ai_testgen", "scripts"):
        files += sorted((ROOT / folder).rglob("*.py"))
    return [f for f in files if not SKIP_PARTS & set(f.parts) and not any(p.startswith("samples") for p in f.parts)]


def _missing(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    missing = []
    if path.name != "__init__.py" and not ast.get_docstring(tree):
        missing.append("module")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)) or node.name.startswith("_"):
            continue
        is_property = any(isinstance(d, ast.Name) and d.id == "property" for d in getattr(node, "decorator_list", []))
        long_enough = isinstance(node, ast.ClassDef) or node.end_lineno - node.lineno + 1 >= MIN_LINES
        is_stub = isinstance(node, ast.FunctionDef) and len(node.body) == 1 and ast.unparse(node.body[0]) == "..."  # Protocol method
        if long_enough and not is_property and not is_stub and not ast.get_docstring(node):
            missing.append(f"{type(node).__name__} {node.name} (line {node.lineno})")
    return missing


@pytest.mark.parametrize("path", _sources(), ids=lambda p: str(p.relative_to(ROOT)))
def test_public_surface_is_documented(path):
    assert not _missing(path), f"{path.relative_to(ROOT)} lacks a docstring for: {', '.join(_missing(path))}"
