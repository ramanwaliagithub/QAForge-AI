"""Healing review CLI:  python -m framework.healing  <report|list|approve|reject|apply>

    uv run pytest --heal                                  # writes reports/healing.json (proposals only)
    python -m framework.healing report                    # merge into reports/healing_review.json, write .md and .html
    python -m framework.healing list
    python -m framework.healing approve <id> [<id> ...]   # or: approve --all --min-score 0.8
    python -m framework.healing reject <id> --note "wrong element"
    python -m framework.healing apply [--dry-run] [--yes]  # patch approved proposals; shows each diff first
"""
import argparse
import os
import sys
from pathlib import Path

from framework.healing import review as rv
from framework.healing.patching import DEFAULT_ROOTS, PatchRefused, apply_plan, check_clean, plan_patch

DEFAULT_EVENTS = "reports/healing.json"
DEFAULT_REVIEW = "reports/healing_review.json"


def _paths(args):
    return (Path(args.events or os.getenv("HEAL_REPORT", DEFAULT_EVENTS)), Path(args.review or os.getenv("HEAL_REVIEW", DEFAULT_REVIEW)))


def _roots(args):
    return tuple(args.roots) if args.roots else DEFAULT_ROOTS


def _line(p: dict) -> str:
    where = f"{p['definitions'][0]['file']}:{p['definitions'][0]['line']}" if len(p["definitions"]) == 1 else f"{len(p['definitions'])} definitions"
    return f"{p['id']}  {p['status']:8} {p['score']:.2f}  {p['failed_locator']}  ->  {p['suggestion']}   [{where}]"


def cmd_report(args, out) -> int:
    import json
    events_path, review_path = _paths(args)
    if not events_path.exists():
        print(f"No {events_path}. Run `uv run pytest --heal` first.", file=out)
        return 2
    events = json.loads(events_path.read_text()).get("events", [])
    repo = Path.cwd()
    review = rv.merge_review(rv.load_review(review_path), rv.build_proposals(events, _roots(args), repo))
    rv.save_review(review, review_path)
    out_dir = Path(args.out_dir or review_path.parent)
    written = []
    if args.format in ("md", "both"):
        (out_dir / "healing_review.md").write_text(rv.render_markdown(review, events, _roots(args), repo) + "\n")
        written.append(out_dir / "healing_review.md")
    if args.format in ("html", "both"):
        (out_dir / "healing_review.html").write_text(rv.render_html(review, events, _roots(args), repo))
        written.append(out_dir / "healing_review.html")
    c = rv.summary_counts(review)
    print(f"{len(review['proposals'])} proposals ({', '.join(f'{v} {k}' for k, v in c.items())}) from {len(events)} heal events", file=out)
    for p in review["proposals"]:
        print("  " + _line(p), file=out)
    print("written: " + ", ".join(str(w) for w in [review_path, *written]), file=out)
    return 0


def cmd_list(args, out) -> int:
    review = rv.load_review(_paths(args)[1])
    for p in review["proposals"]:
        print(_line(p), file=out)
    if not review["proposals"]:
        print("no proposals; run `report` first", file=out)
    return 0


def cmd_decide(args, out, status: str) -> int:
    _, review_path = _paths(args)
    review = rv.load_review(review_path)
    ids = list(args.ids)
    if status == "approved" and args.all:
        ids += [p["id"] for p in review["proposals"]
                if p["status"] == "proposed" and p["verified"] and len(p["definitions"]) == 1 and p["score"] >= args.min_score]
    if not ids:
        print("nothing to decide: give proposal ids" + (" or use --all (verified, one source definition, score >= --min-score)" if status == "approved" else ""), file=out)
        return 1
    try:
        changed = rv.decide(review, ids, status, args.note or "")
    except (KeyError, ValueError) as e:
        print(f"error: {e}", file=out)
        return 2
    rv.save_review(review, review_path)
    for p in changed:
        print(f"{status}  {_line(p)}", file=out)
    return 0


