# Day 24: Phase 3 consolidation

Branch `day-24-consolidation`, issue #29. Tag `v0.3-workflow` on the merge commit.

## What I did
- **The playbook, `docs/ai-dev-workflow.md`.** Written last, from what Days 18 to 23 measured rather than from what I expected: the loop (probe, spec, measured checks, review, gates), what I
  delegate, what I keep, what to distrust, what is automated, and three open questions. Every claim points at a day's notes; where there was one run, it says one run.
- **Refactored what had become messy** (it had piled up in the last week):
  - Seven test files each defined their own scripted model client, slightly different each time. They now use one `ScriptedClient` in `framework/llm_client.py`, with its own tests
    (98 tests across those files pass unchanged).
  - Four scripts each parsed `--name=value` flags by hand. They share `scripts/flags.py`.
  - **`--help` now prints the usage.** I ran `draft_bug_reports --help` to see its options and it ran the whole pipeline, deleting a committed index file (restored from git before anything
    else happened). A script that rewrites reports must not start by accident, so the parser takes the usage text and exits on `--help`; this is tested.
  - `scripts/` is now a package: mypy saw `scripts/flags.py` under two module names.
- **An architecture diagram in the README** (Mermaid), with real folder and file names in the boxes. A test (`tests/test_readme_architecture.py`) fails when one of them stops existing;
  I renamed one on purpose to see it fail.
- **Closed Phase 3**: tag `v0.3-workflow`.

## State of the suite
695 passed, 1 skipped, 3 xfailed, serial and `-n 3`, reruns off. ParaBank was down at the start of the session (the container runtime had stopped over the break): 10 failures and 18 errors
until it was started again, which is the reason D1 says to run the suite against the live app.

## What I would not claim
- The playbook is one person's conclusions from small experiments on one app with one model. It is a starting point for Phase 4, which tests the same questions with proper sample sizes.
- The diagram is checked for names, not for arrows: a wrong arrow would pass the test.
