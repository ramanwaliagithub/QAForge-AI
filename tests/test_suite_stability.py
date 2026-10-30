"""The stability script must run exactly the selection it was given.

Its first real use measured the wrong thing for four hours: `--alluredir <dir>` (space form) widened collection to the
deliberately failing healing samples and generated tests, so every run "failed". These tests pin the command shape.
"""
import sys
from pathlib import Path

from scripts.suite_stability import build_command, count_collected


def test_options_use_the_equals_form_and_never_a_bare_directory_argument():
    cmd = build_command([], Path("/tmp/j.xml"), Path("/tmp/allure"))
    assert "--alluredir=/tmp/allure" in cmd and "--junitxml=/tmp/j.xml" in cmd
    assert "/tmp/allure" not in cmd and "--alluredir" not in cmd  # the space-separated form is the bug


def test_default_selection_is_the_suite_and_reruns_are_off():
    cmd = build_command([], Path("j.xml"), Path("a"))
    assert cmd[:4] == [sys.executable, "-m", "pytest", "tests"] and "--reruns=0" in cmd


def test_explicit_selection_replaces_the_default():
    cmd = build_command(["ai_testgen/generated", "-m", "ai"], Path("j.xml"), Path("a"))
    assert cmd[3:6] == ["ai_testgen/generated", "-m", "ai"] and "tests" not in cmd


def test_collection_count_matches_a_plain_collect_only():
    """The collected count must not depend on the options the script adds (472 vs 514 was the bug)."""
    import subprocess

    plain = subprocess.run([sys.executable, "-m", "pytest", "tests/test_sources_parse.py", "--collect-only", "-q",
                            "-p", "no:cacheprovider", "--reruns=0"], capture_output=True, text=True).stdout
    expected = int(next(line for line in reversed(plain.strip().splitlines()) if "collected" in line).split()[0])
    assert count_collected(["tests/test_sources_parse.py"]) == expected
