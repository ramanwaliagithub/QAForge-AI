"""The scoring helpers of the duplicate and triage evaluations: a wrong formula would make every number in the notes wrong."""
import pytest

from scripts.dedupe_eval import at, auc, best
from scripts.triage_eval import score

PAIRS = [(0.9, True), (0.8, True), (0.7, False), (0.6, True), (0.5, False), (0.4, False)]


def test_auc_is_the_chance_a_duplicate_pair_outscores_a_non_duplicate_pair():
    assert auc(PAIRS) == pytest.approx(8 / 9)  # 3 duplicates x 3 others = 9 comparisons; only the 0.6 duplicate loses, to the 0.7 other
    assert auc([(1.0, True), (0.0, False)]) == 1.0 and auc([(0.0, True), (1.0, False)]) == 0.0 and auc([(0.5, True), (0.5, False)]) == 0.5


def test_precision_and_recall_at_a_threshold():
    row = at(PAIRS, 0.75)  # calls the 0.9 and 0.8 pairs: both true; one of three duplicates is missed
    assert (row["called"], row["precision"], row["recall"]) == (2, 1.0, 0.67)
    row = at(PAIRS, 0.6)  # calls four: three true duplicates and the 0.7 non-duplicate
    assert (row["called"], row["precision"], row["recall"]) == (4, 0.75, 1.0)


def test_nothing_called_gives_zero_not_a_division_error():
    assert at(PAIRS, 0.99) == {"threshold": 0.99, "called": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0}


def test_the_best_threshold_is_the_one_with_the_highest_f1():
    top = best(PAIRS)  # F1 by threshold: 0.9 -> 0.5, 0.8 -> 0.8, 0.7 -> 0.67, 0.6 -> 0.86
    assert (top["threshold"], top["f1"]) == (0.6, 0.86)


TRUTH = {"a": {"classes": ["app_bug"]}, "b": {"classes": ["test_bug", "ui_change"]}, "c": {"classes": ["test_bug"]}, "d": {"classes": ["app_bug"]}}


def test_triage_counts_right_unclear_and_wrong_apart_and_names_the_wrong_ones():
    rows = [{"input": "a", "classification": "app_bug"}, {"input": "b", "classification": "ui_change"},
            {"input": "c", "classification": "app_bug"}, {"input": "d", "classification": "unclear"}]
    result = score(rows, TRUTH)
    assert (result["total"], result["right"], result["unclear"], result["wrong"]) == (4, 2, 1, 1)
    assert result["wrong_items"] == ["c: said app_bug, accepted ['test_bug']"]
