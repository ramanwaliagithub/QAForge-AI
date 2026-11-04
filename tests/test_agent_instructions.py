"""The agent instruction files must not rot: same rule ids everywhere, every path they mention exists, and they stay short.

Instructions that point at files that no longer exist, or that drift apart between tools, are worse than none: an agent follows them
faithfully (see docs/notes/day18.md). A length cap is part of the design: a long rule file is read less carefully.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = ROOT / "CLAUDE.md"
COPILOT = ROOT / ".github" / "copilot-instructions.md"
CHECKLIST = ROOT / "docs" / "test-writing-checklist.md"
PLACEHOLDERS = {"tests/test_x.py"}  # examples in the text, not real files
MAX_LINES = {CLAUDE: 90, COPILOT: 60}
RULE_ID = re.compile(r"\[([A-Z]\d)\]")


def _ids(path: Path) -> list[str]:
    return RULE_ID.findall(path.read_text())


def _repo_files() -> set[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    return set(out.splitlines())


def _mentioned_paths(path: Path) -> set[str]:
    """Things inside backticks that look like a repo path or a markdown/python file name."""
    found = set()
    for span in re.findall(r"`([^`]+)`", path.read_text()):
        for part in span.split():
            part = part.rstrip(",.;:)")
            if "://" in part or "<" in part or "*" in part or part in PLACEHOLDERS:
                continue
            if part.startswith(".") and not part.startswith(".github/"):  # a bare extension such as `.py`
                continue
            if re.match(r"^\.?[A-Za-z_][\w./-]*$", part) and ("/" in part or part.endswith((".md", ".py"))):
                found.add(part)
    return found


def test_rule_ids_are_unique_in_claude_md():
    ids = _ids(CLAUDE)
    assert len(ids) == len(set(ids)), f"duplicate rule ids: {sorted({i for i in ids if ids.count(i) > 1})}"


def test_copilot_file_has_exactly_the_rules_of_claude_md():
    assert set(_ids(COPILOT)) == set(_ids(CLAUDE)), (
        f"only in CLAUDE.md: {sorted(set(_ids(CLAUDE)) - set(_ids(COPILOT)))}; only in copilot: {sorted(set(_ids(COPILOT)) - set(_ids(CLAUDE)))}")


def test_checklist_references_only_rules_that_exist():
    unknown = set(_ids(CHECKLIST)) - set(_ids(CLAUDE))
    assert not unknown, f"the checklist cites rules that CLAUDE.md does not define: {sorted(unknown)}"


def test_every_rule_is_checked_by_the_checklist():
    """The checklist is how the rules are applied; a rule it never mentions is a rule nobody runs (page-object and code rules excepted)."""
    exempt = {"P1", "P2", "P3", "C3"}
    missing = set(_ids(CLAUDE)) - set(_ids(CHECKLIST)) - exempt
    assert not missing, f"not in the checklist: {sorted(missing)}"


def test_paths_mentioned_in_the_instruction_files_exist():
    files = _repo_files()
    missing = []
    for doc in (CLAUDE, COPILOT, CHECKLIST):
        for token in sorted(_mentioned_paths(doc)):
            if token.endswith("/"):
                exists = (ROOT / token).is_dir()
            elif "/" in token:
                exists = token in files
            else:  # a bare file name such as conftest.py or transfer_page.py: anywhere in the repo
                exists = any(f == token or f.endswith("/" + token) for f in files)
            if not exists:
                missing.append(f"{doc.name}: {token}")
    assert not missing, "instruction files mention paths that do not exist:\n" + "\n".join(missing)


def test_instruction_files_stay_short():
    for path, limit in MAX_LINES.items():
        lines = len(path.read_text().splitlines())
        assert lines <= limit, f"{path.name} has {lines} lines (limit {limit}): cut a rule or move detail to docs/"


def test_instruction_files_do_not_credit_a_tool():
    """Standing rule for this repo: no co-author trailers or generated-by credits in files, commits or PRs."""
    for path in (CLAUDE, COPILOT, CHECKLIST):
        text = path.read_text().lower()
        assert "co-authored-by:" not in text and "generated with" not in text, path.name
