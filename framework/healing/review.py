"""Turn the run-time heal events into reviewable proposals, with a score, a status and a report.

Workflow:  pytest --heal  ->  reports/healing.json (events)
           `healing report`  ->  merge into reports/healing_review.json (+ .md / .html), decisions are kept
           `healing approve|reject ID`  ->  record the human decision
           `healing apply`  ->  patch approved, patchable proposals (see patching.py)
"""
import hashlib
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from framework.healing.patching import DEFAULT_ROOTS, PatchRefused, locate, plan_patch
from framework.locator_audit import classify_css

SCHEMA = 1
STATUSES = ("proposed", "approved", "rejected", "applied")
# fields a human or `apply` owns: a re-run of `report` must never overwrite them
DECISION_FIELDS = ("status", "note", "decided_at", "applied_at", "applied_diff")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def proposal_id(failed: str, suggestion: str) -> str:
    return hashlib.sha1(f"{failed}->{suggestion}".encode()).hexdigest()[:8]


def risk_flags(p: dict) -> list[str]:
    flags = []
    defs = p["definitions"]
    if not defs:
        flags.append("no_source_definition: cannot be applied automatically (built at run time or defined elsewhere)")
    elif len(defs) > 1:
        flags.append(f"ambiguous_definition: {len(defs)} source lines contain the old locator; apply will refuse")
    if p["strategy"] == "css":
        flags.append("non_semantic_locator: css; tests/test_locator_quality.py will need an ACCEPTED entry with a reason")
    if p["model_confidence"] is not None and p["model_confidence"] < 0.5:
        flags.append(f"low_model_confidence: {p['model_confidence']}")
    if p["repaired"]:
        flags.append("repaired_by_harness: the model's selector was mechanically corrected (dotted id)")
    if not p["verified"]:
        flags.append("not_verified: a retry with this locator did not succeed in every test")
    return flags


def score_proposal(p: dict) -> tuple[float, dict]:
    """A transparent 0..1 ordering aid, NOT a calibrated probability: no wrong heal has been observed yet in the real
    runs, so there is nothing to calibrate against. Each component is shown in the report."""
    parts = {"base": 0.5}
    parts["retry_verified"] = 0.2 if p["verified"] else -0.3                 # the action really worked with it
    parts["first_attempt"] = 0.1 if p["attempts_min"] <= 1 else 0.0           # no rejections needed
    parts["semantic_locator"] = 0.1 if p["strategy"] in ("role", "label") else (0.05 if p["strategy"] == "css" else 0.0)
    parts["one_source_definition"] = 0.1 if len(p["definitions"]) == 1 else 0.0  # actionable and unambiguous
    parts["repeated_across_tests"] = round(min(0.1, 0.05 * (p["count"] - 1)), 2)  # the same fix proposed more than once
    parts["harness_repair"] = -0.1 if p["repaired"] else 0.0
    if p["model_confidence"] is not None:
        parts["model_self_report"] = round((p["model_confidence"] - 0.5) * 0.1, 3)  # barely trusted: models over-claim
    return round(max(0.0, min(1.0, sum(parts.values()))), 2), parts


