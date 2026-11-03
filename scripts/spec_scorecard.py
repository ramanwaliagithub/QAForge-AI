"""Score an implementation of specs/001-billpay-page-and-tests.md against the spec's acceptance criteria.

Usage: uv run python -m scripts.spec_scorecard <checkout_dir> <label> [--runs 3]
Example: uv run python -m scripts.spec_scorecard ../some-worktree vague

The rubric is the spec's own criteria (numbers in brackets are the criterion numbers), fixed BEFORE any implementation was looked at.
It scores only what a script can decide; whether the assertions are meaningful is judged by reading (docs/notes/day18.md).
The checkout is run with THIS repository's interpreter from inside the checkout (pytest.ini has `pythonpath = .`, so the
checkout's own `framework` is imported). Results go to reports/day18/<label>.json.
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

from framework.locator_audit import audit_paths

PAGE = "framework/pages/bill_pay_page.py"
INIT = "framework/pages/__init__.py"
TESTS = "tests/test_bill_pay.py"
QUALITY = "tests/test_locator_quality.py"
ALLOWED_CHANGES = {PAGE, INIT, TESTS, QUALITY}
REQUIRED_TESTS = [
    "test_bill_pay_form_shows_every_field_and_the_customers_account",
    "test_empty_submit_requires_every_field",
    "test_mismatched_account_numbers_are_refused",
    "test_non_numeric_amount_is_refused",
    "test_successful_payment_is_confirmed_and_debits_the_account",
]
REQUIRED_MEMBERS = {"path", "FIELDS", "open", "fill_payment", "submit", "pay", "field_error", "result_heading", "result_message",
                    "from_account"}
BANNED_ATTRIBUTES = {"nth", "first", "last", "wait_for_timeout", "sleep"}
REPO_CHECKS = ["tests/test_locator_quality.py", "tests/test_lint.py", "tests/test_docstrings.py", "tests/test_sources_parse.py"]


def _calls_expect(node: ast.AST) -> bool:
    """True if the subtree calls `expect(...)`."""
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "expect" for n in ast.walk(node))


def _class_members(tree: ast.Module, name: str) -> tuple[bool, set[str], bool]:
    """(class found, its method and class-attribute names, whether it subclasses BasePage)."""
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            members = set()
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    members.add(item.name)
                elif isinstance(item, ast.Assign):
                    members |= {t.id for t in item.targets if isinstance(t, ast.Name)}
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    members.add(item.target.id)
            return True, members, any(isinstance(b, ast.Name) and b.id == "BasePage" for b in node.bases)
    return False, set(), False


def _exports(init_source: str, name: str) -> bool:
    """True if `name` is both imported in and listed in `__all__` of the package __init__."""
    tree = ast.parse(init_source)
    imported = any(isinstance(n, ast.ImportFrom) and name in [a.name for a in n.names] for n in ast.walk(tree))
    listed = any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)
                 and name in [e.value for e in getattr(n.value, "elts", []) if isinstance(e, ast.Constant)] for n in ast.walk(tree))
    return imported and listed


def _banned(tree: ast.Module) -> list[str]:
    """Banned constructs: sleeps, fixed waits, position locators, XPath."""
    found = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr in BANNED_ATTRIBUTES:
            found.append(f"line {n.lineno}: .{n.attr}")
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith(("//", "xpath=")):
            found.append(f"line {n.lineno}: xpath {n.value[:30]!r}")
    return found


def static_checks(page_source: str | None, tests_source: str | None, init_source: str | None) -> dict:
    """The checks that need only the source text (criteria 1, 2, 4 names, 5, 6, 7). Pure, so it is unit-tested."""
    result: dict = {}
    if page_source is None:
        result["1_page_object_file"] = False
    else:
        page = ast.parse(page_source)
        found, members, based = _class_members(page, "BillPayPage")
        result["1_page_object_file"] = True
        result["1_class_subclasses_basepage"] = found and based
        result["1_missing_members"] = sorted(REQUIRED_MEMBERS - members)
        result["1_exported_from_package"] = _exports(init_source or "", "BillPayPage")
        in_open = {id(n) for f in ast.walk(page) if isinstance(f, ast.FunctionDef) and f.name == "open" for n in ast.walk(f)}
        result["2_assertions_in_page_object"] = sum(
            1 for n in ast.walk(page) if id(n) not in in_open and (isinstance(n, ast.Assert) or (
                isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "expect")))
        result["6_banned_in_page_object"] = _banned(page)
    if tests_source is None:
        result["4_tests_file"] = False
    else:
        tree = ast.parse(tests_source)
        tests = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        names = [t.name for t in tests]
        result["4_tests_file"] = True
        result["4_test_functions"] = len(names)
        result["4_names_match"] = sorted(names) == sorted(REQUIRED_TESTS)
        result["4_missing_names"] = sorted(set(REQUIRED_TESTS) - set(names))
        result["5_tests_without_expect"] = [t.name for t in tests if not _calls_expect(t)]
        result["6_banned_in_tests"] = _banned(tree)
        result["7_fixtures"] = {t.name: [a.arg for a in t.args.args] for t in tests}
        payment = next((t for t in tests if "success" in t.name), None)
        result["7_payment_test_uses_new_customer_page"] = bool(payment) and "new_customer_page" in [a.arg for a in payment.args.args]
    return result


def parse_summary(output: str) -> dict:
    """Counts from pytest's last summary line, e.g. '5 passed, 1 skipped in 12.3s'."""
    counts = {"passed": 0, "failed": 0, "error": 0}
    summary = next((line for line in reversed(output.strip().splitlines()) if re.search(r"\d+ (passed|failed|error)", line)), "")
    for number, word in re.findall(r"(\d+) (passed|failed|errors?)", summary):
        counts["error" if word.startswith("error") else word] += int(number)
    return counts


