"""The mutation harness: its catalogue and its plugin must agree, and its pieces must do what they say."""
import sys
from pathlib import Path

import pytest

from scripts.mutation_check import MUTANTS, PLUGIN_DIR, build_command, failed_tests

sys.path.insert(0, str(PLUGIN_DIR))
import qaforge_mutants


def test_the_catalogue_and_the_plugin_define_the_same_mutants():
    assert sorted(MUTANTS) == qaforge_mutants.MUTANTS


def test_every_mutant_has_exactly_one_kind_of_behaviour():
    both = set(qaforge_mutants.INIT_SCRIPTS) & set(qaforge_mutants.ROUTES)
    assert not both, f"a mutant should change either the page or the network, not both: {sorted(both)}"


def test_the_command_runs_serially_with_reruns_off_and_loads_the_plugin_by_name():
    cmd = build_command(Path("/tmp/x.xml"))
    assert "--reruns=0" in cmd and "-n" not in cmd and cmd[cmd.index("-p", cmd.index("--junitxml=/tmp/x.xml")) + 1] == "qaforge_mutants"
    assert "--junitxml=/tmp/x.xml" in cmd  # `--opt=value`, see docs/notes/day17.md


def test_failed_tests_lists_failures_and_errors_but_not_passes_or_skips(tmp_path):
    junit = tmp_path / "r.xml"
    junit.write_text('<testsuites><testsuite><testcase name="ok"/><testcase name="bad"><failure message="x"/></testcase>'
                     '<testcase name="boom"><error message="y"/></testcase><testcase name="skipped"><skipped/></testcase>'
                     "</testsuite></testsuites>")
    assert failed_tests(junit) == ["bad", "boom"]


def test_an_unknown_mutant_name_is_refused_loudly(monkeypatch):
    monkeypatch.setenv("QAFORGE_MUTANT", "no_such_mutant")
    with pytest.raises(pytest.UsageError):
        qaforge_mutants.pytest_configure(config=None)


def test_without_the_variable_the_plugin_changes_nothing(monkeypatch):
    from playwright.sync_api import Browser

    monkeypatch.delenv("QAFORGE_MUTANT", raising=False)
    before = Browser.new_context
    qaforge_mutants.pytest_configure(config=None)
    assert Browser.new_context is before
