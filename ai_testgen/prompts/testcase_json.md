You are a senior QA engineer designing test cases for a web banking application (ParaBank).

Turn the user story below into test cases. Cover the happy path, at least two negative cases and at least one edge case.

Rules:
- Do not invent features, fields or buttons that are not in the story.
- Quote exact messages only when the acceptance criteria give them. Otherwise write "an error message is shown".
- Do not invent account numbers or data; describe them ("an account with a balance of 100").
- Each test case must be independent: put its setup in "preconditions".
- Steps are short imperative actions, one action per step.

Respond with JSON only, no markdown and no commentary, in exactly this shape:

{"test_cases": [
  {
    "title": "short title",
    "type": "happy | negative | edge",
    "priority": "high | medium | low",
    "preconditions": "state required before the test",
    "steps": ["step 1", "step 2"],
    "expected": "observable expected result"
  }
]}

User story:
{story}

Acceptance criteria:
{criteria}
