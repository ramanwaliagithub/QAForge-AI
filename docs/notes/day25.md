# Day 25: Why LLM testing is different

Branch `day-25-llm-service`, issue #31. Code: `rag_app/` (the service), `tests/llm_service/` (the five plain checks), `scripts/probe_llm_service.py`, `scripts/llm_service_mutants.py`.
Evidence: `reports/day25/probe.json`, `reports/day25/mutants.json`. Quality dimensions: `docs/llm-quality-dimensions.md`.

## The target
A small help-center assistant: `POST /ask` retrieves the 3 closest of 9 passages (nomic-embed-text), then asks llama3.1:8b to answer only from them or say "I don't know based on the help center."
The passages were written from the live ParaBank pages (the $515.50 first account, the $100.00 minimum, the search options, the form fields). Temperature 0.7, a normal application default.
Ordinary on purpose; `create_app` takes the model client, so 15 tests of its plumbing run with a scripted model.

## Why it is different to test (from running it, not from the textbook)
- **The same question gets different words every time.** 8 answerable questions asked 5 times each gave 28 different answers in 40 calls. `assert answer == expected` cannot work, and a single run proves little.
- **Correct is a judgement, not a value.** "You need at least $100.00" and "A minimum of $100.00 must be deposited..." are both right. My own first checker also judged wrongly: it accepted "I don't know" as the right answer to
  "can I change my username there?" because the pattern matched "don't". The model really did refuse that question 5 of 5 times when the answer is in the knowledge base; I only found out when I read the answers.
- **Quality has several independent dimensions** (correctness, faithfulness, safety, consistency: `docs/llm-quality-dimensions.md`), and a change can hurt one and leave the others alone.
- **There is no stack trace.** A wrong answer is a well-formed, fast, 200-status answer.

## The five plain checks, and why they are not enough
The checks anyone writes first: status 200, response schema with known passage ids, latency under 20 s, non-empty answer under 600 characters, empty question refused (422). All pass (`uv run pytest -m eval`).
Then I broke the service seven ways, as I did for the Bill Pay tests on Day 19 (13 questions, 3 repeats each, 39 calls per variant):

| Injected defect | Plain checks | Correct answers (baseline 36/39) | Cited the right passage (baseline 24/24) |
|---|---|---|---|
| Retrieval returns the worst passages | 39/39 passed | **15/39** | **0/24** |
| Prompt no longer says "only the passages" | 39/39 passed | **24/39**: 0 of 15 unanswerable or adversarial questions refused | 24/24 |
| A stale fact in the knowledge base ($50 minimum) | 39/39 passed | **29/39** | 24/24 |
| No passages in the prompt | 39/39 passed | **12/39** | 24/24 |
| Model told to always refuse | 39/39 passed | **22/39** (the model ignored the instruction 7 times in 24 answerable calls) | 24/24 |
| Citations point at the neighbouring passage | 39/39 passed | 36/39 (not noticed) | **15/24** |
| Temperature 1.8 | 39/39 passed | 36/39 (**not noticed by anything**) | 24/24 |

- **The five plain checks noticed 0 of 7.** The substring fact check noticed 5; the citation check the sixth. The seventh, a very high temperature, was invisible to every check I have: at 1.8 this model on this small knowledge base still
  answered correctly. That is a consistency question, which needs repeated sampling and a spread measure (Day 32), not a threshold on one answer.
- **A weak mutant is a finding about the mutant.** My first "always refuses" variant (an instruction appended at the end of the prompt) did nothing: the model answered anyway and scored 39/39. I moved the instruction to the start and repeated it at the end; it now has a partial effect.
- **The baseline is not clean.** 3 of 39 baseline answers are the username refusals; every comparison above is against 36/39, not 39/39.

## What I changed after seeing results (and so what is tuned)
The username pattern (it accepted a refusal), the "always refuses" mutant (it had no effect), and the addition of the citation check (the first run had no way to see wrong citations). The first 65-call probe, before the regex fix,
reported 65/65 correct; with the corrected check the same questions are 60/65. Only the corrected run is committed (the rerun overwrote the first output file); the first figures are quoted from the console.

## Limits
One model, one app, nine passages, three or five repeats. The fact check is a substring match, not a judgement, and the mutants and questions are mine. This is a motivating experiment, not a benchmark: Days 26 to 36 replace each crude piece with a
proper one (a golden dataset, deterministic checks, a judge, thresholds).
