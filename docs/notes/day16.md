# Day 16: healing review report and apply CLI

## Flow
```
uv run pytest --heal                       -> reports/healing.json         (events; nothing edited)
python -m framework.healing report         -> reports/healing_review.json  (proposals + decisions, persists)
                                              reports/healing_review.md / .html  (what a reviewer reads)
python -m framework.healing approve <id>   -> status approved   (or: reject <id> --note ...)
python -m framework.healing apply          -> shows each diff, asks to confirm, patches the source, status applied
```
Code: `framework/healing/review.py` (proposals, score, decisions, reports), `patching.py` (plan and apply a one-line fix), `__main__.py` (CLI). A worked example of the report: `docs/examples/healing_review.md` (and `.html`).

## Design
- **One proposal per distinct fix**: the same old -> new locator healed in 3 tests is one row ("tests affected: 3"), keyed by a short id (`74be18c8`; a unique prefix is enough on the command line).
- **Status** `proposed -> approved | rejected -> applied`. Re-running `report` refreshes facts but never touches a decision or an applied patch (tested).
- **Each proposal shows**: old and new locator, why (the model's reason), where the old one is defined in source (searched fresh at report time), the element it resolved to, tests affected, flags, the score with its parts, and the **exact diff `apply` would make** (or why it would refuse).
- **Confidence score**: 0..1 from visible components (retry verified, first attempt, semantic locator, exactly one source definition, repeated across tests, harness repair penalty, and the model's own confidence at a tiny weight). It is a heuristic ordering aid and **not calibrated**: there is no observed wrong heal in the real runs to calibrate against. In practice it saturates: a verified, first-attempt, single-definition fix scores 0.99 to 1.0 whatever the strategy, and the lower scores come from missing definitions or repairs. **The flags and the diff are the real review signal; the score just orders the list.**

## Safety rules of `apply` (agreed at the start of the day, enforced and tested)
| Rule | Behaviour |
|---|---|
| Only approved | `proposed` and `rejected` are never touched; with nothing approved it says so |
| Human confirms | shows the diff, then asks `[y/N]`; without a terminal it refuses unless `--yes`; `--dry-run` shows diffs and writes nothing |
| One unique literal match | the old locator must appear exactly once in the source as literal text (quote style preserved); 0 matches (built from an f-string, or defined elsewhere), several matches, or twice on one line: **refused with a reason**, left `approved` for a human |
| Valid result | the patched file must still parse |
| Clean files only | a file with uncommitted changes is refused (`--allow-dirty` overrides); files this same run already patched are exempt, so two fixes in one file work |
| Never commits, never runs tests | prints `next: git diff; run tests/test_locator_quality.py and the tests that healed; commit` |
| Writes atomically | temp file + rename; no partial file |

## End to end on a real broken test (real model, real ParaBank)
Setup: on a throwaway branch I committed a stale locator in the real `TransferPage` (`#amount` -> `#amt`; `apply` refuses uncommitted files, so the breakage had to be committed).
1. `pytest tests/test_transfer_edge_cases.py` without `--heal`: the broken locator fails the decimal test, **and the two strict-xfail tests still show "expected failure"**: they were hiding it (see findings).
2. Same with `--heal`: 2 passed, 2 xfailed, 3 `HealedLocatorWarning`s pointing at `framework/pages/transfer_page.py:13`; the three heals collapsed into **one proposal** (score 1.00).
3. `apply --yes` before approving: "nothing to apply". `approve 74be18c8`. `apply` with no terminal: "re-run with --yes", file untouched. `apply --yes`: diff shown, patched, status `applied`.
4. Result: `git diff main` on the file is **empty** (the patch restored the original locator), the tests pass **without** `--heal` (2 passed, 2 xfailed), `list` shows `applied`. Throwaway branch deleted.

## Findings
1. **`xfail` hides unrelated failures.** My Day 11 strict-xfail tests (documenting ParaBank bugs) accepted *any* failure, including a stale locator. Now `raises=AssertionError`; with the locator broken they fail (3 failed) instead of passing as "expected". A regression test of this kind should name the failure it expects.
2. **CLI bug found by the tests:** `--roots` took `nargs="+"`, so `--roots pages report` swallowed `report` as a second folder and the subcommand vanished (all 14 CLI tests failed at once). A flag placed before a subcommand must take exactly one value: it is now repeatable (`--roots a --roots b`).
3. Healing at run time proposes; **how well the proposal survives review is a human question**: the report shows the resolved element and the diff, but a reviewer must still confirm it is the intended element (the heal only proves the action worked).
4. Several heals of one broken locator across tests are common (3 tests here), so grouping into one proposal is what keeps a review short.

## Limits
- `apply` only handles a locator that is **literal, on one line, defined once** in the searched roots (`framework/pages` by default; `--roots` to add). Locators built from f-strings (the registration fields), or chains whose source text differs from Playwright's log (`get_by_role(...).filter(has=self.page...)`), are refused: change them by hand.
- A `css` fix usually needs a matching `ACCEPTED` entry (with a reason) in `tests/test_locator_quality.py`; `apply` warns, it does not edit tests.
- Decisions live in `reports/healing_review.json`, which is git-ignored (a local working file); the committed `docs/examples/` copy is only an illustration.
- Score caveats above; one model; samples are small and synthetic.