def _pytest(checkout: Path, *args: str) -> str:
    """Run pytest inside the checkout with this repo's interpreter (reruns off); return its output."""
    cmd = [sys.executable, "-m", "pytest", *args, "-q", "-p", "no:cacheprovider", "--reruns=0", "--tb=line"]
    return subprocess.run(cmd, cwd=checkout, capture_output=True, text=True, check=False).stdout


def _changed(checkout: Path) -> list[str]:
    """Paths changed or added in the checkout (tracked changes and untracked files)."""
    out = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=checkout, capture_output=True, text=True, check=True).stdout
    return sorted(line[3:] for line in out.splitlines())


def _read(checkout: Path, rel: str) -> str | None:
    """File text, or None when the file does not exist."""
    path = checkout / rel
    return path.read_text() if path.exists() else None


def main() -> None:
    """Score one checkout and write reports/day18/<label>.json."""
    checkout, label = Path(sys.argv[1]).resolve(), sys.argv[2]
    runs = int(sys.argv[sys.argv.index("--runs") + 1]) if "--runs" in sys.argv else 3
    report = static_checks(_read(checkout, PAGE), _read(checkout, TESTS), _read(checkout, INIT))
    if (checkout / PAGE).exists():
        findings = audit_paths([checkout / PAGE])
        report["6_weak_selectors_in_page_object"] = [f"{f.selector} ({f.tier})" for f in findings if f.tier in ("css", "fragile")]
        report["3_non_semantic_selectors"] = sorted({f.selector for f in findings if f.tier != "semantic"})
    if (checkout / TESTS).exists():
        collected = _pytest(checkout, "--collect-only", TESTS)
        report["4_collected"] = sum(1 for line in collected.splitlines() if "::" in line)
        report["9_runs_n3"] = [parse_summary(_pytest(checkout, TESTS, "-n", "3")) for _ in range(runs)]
        report["9_serial_run"] = parse_summary(_pytest(checkout, TESTS))
    report["10_repo_checks"] = parse_summary(_pytest(checkout, *REPO_CHECKS))
    changed = _changed(checkout)
    report["11_changed_paths"] = changed
    report["11_outside_deliverables"] = [p for p in changed if p not in ALLOWED_CHANGES]
    report["size_lines"] = {rel: len((_read(checkout, rel) or "").splitlines()) for rel in (PAGE, TESTS)}
    out = Path("reports/day18")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{label}.json").write_text(json.dumps(report, indent=2) + "\n")
    for key, value in report.items():
        print(f"{key:42} {value}")


if __name__ == "__main__":
    main()
