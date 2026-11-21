# Day 23: AI bug report and triage helper

Branch `day-23-bug-reports`, issue #27. Code: `ai_testgen/bug_report.py` (draft, check, render), `ai_testgen/duplicates.py` (fingerprint and embedding index), scripts
`draft_bug_reports`, `dedupe_eval`, `triage_eval`. Outputs in `reports/bugs/` (11 reports as `.md` and `.json`, `summary.json`, `index.json`, the evaluations, and
`inputs/` with copies of the 11 saved failures so a run can be repeated). `reports/bugs/strict/` is the second prompt's run.

## What it does
From a saved failure (error, locator, page text, the test's source) the model writes a bug report: title, triage, severity, steps, expected, actual, evidence, suspected cause,
next action. **Every evidence quote is checked against the failure**; an invented one is sent back once and, if still invented, dropped and listed in the report. The model is a text model:
it is given the page's accessibility text, not the screenshot, and each report says so. A drafted report is then compared with the earlier ones to flag duplicates.

## Run on 11 saved failures (llama3.1:8b, about 5.5 s per draft)
Ground truth (`reports/bugs/ground_truth.json`) was written by hand **before** any draft existed: which class(es) I accept for each failure and which failures share a root cause
(6 duplicate pairs among 55).
- **Drafting:** 11 of 11 valid reports; 10 on the first attempt, one needed three and had an invented quote dropped (`unexpected value 'Transfer Complete!'`).
  The classification came out the same on a second identical run.
- **Triage: 6 of 11 right** (never "unclear"). It calls `app_bug` whenever a check fails: three stale-locator failures and two wrong-expectation failures were called app bugs or
  "environment". With a second prompt that says to be strict about `app_bug` and to choose `unclear` when the facts cannot tell: **7 of 11**, still never "unclear", and one test that was
  right before became wrong. That prompt was written after seeing the first result and scored on the same 11, so 7/11 is the optimistic figure and the gain is within what one flipped answer
  explains. **The prompt is not the lever:** whether a failed text check is a test mistake or a page mistake depends on the requirement, which the model is not given.
- **Quality of the text:** the structure is good and the steps are usable. The wording over-claims: the empty-form report calls a payment sent from a rejected form "a critical security
  vulnerability" next to a severity of "major". Triage and severity are labelled as a draft in every report.

## Duplicates: what worked and what did not
| Method | AUC | Best threshold (fitted on the same 11) | At my first guess of 0.85 |
|---|---|---|---|
| Embedding of title, expected, actual (nomic-embed-text) | 0.93 | 0.74: precision 0.80, recall 0.67 | **found none of 6** |
| Same, actual only | 0.85 | 0.67: precision 0.45, recall 0.83 | none |
| Same, with the `clustering:` prefix | 0.88 | 0.84: precision 0.75, recall 0.50 | 1 of 6 |
| Fingerprint (kind, locator, shape of the message), exact match | 1.00 | no threshold needed: 6 of 6, 0 wrong | n/a |

- **Embeddings rank well and still cannot decide.** True duplicates scored 0.68 to 0.83 and the best look-alike that was *not* a duplicate scored 0.77: a rejected-form report and a stale-locator report, both
  called app bugs and both about amounts, read almost the same and are different defects. Any threshold trades one error for the other.
- **What I shipped is both signals, with different promises.** Equal fingerprints: "same failure, probably a duplicate". Embedding at or above 0.75 (precision 0.75, recall 0.5 on this
  data): "similar, worth a look, not proof". Nothing is merged or closed.
- **The fingerprint was written after I had seen these 11, so its 6 of 6 is optimistic.** As a sanity check I ran it over all 48 saved failures and read the groups it makes (39 distinct fingerprints;
  five groups of two to five). All five are plausibly one cause each, for instance five tests waiting for the same stale `#amt` locator. That is reading, not scoring.
- **The default threshold I would have shipped was useless.** 0.85 is a common number; here it found nothing. The threshold has to be measured on the reports of the project.

## Limits
- 11 failures, one model, my own ground truth and my own fingerprint design. The duplicate groups come from two situations: a mutation run (rejected forms that still post) and an older
  state of the page object (`#amt`). Real failures of a live project will be messier.
- The model never saw a screenshot and was not given the requirement, which is exactly what triage needs. Giving it the user story the test came from is the next thing to try.
- `unclear` is the right answer for several of these and the model never gives it, which is worth knowing before anyone routes bugs automatically by its triage.