def build_proposals(events: list[dict], roots=DEFAULT_ROOTS, repo_root: Path | None = None) -> list[dict]:
    """One proposal per distinct (old locator -> new locator). Only verified heals are proposals; skips and failures are
    not (they are summarised in the report instead)."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for e in events:
        if e.get("outcome") in ("healed", "retry_failed") and e.get("suggestion") and e.get("failed_locator"):
            groups[(e["failed_locator"], e["suggestion"])].append(e)
    proposals = []
    for (failed, suggestion), evs in groups.items():
        first = evs[0]
        p = {
            "id": proposal_id(failed, suggestion), "failed_locator": failed, "suggestion": suggestion,
            "actions": sorted({e["action"] for e in evs}), "count": len(evs),
            "tests": sorted({e["test_id"] for e in evs}),
            "strategy": first.get("strategy"), "reason": first.get("reason", ""), "element": first.get("element"),
            "model_confidence": first.get("confidence"), "attempts_min": min(e.get("attempts", 0) or 1 for e in evs),
            "verified": all(e.get("verified") for e in evs), "repaired": any(e.get("repaired_from") for e in evs),
            "definitions": [{k: h[k] for k in ("file", "line", "text")} for h in locate(failed, roots, repo_root)],
        }
        p["flags"] = risk_flags(p)
        p["score"], p["score_breakdown"] = score_proposal(p)
        p.update(status="proposed", note="", decided_at=None, applied_at=None, applied_diff=None)
        proposals.append(p)
    return sorted(proposals, key=lambda p: (-p["score"], p["id"]))


def empty_review() -> dict:
    return {"schema": SCHEMA, "updated_at": now(), "proposals": []}


def load_review(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return empty_review()
    data = json.loads(path.read_text())
    if data.get("schema") != SCHEMA:
        raise ValueError(f"Unsupported review schema {data.get('schema')!r} in {path}")
    return data


def save_review(review: dict, path: Path) -> None:
    review["updated_at"] = now()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(review, indent=2) + "\n")


def merge_review(review: dict, proposals: list[dict]) -> dict:
    """Add new proposals, refresh the facts of known ones, and NEVER touch a human decision or an applied patch."""
    known = {p["id"]: p for p in review["proposals"]}
    for new in proposals:
        old = known.get(new["id"])
        if old is None:
            known[new["id"]] = new
        elif old["status"] != "applied":  # an applied proposal is history: leave it exactly as it was
            known[new["id"]] = {**new, **{k: old[k] for k in DECISION_FIELDS}}
    review["proposals"] = sorted(known.values(), key=lambda p: (-p["score"], p["id"]))
    return review


def decide(review: dict, ids: list[str], status: str, note: str = "") -> list[dict]:
    """Approve or reject proposals by id (a unique prefix is enough). Applied proposals cannot be re-decided."""
    if status not in ("approved", "rejected"):
        raise ValueError(f"cannot set status {status!r}")
    changed = []
    for pid in ids:
        matches = [p for p in review["proposals"] if p["id"].startswith(pid)]
        if len(matches) != 1:
            raise KeyError(f"{pid!r} matches {len(matches)} proposals")
        p = matches[0]
        if p["status"] == "applied":
            raise ValueError(f"{p['id']} is already applied")
        p.update(status=status, note=note or p["note"], decided_at=now())
        changed.append(p)
    return changed


def patch_preview(p: dict, roots=DEFAULT_ROOTS, repo_root: Path | None = None) -> tuple[str | None, str | None]:
    """(diff, refusal reason) for what `apply` would do right now."""
    try:
        return plan_patch(p["failed_locator"], p["suggestion"], roots, repo_root).diff, None
    except PatchRefused as e:
        return None, f"{e.code}: {e}"


def summary_counts(review: dict) -> dict:
    out = {s: 0 for s in STATUSES}
    for p in review["proposals"]:
        out[p["status"]] += 1
    return out


def render_markdown(review: dict, events: list[dict] | None = None, roots=DEFAULT_ROOTS, repo_root: Path | None = None) -> str:
    c = summary_counts(review)
    out = ["# Healing review", "",
           f"Updated {review['updated_at']}. {len(review['proposals'])} proposals: " + ", ".join(f"{v} {k}" for k, v in c.items()) + ".", "",
           "Each proposal is a locator that failed at run time and was replaced, in memory only, by an LLM suggestion that "
           "worked when the step was retried. **No source file has been changed.** The score is a transparent heuristic "
           "(components shown), not a probability. Approve with `python -m framework.healing approve <id>`, then "
           "`python -m framework.healing apply`.", ""]
    if events:
        skipped = [e for e in events if e.get("outcome") not in ("healed", "retry_failed", None)]
        if skipped:
            by = defaultdict(int)
            for e in skipped:
                by[e["outcome"]] += 1
            out += ["Not proposals (nothing to review): " + ", ".join(f"{n}x {k}" for k, n in sorted(by.items())) + ".", ""]
    for i, p in enumerate(review["proposals"], start=1):
        diff, refusal = patch_preview(p, roots, repo_root) if p["status"] != "applied" else (p.get("applied_diff"), None)
        out += [f"## {i}. `{p['id']}`  {p['status'].upper()}  score {p['score']:.2f}", "",
                f"- **Old:** `{p['failed_locator']}`", f"- **New:** `{p['suggestion']}`  ({p['strategy']}; {', '.join(p['actions'])})",
                f"- **Why (model):** {p['reason'] or 'n/a'}  (self-reported confidence {p['model_confidence']})"]
        if p["definitions"]:
            d = p["definitions"][0]
            out.append(f"- **Defined at:** `{d['file']}:{d['line']}`  `{d['text']}`" + (f"  (+{len(p['definitions']) - 1} more)" if len(p["definitions"]) > 1 else ""))
        else:
            out.append("- **Defined at:** not found as literal source text")
        if p["element"]:
            out.append("- **Resolved element:** " + ", ".join(f"{k}={v!r}" for k, v in p["element"].items() if v))
        out.append(f"- **Tests affected ({p['count']}):** " + ", ".join(f"`{t.split('::')[-1]}`" for t in p["tests"][:6]))
        out.append("- **Score:** " + ", ".join(f"{k} {v:+.2f}" if k != "base" else f"base {v:.2f}" for k, v in p["score_breakdown"].items()))
        for f in p["flags"]:
            out.append(f"- **Flag:** {f}")
        if p["note"]:
            out.append(f"- **Note:** {p['note']}")
        out.append("")
        if diff:
            out += ["```diff", diff.rstrip(), "```", ""]
        elif refusal:
            out += [f"> `apply` would refuse: {refusal}", ""]
    return "\n".join(out)


def render_html(review: dict, events: list[dict] | None = None, roots=DEFAULT_ROOTS, repo_root: Path | None = None) -> str:
    e = html.escape
    c = summary_counts(review)
    rows = []
    for p in review["proposals"]:
        diff, refusal = patch_preview(p, roots, repo_root) if p["status"] != "applied" else (p.get("applied_diff"), None)
        d = p["definitions"][0] if p["definitions"] else None
        flags = "".join(f"<li>{e(f)}</li>" for f in p["flags"]) or "<li>none</li>"
        rows.append(f"""<section class="card {e(p['status'])}">
