"""The shared flag parser of the scripts."""
import pytest

from scripts.flags import parse_flags


def test_values_bare_flags_and_positionals_are_separated():
    assert parse_flags(["label", "--n=30", "--register", "other"]) == ({"n": "30", "register": "1"}, ["label", "other"])


def test_a_value_may_contain_an_equals_sign_and_an_empty_value_stays_empty():
    assert parse_flags(["--query=a=b", "--empty="])[0] == {"query": "a=b", "empty": ""}


def test_a_space_separated_value_is_a_positional_not_the_flags_value():
    assert parse_flags(["--out", "reports/x"]) == ({"out": "1"}, ["reports/x"])


def test_nothing_in_nothing_out():
    assert parse_flags([]) == ({}, [])


def test_help_prints_the_usage_and_exits_before_anything_runs(capsys):
    with pytest.raises(SystemExit) as stop:
        parse_flags(["--help"], "usage text")
    assert stop.value.code == 0 and capsys.readouterr().out == "usage text\n"


def test_help_without_a_usage_text_is_just_a_flag():
    assert parse_flags(["--help"])[0] == {"help": "1"}
