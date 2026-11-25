"""The architecture diagram in the README names real files and folders: a rename must update the diagram."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text()
MERMAID = re.search(r"```mermaid\n(.*?)```", README, re.S)


def test_the_readme_has_a_mermaid_diagram():
    assert MERMAID and "flowchart" in MERMAID.group(1)


def test_every_path_in_the_diagram_exists():
    paths = set(re.findall(r"(?<![\w/])((?:[a-z_]+/)+(?:[a-z_]+\.py)?|[a-z_]+\.py)(?![\w])", MERMAID.group(1)))
    known_files = {path.name for path in ROOT.rglob("*.py") if ".venv" not in path.parts}
    missing = []
    for token in sorted(paths):
        if token.endswith("/"):
            exists = (ROOT / token).is_dir()
        elif "/" in token:
            exists = (ROOT / token).is_file()
        else:
            exists = token in known_files  # a bare file name, named after the folder it sits in on the same line
        if not exists:
            missing.append(token)
    assert not missing, f"the diagram mentions paths that do not exist: {missing}"


def test_the_diagram_is_not_trivially_empty():
    paths = re.findall(r"(?:[a-z_]+/)+[a-z_]*\.?[a-z]*", MERMAID.group(1))
    assert len(paths) >= 15