<h2><code>{e(p['id'])}</code> <span class="badge">{e(p['status'])}</span> <span class="score">score {p['score']:.2f}</span></h2>
<table>
<tr><th>Old</th><td><code>{e(p['failed_locator'])}</code></td></tr>
<tr><th>New</th><td><code>{e(p['suggestion'])}</code> <small>({e(str(p['strategy']))}; {e(', '.join(p['actions']))})</small></td></tr>
<tr><th>Why (model)</th><td>{e(p['reason'] or 'n/a')} <small>(self-reported {e(str(p['model_confidence']))})</small></td></tr>
<tr><th>Defined at</th><td>{f"<code>{e(d['file'])}:{d['line']}</code> <code>{e(d['text'])}</code>" if d else "not found as literal source text"}</td></tr>
<tr><th>Resolved element</th><td>{e(', '.join(f'{k}={v!r}' for k, v in (p['element'] or {}).items() if v))}</td></tr>
<tr><th>Tests ({p['count']})</th><td>{e(', '.join(t.split('::')[-1] for t in p['tests'][:6]))}</td></tr>
<tr><th>Score parts</th><td>{e(', '.join(f'{k} {v:+.2f}' for k, v in p['score_breakdown'].items()))}</td></tr>
<tr><th>Flags</th><td><ul>{flags}</ul></td></tr>
</table>
{f'<pre class="diff">{e(diff)}</pre>' if diff else (f'<p class="refuse">apply would refuse: {e(refusal)}</p>' if refusal else '')}
<p><small>Approve: <code>python -m framework.healing approve {e(p['id'])}</code></small></p>
</section>""")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Healing review</title><style>
body{{font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:960px;padding:16px;color:#1b1f23;background:#fff}}
.card{{border:1px solid #d0d7de;border-radius:8px;padding:12px 16px;margin:16px 0}}.card.approved{{border-color:#1a7f37}}.card.rejected{{border-color:#cf222e;opacity:.7}}.card.applied{{border-color:#8250df}}
table{{border-collapse:collapse;width:100%}}th{{text-align:left;width:130px;vertical-align:top;color:#57606a;font-weight:600}}td,th{{padding:3px 6px}}
code{{background:#f6f8fa;padding:1px 5px;border-radius:4px;font-size:13px}}.badge{{font-size:12px;background:#ddf4ff;border-radius:10px;padding:2px 8px}}.score{{font-size:13px;color:#57606a}}
pre.diff{{background:#f6f8fa;padding:10px;overflow:auto;border-radius:6px;font-size:13px}}.refuse{{color:#cf222e}}
@media(prefers-color-scheme:dark){{body{{background:#0d1117;color:#e6edf3}}.card{{border-color:#30363d}}code,pre.diff{{background:#161b22}}th{{color:#8b949e}}.badge{{background:#1f3a5f}}}}
</style></head><body>
<h1>Healing review</h1>
<p>Updated {e(review['updated_at'])}. {len(review['proposals'])} proposals: {e(', '.join(f'{v} {k}' for k, v in c.items()))}.</p>
<p><strong>No source file has been changed.</strong> The score is a transparent heuristic, not a probability.</p>
{''.join(rows)}</body></html>"""
