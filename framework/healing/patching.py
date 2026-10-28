"""Plan and apply a one-line locator fix to a page object, or refuse with a reason.

Editing source is the one risky step in the healing flow, so it is deliberately conservative:
- the failed locator must appear in the source EXACTLY ONCE, as literal text (not built from f-strings or variables);
- the patched file must still parse;
- a file with uncommitted changes is never touched (so a patch never mixes with someone's work in progress);
- planning (`plan_patch`) never writes; `apply_plan` is the only function that does.
"""
import ast
import difflib
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ROOTS = ("framework/pages",)


class PatchRefused(Exception):
    """The fix cannot be applied automatically. `code` is machine readable, the message says what to do."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class PatchPlan:
    file: str
    line: int          # 1-based
    old_line: str
    new_line: str
    diff: str
    new_content: str


def expr_variants(expr: str) -> list[str]:
    """The expression as Playwright logs it (double quotes), and the single-quoted spelling if that is lossless."""
    out = [expr]
    if '"' in expr and "'" not in expr:
        out.append(expr.replace('"', "'"))
    return out


def locate(expr: str, roots=DEFAULT_ROOTS, repo_root: Path | None = None) -> list[dict]:
    """Every line under `roots` that contains `expr` literally: [{file, line, text, matched}]."""
    repo_root = Path(repo_root or Path.cwd())
    hits = []
    for root in roots:
        for path in sorted((repo_root / root).rglob("*.py")):
            for n, line in enumerate(path.read_text().splitlines(), start=1):
                for variant in expr_variants(expr):
                    if variant in line:
                        hits.append({"file": str(path.relative_to(repo_root)), "line": n, "text": line.strip(), "matched": variant})
                        break
    return hits


def plan_patch(old_expr: str, new_expr: str, roots=DEFAULT_ROOTS, repo_root: Path | None = None) -> PatchPlan:
    """Work out the one-line change that replaces `old_expr` by `new_expr`, or raise PatchRefused. Writes nothing."""
    repo_root = Path(repo_root or Path.cwd())
    if not old_expr or not new_expr:
        raise PatchRefused("incomplete", "The proposal has no old or new locator.")
    hits = locate(old_expr, roots, repo_root)
    if not hits:
        raise PatchRefused("no_match", f"{old_expr} does not appear literally in {', '.join(roots)}. It is probably built at run "
                                       "time (f-string or variable) or defined elsewhere: change it by hand.")
    if len(hits) > 1:
        where = ", ".join(f"{h['file']}:{h['line']}" for h in hits)
        raise PatchRefused("ambiguous", f"{old_expr} appears {len(hits)} times ({where}); not guessing which one to change.")
    hit = hits[0]
    path = repo_root / hit["file"]
    lines = path.read_text().splitlines(keepends=True)
    old_line = lines[hit["line"] - 1]
    if old_line.count(hit["matched"]) != 1:
        raise PatchRefused("multiple_on_line", f"{hit['file']}:{hit['line']} contains the locator more than once.")
    # keep the file's quoting style: if it matched the single-quoted spelling, write the new locator the same way
    replacement = new_expr.replace('"', "'") if hit["matched"] != old_expr and "'" not in new_expr else new_expr
    new_line = old_line.replace(hit["matched"], replacement, 1)
    new_content = "".join(lines[: hit["line"] - 1] + [new_line] + lines[hit["line"]:])
    try:
        ast.parse(new_content)
    except SyntaxError as e:
        raise PatchRefused("syntax_error", f"the patched file would not parse ({e.msg}, line {e.lineno}); not applying.") from e
    diff = "".join(difflib.unified_diff(path.read_text().splitlines(keepends=True), new_content.splitlines(keepends=True),
                                        fromfile=f"a/{hit['file']}", tofile=f"b/{hit['file']}", n=2))
    return PatchPlan(hit["file"], hit["line"], old_line.rstrip("\n"), new_line.rstrip("\n"), diff, new_content)


def check_clean(file: str, repo_root: Path | None = None) -> None:
    """Refuse to patch a file that has uncommitted changes, or whose state git cannot tell us."""
    repo_root = Path(repo_root or Path.cwd())
    try:
        proc = subprocess.run(["git", "-C", str(repo_root), "status", "--porcelain", "--", file],
                              capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise PatchRefused("not_a_git_repo", f"cannot check whether {file} has uncommitted changes ({type(e).__name__}); "
                                             "use --allow-dirty to skip this check.") from e
    if proc.stdout.strip():
        raise PatchRefused("dirty", f"{file} has uncommitted changes ({proc.stdout.strip()[:2]!r}). Commit or stash them first, "
                                    "or pass --allow-dirty.")


def apply_plan(plan: PatchPlan, repo_root: Path | None = None) -> None:
    """Write the patched file (atomically). The caller has already shown the diff and got confirmation."""
    path = Path(repo_root or Path.cwd()) / plan.file
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(plan.new_content)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
