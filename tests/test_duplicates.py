"""Duplicate detection with a stand-in embedder: the arithmetic, the threshold, the index file and the rules that stop false alarms."""
import hashlib
from pathlib import Path

import pytest

from ai_testgen.bug_report import BugReport
from ai_testgen.duplicates import SIMILAR_THRESHOLD, DuplicateIndex, embedding_text, fingerprint
from framework.healing.collector import load_failure_context
from framework.similarity import cosine


class WordEmbedder:
    """Bag of words in 64 buckets: texts that share words get similar vectors, like a very crude embedding model."""

    def embed(self, text):
        vector = [0.0] * 64
        for word in text.lower().replace(".", " ").split():
            vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
        return vector


def _report(title, expected="The page refuses the form.", actual="A payment request was sent."):
    return BugReport(title=title, classification="app_bug", summary="s", steps_to_reproduce=["a"], expected=expected, actual=actual, next_action="n")


def test_cosine_is_one_for_equal_direction_zero_for_unrelated_and_safe_for_empty():
    assert cosine([1, 2], [2, 4]) == pytest.approx(1.0) and cosine([1, 0], [0, 1]) == 0.0 and cosine([0, 0], [1, 1]) == 0.0


def test_the_text_that_is_embedded_says_what_is_wrong_and_nothing_about_the_test():
    text = embedding_text(_report("Rejected form posts a payment"))
    assert "Rejected form posts a payment" in text and "Expected: The page refuses the form." in text and "Actual: A payment request was sent." in text


def test_a_report_resembling_an_earlier_one_is_named_and_a_different_one_is_not():
    index, client = DuplicateIndex("m"), WordEmbedder()
    assert index.check_and_add(client, "bug-a", _report("Rejected form posts a payment request")) is None  # nothing earlier
    same = index.check_and_add(client, "bug-b", _report("Rejected form still posts a payment request"))
    assert same is not None and same.id == "bug-a" and same.similarity >= SIMILAR_THRESHOLD and same.kind == "similar"
    other = _report("Negative transfer amount is accepted", expected="A negative amount is refused.", actual="The transfer completes.")
    assert index.check_and_add(client, "bug-c", other) is None


def test_the_threshold_decides_where_similar_becomes_duplicate():
    near = _report("Rejected form posts a payment request", actual="The request went out.")
    for threshold, expected in ((0.99, None), (0.5, "bug-a")):
        index, client = DuplicateIndex("m"), WordEmbedder()  # a fresh index each time: a stored report is itself the nearest for the next one
        index.check_and_add(client, "bug-a", _report("Rejected form posts a payment request"))
        found = index.check_and_add(client, "bug-b", near, threshold=threshold)
        assert (found.id if found else None) == expected


def test_rerunning_the_same_failure_replaces_its_entry_instead_of_duplicating_itself():
    index, client = DuplicateIndex("m"), WordEmbedder()
    index.check_and_add(client, "bug-a", _report("Rejected form posts a payment request"))
    assert index.check_and_add(client, "bug-a", _report("Rejected form posts a payment request")) is None
    assert [r["id"] for r in index.records] == ["bug-a"]


def test_the_index_survives_a_save_and_load_and_remembers_its_embedding_model(tmp_path):
    path, client = tmp_path / "index.json", WordEmbedder()
    first = DuplicateIndex("nomic", path)
    first.check_and_add(client, "bug-a", _report("Rejected form posts a payment request"))
    first.save()
    again = DuplicateIndex("nomic", path)
    assert again.check_and_add(client, "bug-b", _report("Rejected form still posts a payment request")).id == "bug-a"
    with pytest.raises(ValueError, match="vectors of different models cannot be compared"):
        DuplicateIndex("another-model", path)


def test_saving_without_a_path_is_an_error():
    with pytest.raises(ValueError, match="no path"):
        DuplicateIndex("m").save()


SAMPLES = Path(__file__).resolve().parent.parent / "framework/healing/samples"


def _ctx(name):
    return load_failure_context(next(SAMPLES.glob(f"*{name}.json")))


def test_equal_fingerprints_are_the_same_failure_even_when_the_wording_is_unrelated():
    index, client = DuplicateIndex("m"), WordEmbedder()
    fp = "assertion|get_by_text('x')|expected"
    index.check_and_add(client, "bug-a", _report("Alpha beta gamma", "one", "two"), failure_fingerprint=fp)
    found = index.check_and_add(client, "bug-b", _report("Completely different words here", "three", "four"), failure_fingerprint=fp)
    assert found is not None and found.id == "bug-a" and found.kind == "same_failure" and found.similarity == 1.0


def test_no_fingerprint_means_no_same_failure_claim():
    index, client = DuplicateIndex("m"), WordEmbedder()
    index.check_and_add(client, "bug-a", _report("Alpha beta gamma", "one", "two"))
    assert index.check_and_add(client, "bug-b", _report("Delta epsilon zeta", "three", "four")) is None


def test_the_fingerprint_ignores_numbers_but_not_the_locator_or_the_kind():
    one, other = _ctx("test_sample_id_renamed"), _ctx("test_sample_button_text_changed")
    assert fingerprint(one) == fingerprint(one) and fingerprint(one) != fingerprint(other)
    shifted = load_failure_context(next(SAMPLES.glob("*test_sample_id_renamed.json")))
    shifted.error.message = shifted.error.message.replace("3000ms", "9000ms")
    assert fingerprint(shifted) == fingerprint(one)
    assert "locator_not_found" in fingerprint(one) and "#" in fingerprint(one)
