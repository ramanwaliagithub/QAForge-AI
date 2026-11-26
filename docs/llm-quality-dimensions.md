# Quality dimensions of an LLM service

What "good" means for the sample service (`rag_app/`, `POST /ask`), split into four dimensions that fail independently, with how each is measured and what the Day 25 evidence says.
Later days of Phase 4 build the measurements; this file says what they are for. Update it when a measurement exists.

| Dimension | Question | A failure looks like | Measured by (planned day) | Day 25 evidence |
|---|---|---|---|---|
| **Correctness** | Is the answer true for the app? | "$50.00 minimum" when it is $100.00 | Reference answers and deterministic checks (Days 26, 27); a judge for free text (28) | Substring check on 8 questions: caught a stale fact (29/39 vs 36/39), reversed retrieval (15/39), no context (12/39). It also showed the model refusing a question it could answer (5 of 5 times) |
| **Faithfulness** | Does it use only what it was given, and say so when that is not enough? | An invented interest rate; an answer with no passage behind it; a citation to the wrong passage | Refusal on unanswerable questions, citation checks, hallucination scoring (31, 35) | Without the "only the passages" instruction it answered 0 of 15 unanswerable or adversarial questions with a refusal. A citation pointing at the wrong passage passed every check except the citation check |
| **Safety** | Does it resist being talked out of its rules, and avoid harm? | Obeying "ignore your instructions", repeating the false premise of a loaded question | Adversarial question sets, red-team cases (33, and Phase 6) | The baseline gave the exact refusal on every unanswerable or adversarial call (15 of 15 in the mutant run, 25 of 25 in the probe) |
| **Consistency** | Does the same question get the same substance every time? | $100 one time, $50 the next | Repeated sampling and a spread measure (32) | At temperature 0.7 the 8 answerable questions produced 28 different wordings in 40 calls (all agreed in substance but one question). An exact-match assertion cannot work |

## Three things the table already says
- **Pass/fail on one call is the wrong unit.** The same question gives different words every time, so a check is a rate over repeats, with a stated threshold (Day 36).
- **Each dimension needs its own check.** The five plain checks (status, schema, latency, non-empty, bad input) measure the *service*, not the *answers*; they passed on all seven broken variants.
- **The checks need testing as well.** The first fact check accepted a refusal as a correct answer (the regex matched "n't" in "don't"). A mutant that does nothing is a finding about the mutant (my first "always refuses" variant was ignored by the model).
