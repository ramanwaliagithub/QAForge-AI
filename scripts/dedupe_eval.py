"""How well does each way of comparing failures find the duplicates a person would find? Scored against reports/bugs/ground_truth.json.

    uv run python -m scripts.dedupe_eval [--dir=reports/bugs]

Needs the drafts written by scripts.draft_bug_reports. Every pair of failures is a case: a duplicate if the ground truth puts both in one root-cause
group. For each method the report gives AUC (how often a true duplicate pair scores above a non-duplicate pair), the best threshold and its
precision and recall, and the same at the shipped threshold. The ground truth is small (11 failures, 6 duplicate pairs among 55): read the numbers
as a first measurement, not as a benchmark.
"""
import itertools
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from ai_testgen.bug_report import BugReport
from ai_testgen.duplicates import SIMILAR_THRESHOLD, cosine, embedding_text, fingerprint
from framework.healing.collector import load_failure_context
from framework.llm_client import get_client
from scripts.flags import parse_flags

ROOT = Path(__file__).resolve().parent.parent
FIRST_GUESS = 0.85  # the threshold I set before measuring; kept in the report to show what measuring changed


def auc(pairs: list[tuple[float, bool]]) -> float:
    """Probability that a random duplicate pair scores higher than a random non-duplicate pair (ties count half)."""
    pos = [s for s, d in pairs if d]
    neg = [s for s, d in pairs if not d]
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def at(pairs: list[tuple[float, bool]], threshold: float) -> dict[str, float]:
    """Precision, recall and F1 when every pair scoring at least `threshold` is called a duplicate."""
    called = [d for s, d in pairs if s >= threshold]
    true_pos = sum(called)
    total_dups = sum(d for _, d in pairs)
    precision = true_pos / len(called) if called else 0.0
    recall = true_pos / total_dups
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"threshold": round(threshold, 3), "called": len(called), "precision": round(precision, 2), "recall": round(recall, 2), "f1": round(f1, 2)}


def best(pairs: list[tuple[float, bool]]) -> dict[str, float]:
    """The threshold with the best F1 on these very pairs (so, optimistic: it is fitted to the data it is scored on)."""
    return max((at(pairs, s) for s in sorted({s for s, _ in pairs})), key=lambda r: (r["f1"], r["threshold"]))


def main(argv: list[str]) -> None:
    """Embed the failures four ways, score every pair, and write the comparison."""
    load_dotenv()
    flags, _ = parse_flags(argv, __doc__)
    folder = ROOT / flags.get("dir", "reports/bugs")
    truth = json.loads((folder / "ground_truth.json").read_text())["failures"]
    names = sorted(truth)
    ctxs = {n: load_failure_context(folder / "inputs" / f"{n}.json") for n in names}
    drafts: dict[str, BugReport] = {}
    for path in folder.glob("bug-*.json"):
        data = json.loads(path.read_text())
        drafts[data["input"]] = BugReport(**data["report"])
    client = get_client()
    texts = {
        "draft (title, expected, actual)": {n: embedding_text(drafts[n]) for n in names},
        "draft, actual only": {n: drafts[n].actual for n in names},
        "draft with 'clustering:' prefix": {n: "clustering: " + embedding_text(drafts[n]) for n in names},
        "raw failure (kind, locator, message line)": {n: fingerprint(ctxs[n]).replace("|", " ") for n in names},
    }
    labels = {(a, b): truth[a]["group"] is not None and truth[a]["group"] == truth[b]["group"] for a, b in itertools.combinations(names, 2)}
    result: dict[str, Any] = {"failures": len(names), "pairs": len(labels), "duplicate_pairs": sum(labels.values()), "shipped_threshold": SIMILAR_THRESHOLD, "first_guess": FIRST_GUESS, "methods": {}}
    for method, per in texts.items():
        vectors = {n: client.embed(t) for n, t in per.items()}
        pairs = [(cosine(vectors[a], vectors[b]), d) for (a, b), d in labels.items()]
        dup_scores = sorted((round(s, 3) for s, d in pairs if d), reverse=True)
        top_non = round(max(s for s, d in pairs if not d), 3)
        result["methods"][method] = {"auc": round(auc(pairs), 2), "best": best(pairs), "at_shipped": at(pairs, SIMILAR_THRESHOLD), "at_first_guess": at(pairs, FIRST_GUESS),
                                     "duplicate_scores": dup_scores, "highest_non_duplicate": top_non}
    same = [(1.0 if fingerprint(ctxs[a]) == fingerprint(ctxs[b]) else 0.0, d) for (a, b), d in labels.items()]
    result["methods"]["fingerprint equal (no model)"] = {"auc": round(auc(same), 2), "best": at(same, 1.0), "wrong_pairs": [
        f"{a} ~ {b}" for (a, b), (s, d) in zip(labels, same, strict=True) if (s == 1.0) != d]}
    (folder / "dedupe_eval.json").write_text(json.dumps(result, indent=2) + "\n")
    for method, row in result["methods"].items():
        print(f"{method:44} AUC {row['auc']:.2f}  best {row['best']}")
        if "wrong_pairs" in row:
            print("   wrong pairs:", row["wrong_pairs"])


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
