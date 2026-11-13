"""Custom quality gate for tests, written for what AI-generated tests get wrong and linters do not look for.

    uv run python -m scripts.check_tests [files or folders]      (default: framework, tests, ai_testgen/generated)

Rules (ids are stable; a finding prints as `path:line: QF00N message`):
  QF001  a fixed wait: `time.sleep`, `sleep`, `wait_for_timeout`                      (CLAUDE.md T2)
  QF002  an assertion that cannot fail or says nothing: `assert True`, `assert 1`, `assert "text"`, `assert x == x`,
         `assert a or True`
  QF003  an `expect(...)` that is never completed: a bare `expect(x)` statement, or `expect(x).to_be_visible` without the call
  QF004  a test function that checks nothing: no assert, no `expect`, no `pytest.raises`/`fail`, no `assert_*`/`check_*` helper call

QF001 applies to every file given; QF002-QF004 only to test files (`test_*.py`). A line can opt out with
`# qaforge: allow QF001 <reason>`; the reason is required, so an exception is a visible decision.
`EXCLUDED` lists the one folder of deliberately broken sample tests.
"""
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGETS = ("framework", "tests", "ai_testgen/generated")
# Deliberately broken tests that exist to fail (healing samples): they act, they do not assert, and pytest never collects them.
EXCLUDED = ("framework/healing/sample_tests",)
SLEEPS = {"sleep", "wait_for_timeout"}
CHECKING_PREFIXES = ("assert_", "check_", "verify_")
ALLOW = re.compile(r"#\s*qaforge:\s*allow\s+(QF\d{3})\s+\S+")


@dataclass(frozen=True)
class Finding:
    """One rule violation: where it is, which rule, and what to do about it."""

    path: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule} {self.message}"


def _call_name(node: ast.AST) -> str:
    """`a.b.c(...)` -> "c", `f(...)` -> "f", anything else -> ""."""
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _is_expect_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _call_name(node) == "expect"


def _always_true(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return bool(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return isinstance(node.operand, ast.Constant) and not node.operand.value
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.Is, ast.LtE, ast.GtE)):
        # `f() is f()` is a real check (is the call idempotent?); only a call-free comparison of a thing with itself says nothing
        same = ast.dump(node.left) == ast.dump(node.comparators[0])
        return same and not any(isinstance(n, ast.Call) for n in ast.walk(node))
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        return any(_always_true(value) for value in node.values)
    return False


def _checks_something(func: ast.AST) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name in ("expect", "raises", "fail", "xfail", "skip", "warns") or name.startswith(CHECKING_PREFIXES):
                return True
    return False


def check_source(source: str, filename: str = "<string>", *, is_test_file: bool = True) -> list[Finding]:
    """All findings in one file's source. `is_test_file` switches on QF002-QF004."""
    tree = ast.parse(source, filename)
    lines = source.splitlines()
    found: list[Finding] = []

    def add(node: ast.AST, rule: str, message: str) -> None:
        line = getattr(node, "lineno", 1)
        match = ALLOW.search(lines[line - 1]) if line <= len(lines) else None
        if not (match and match.group(1) == rule):
            found.append(Finding(filename, line, rule, message))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) in SLEEPS:
            add(node, "QF001", f"`{_call_name(node)}` is a fixed wait: wait for a condition with a web-first assertion instead")
        if not is_test_file:
            continue
        if isinstance(node, ast.Assert) and _always_true(node.test):
            add(node, "QF002", "this assertion can never fail or compares a value with itself: assert something the page or app decided")
        if isinstance(node, ast.Expr):
            if _is_expect_call(node.value):
                add(node, "QF003", "`expect(...)` with no matcher checks nothing: add `.to_be_visible()`, `.to_have_text(...)` or similar")
            elif isinstance(node.value, ast.Attribute) and _is_expect_call(node.value.value):
                add(node, "QF003", f"`.{node.value.attr}` is not called: it needs parentheses, otherwise nothing is checked")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test") and not _checks_something(node):
            add(node, "QF004", f"`{node.name}` has no assert, `expect` or `pytest.raises`: it can only fail by crashing")
    return sorted(found, key=lambda f: (f.line, f.rule))


def _files(targets: list[str]) -> list[Path]:
    paths: list[Path] = []
    for target in targets:
        path = Path(target)
        path = path if path.is_absolute() else ROOT / path
        paths += sorted(path.rglob("*.py")) if path.is_dir() else [path]
    skipped = tuple(str(ROOT / folder) for folder in EXCLUDED)
    return [p for p in paths if p.suffix == ".py" and "__pycache__" not in p.parts and not str(p).startswith(skipped)]


def check_paths(targets: list[str]) -> list[Finding]:
    found: list[Finding] = []
    for path in _files(targets):
        shown = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        found += check_source(path.read_text(), shown, is_test_file=path.name.startswith("test_"))
    return found


def main(argv: list[str]) -> int:
    findings = check_paths(argv or list(DEFAULT_TARGETS))
    for finding in findings:
        print(finding)
    if findings:
        print(f"\n{len(findings)} finding(s). Fix them, or opt out on the line with `# qaforge: allow QFnnn <reason>`.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
