"""The pre-commit hooks must stay wired to things that exist; a hook that points at a renamed module blocks every commit."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
HOOKS = {hook["id"]: hook for repo in CONFIG["repos"] for hook in repo["hooks"]}


def test_the_three_gates_are_hooks():
    assert {"ruff", "mypy", "check-tests"} <= set(HOOKS)


def test_hooks_run_through_uv_so_versions_come_from_the_lockfile():
    for hook_id in ("ruff", "mypy", "check-tests"):
        assert HOOKS[hook_id]["entry"].startswith("uv run "), hook_id


def test_the_gate_hook_points_at_a_module_that_exists():
    module = HOOKS["check-tests"]["entry"].split("-m ")[1].strip()
    assert (ROOT / (module.replace(".", "/") + ".py")).is_file()


def test_the_tools_the_hooks_run_are_locked_dev_dependencies():
    lock = (ROOT / "uv.lock").read_text()
    pyproject = (ROOT / "pyproject.toml").read_text()
    for tool in ("ruff", "mypy", "pre-commit"):
        assert f'name = "{tool}"' in lock and f'"{tool}' in pyproject, tool


def test_ruff_and_mypy_are_configured_in_pyproject():
    pyproject = (ROOT / "pyproject.toml").read_text()
    assert "[tool.ruff.lint]" in pyproject and "[tool.mypy]" in pyproject
