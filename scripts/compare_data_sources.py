"""Faker against a model as the source of test data: validity, variety, repeatability, speed, and whether ParaBank takes the people.

    uv run python -m scripts.compare_data_sources [label] [--n=30] [--llm-runs=3] [--register | --register-only]

Writes reports/day22/<label>.json. `--register` registers every identity of the last LLM run and of Faker through the real form and checks
that the welcome line shows the name as given (needs ParaBank up). Numbers come from this machine's local model; they are a measurement,
not a verdict on models in general.
"""
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from framework.data import DataFactory, DataGenerationError, FakerSource, Identity, LLMSource
from framework.llm_client import get_client
from scripts.flags import parse_flags

ROOT = Path(__file__).resolve().parent.parent


def variety(people: list[Identity]) -> dict[str, float]:
    """Share of distinct values per field (1.0 = every person different), plus how many phones/SSNs look made up by a pattern."""
    n = len(people)
    ratios = {
        "first_names": len({p.first_name for p in people}) / n,
        "last_names": len({p.last_name for p in people}) / n,
        "cities": len({p.city for p in people}) / n,
        "states": len({p.state for p in people}) / n,
        "zip_codes": len({p.zip_code for p in people}) / n,
        "streets": len({p.street for p in people}) / n,
        "phone_suffixes": len({p.phone[-4:] for p in people}) / n,
        "ssn_serials": len({p.ssn[-4:] for p in people}) / n,
    }
    ratios["sequential_phones"] = sum(p.phone in "01234567890123456789" for p in people) / n
    return {k: round(v, 2) for k, v in ratios.items()}


def faker_row(n: int) -> dict[str, Any]:
    """Measure Faker: variety, time, and whether the same seed repeats."""
    start = time.perf_counter()
    people = FakerSource(1).identities(n)
    seconds = time.perf_counter() - start
    return {"source": "faker", "n": n, "valid_on_first_sight": 1.0, "seconds": round(seconds, 3), "variety": variety(people),
            "same_seed_same_people": FakerSource(1).identities(n) == people, "people": [p.model_dump() for p in people]}


def llm_rows(n: int, runs: int) -> list[dict[str, Any]]:
    """Measure the model `runs` times: what fraction of its items passed the rules untouched, time, variety, and failures."""
    rows = []
    for run in range(runs):
        source = LLMSource(get_client(), temperature=0.7, max_attempts=6)
        start = time.perf_counter()
        try:
            people = source.identities(n)
            error = None
        except DataGenerationError as e:
            people, error = [], str(e)
        returned = source.stats.items_returned
        rejected = sum(source.stats.rejected.values())
        rows.append({
            "source": "llm", "run": run + 1, "n": n, "got": len(people), "error": error, "calls": source.stats.calls,
            "items_returned": returned, "rejected": dict(source.stats.rejected), "duplicates": source.stats.duplicates,
            "valid_on_first_sight": round((returned - rejected) / returned, 2) if returned else 0,
            "seconds": round(time.perf_counter() - start, 1), "variety": variety(people) if people else None,
            "people": [p.model_dump() for p in people],
        })
        print(f"llm run {run + 1}: {len(people)}/{n} in {rows[-1]['seconds']}s, {source.stats.calls} calls, rejected {dict(source.stats.rejected)}", flush=True)
    return rows


def overlap(a: list[dict], b: list[dict]) -> float:
    """Share of the people in `a` (by full name) that also appear in `b`: 1.0 means the two runs gave the same people."""
    names_b = {(p["first_name"], p["last_name"]) for p in b}
    return round(sum((p["first_name"], p["last_name"]) in names_b for p in a) / len(a), 2) if a else 0.0


def register_all(people: list[Identity], label: str) -> dict[str, Any]:
    """Register each identity through the real form (fresh browser context each) and compare the welcome line with the name given."""
    from playwright.sync_api import sync_playwright

    from framework.pages import RegisterPage

    base = os.getenv("BASE_URL", "http://localhost:8080/parabank")
    factory = DataFactory()
    accepted, shown_wrong, failed = 0, [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for person in people:
            customer = factory.customers(1)[0].model_copy(update=person.model_dump())
            context = browser.new_context()
            context.set_default_timeout(15000)
            page = context.new_page()
            try:
                RegisterPage(page, base).open().register(**customer.register_kwargs())
                page.get_by_role("link", name="Log Out").wait_for()
                welcome = page.locator("body").inner_text()
                accepted += 1
                if f"Welcome {person.first_name} {person.last_name}" not in welcome:
                    shown_wrong.append({"given": f"{person.first_name} {person.last_name}", "page": next((line for line in welcome.splitlines() if line.startswith("Welcome")), "")})
            except Exception as error:  # a timeout or a rejected form: record it, keep going
                failed.append({"person": f"{person.first_name} {person.last_name}", "error": str(error).splitlines()[0][:120]})
            finally:
                context.close()
        browser.close()
    return {"source": label, "tried": len(people), "accepted": accepted, "name_not_shown_as_given": shown_wrong, "failed": failed}


def main(argv: list[str]) -> None:
    """Run the comparison and write the report."""
    load_dotenv()
    flags, positional = parse_flags(argv, __doc__)
    label = positional[0] if positional else "comparison"
    n, runs = int(flags.get("--n", 30)), int(flags.get("--llm-runs", 3))
    faker = faker_row(n)
    out = ROOT / "reports" / "day22"
    if "--register-only" in flags:  # redo only the registration part of an existing report, from the saved LLM people
        existing = json.loads((out / f"{label}.json").read_text())
        saved = [Identity(**p) for p in json.loads((out / f"{label}-llm-people.json").read_text())]
        existing["registration"] = [register_all([Identity(**p) for p in faker["people"]], "faker"), register_all(saved, "llm")]
        (out / f"{label}.json").write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(existing["registration"], indent=1, ensure_ascii=False))
        return
    llm = llm_rows(n, runs)
    good = [r for r in llm if r["got"] == n]
    report: dict[str, Any] = {
        "model": os.getenv("OLLAMA_MODEL", "llama3.1:8b"), "n": n, "faker": {k: v for k, v in faker.items() if k != "people"},
        "llm_runs": [{k: v for k, v in r.items() if k != "people"} for r in llm],
        "llm_median_seconds": statistics.median(r["seconds"] for r in llm),
        "llm_run_to_run_overlap": overlap(llm[0]["people"], llm[1]["people"]) if len(llm) > 1 else None,
        "llm_complete_runs": len(good),
    }
    if "--register" in flags:
        report["registration"] = [register_all([Identity(**p) for p in faker["people"]], "faker")]
        if good:
            report["registration"].append(register_all([Identity(**p) for p in good[-1]["people"]], "llm"))
        print(json.dumps(report["registration"], indent=1)[:1500])
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{label}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if good:
        (out / f"{label}-llm-people.json").write_text(json.dumps(good[-1]["people"], indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "registration"}, indent=1)[:2500])


if __name__ == "__main__":
    main(sys.argv[1:])
    sys.exit(0)