def cmd_apply(args, out, input_fn=input, isatty=None) -> int:
    isatty = sys.stdin.isatty() if isatty is None else isatty
    _, review_path = _paths(args)
    repo = Path.cwd()
    review = rv.load_review(review_path)
    approved = [p for p in review["proposals"] if p["status"] == "approved"]
    if not approved:
        print("nothing to apply: no approved proposals (see `list`, `approve`)", file=out)
        return 0
    touched: set[str] = set()   # files patched earlier in THIS run: they are dirty because of us, not because of someone else
    applied = refused = declined = 0
    for p in approved:
        print(f"\n{p['id']}  {p['failed_locator']}  ->  {p['suggestion']}", file=out)
        try:
            plan = plan_patch(p["failed_locator"], p["suggestion"], _roots(args), repo)
            if not args.allow_dirty and plan.file not in touched:
                check_clean(plan.file, repo)
        except PatchRefused as e:
            refused += 1
            print(f"  REFUSED ({e.code}): {e}", file=out)
            continue
        print(plan.diff.rstrip(), file=out)
        if p["strategy"] == "css":
            print("  note: a css locator is non-semantic; tests/test_locator_quality.py will need an ACCEPTED entry with a reason.", file=out)
        if args.dry_run:
            print("  dry run: not applied", file=out)
            continue
        if not args.yes:
            if not isatty:
                print("  not applied: no terminal to confirm on; re-run with --yes", file=out)
                declined += 1
                continue
            if input_fn("  Apply this change? [y/N] ").strip().lower() != "y":
                print("  skipped", file=out)
                declined += 1
                continue
        apply_plan(plan, repo)
        touched.add(plan.file)
        p.update(status="applied", applied_at=rv.now(), applied_diff=plan.diff)
        rv.save_review(review, review_path)
        applied += 1
        print(f"  applied to {plan.file}:{plan.line}", file=out)
    print(f"\n{applied} applied, {refused} refused, {declined} not confirmed" + (" (dry run)" if args.dry_run else ""), file=out)
    if applied:
        print("next: git diff; uv run pytest tests/test_locator_quality.py and the tests that healed; then commit.", file=out)
    return 1 if refused else 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m framework.healing", description="Review and apply self-healing proposals.")
    ap.add_argument("--events", help=f"healing events from `pytest --heal` (default {DEFAULT_EVENTS}, env HEAL_REPORT)")
    ap.add_argument("--review", help=f"review file with decisions (default {DEFAULT_REVIEW}, env HEAL_REVIEW)")
    ap.add_argument("--roots", action="append", metavar="DIR",
                    help=f"source folder to search and patch; repeat for several (default {' '.join(DEFAULT_ROOTS)})")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="merge events into the review file and write the markdown/html report")
    r.add_argument("--format", choices=["md", "html", "both"], default="both")
    r.add_argument("--out-dir")
    sub.add_parser("list", help="list proposals with their status and score")
    a = sub.add_parser("approve", help="mark proposals approved (ids may be unique prefixes)")
    a.add_argument("ids", nargs="*")
    a.add_argument("--all", action="store_true", help="every proposed one that is verified, has ONE source definition and score >= --min-score")
    a.add_argument("--min-score", type=float, default=0.8)
    a.add_argument("--note")
    j = sub.add_parser("reject", help="mark proposals rejected")
    j.add_argument("ids", nargs="+")
    j.add_argument("--note")
    p = sub.add_parser("apply", help="patch the approved proposals in source (shows each diff first)")
    p.add_argument("--dry-run", action="store_true", help="show the diffs, change nothing")
    p.add_argument("--yes", action="store_true", help="apply without the interactive confirmation")
    p.add_argument("--allow-dirty", action="store_true", help="patch files that have uncommitted changes (not recommended)")
    return ap


def main(argv=None, out=None, input_fn=input, isatty=None) -> int:
    out = out or sys.stdout
    args = build_parser().parse_args(argv)
    if args.cmd == "report":
        return cmd_report(args, out)
    if args.cmd == "list":
        return cmd_list(args, out)
    if args.cmd == "approve":
        return cmd_decide(args, out, "approved")
    if args.cmd == "reject":
        return cmd_decide(args, out, "rejected")
    return cmd_apply(args, out, input_fn, isatty)


if __name__ == "__main__":
    raise SystemExit(main())
