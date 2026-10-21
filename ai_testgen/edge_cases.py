"""Edge cases for a form, proposed by an LLM from the real page snapshot, then checked against the app."""
import json
import re

from pydantic import BaseModel, Field, ValidationError

from framework.llm_client import LLMClient

PROMPT = """You are a QA engineer doing exploratory testing of the Transfer Funds page of a web banking app.

Page snapshot (what the page really contains):
{snapshot}

The logged-in customer has exactly two accounts: index 0 and index 1. The form has an amount field, a "from" account
dropdown, a "to" account dropdown and a Transfer button.

Propose exactly {n} edge cases that are most likely to expose bugs. Each must be something you can do with only those
controls. Respond with JSON only, in this shape:
{{"edge_cases": [{{"title": "short title", "amount": "text typed into the amount field ('' for empty)",
"from_index": 0, "to_index": 1, "expected": "what a correct banking app should do (say whether the transfer is accepted or rejected)"}}]}}
"""


class EdgeCase(BaseModel):
    title: str = Field(min_length=3)
    amount: str
    from_index: int = Field(ge=0, le=1)
    to_index: int = Field(ge=0, le=1)
    expected: str = Field(min_length=3)


class EdgeCaseError(ValueError):
    pass


def parse_edge_cases(text: str) -> list[EdgeCase]:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise EdgeCaseError("No JSON object in the response.")
    try:
        data = json.loads(text[start : end + 1])
        items = data["edge_cases"] if isinstance(data, dict) else data
        cases = [EdgeCase.model_validate(i) for i in items]
    except (json.JSONDecodeError, KeyError, TypeError, ValidationError) as e:
        raise EdgeCaseError(f"Invalid edge case JSON: {e}") from e
    if not cases:
        raise EdgeCaseError("Empty edge case list.")
    return cases


def propose_edge_cases(client: LLMClient, snapshot: str, n: int = 5, max_retries: int = 2) -> list[EdgeCase]:
    prompt = PROMPT.format(snapshot=snapshot, n=n)
    last = None
    for _ in range(max_retries + 1):
        reply = client.generate(prompt, temperature=0.0, json_mode=True, num_ctx=8192).text
        try:
            return parse_edge_cases(reply)[:n]
        except EdgeCaseError as e:
            last = e
            prompt += f"\n\nYour previous answer was rejected: {e}\nReturn corrected JSON only."
    raise EdgeCaseError(f"No valid edge cases: {last}")


_REJECT = re.compile(r"reject|error|invalid|not (?:be )?(?:allowed|accepted|permitted)|fail|prevent|disallow|refus|deny|denied", re.I)


def expects_rejection(expected: str) -> bool:
    """Did the model say the app should reject the transfer? (keyword heuristic on its own wording)"""
    accepts = re.search(r"\b(?:is|be|are|should be) (?:accepted|allowed|successful|processed|completed)|succeed", expected, re.I)
    return bool(_REJECT.search(expected)) and not (accepts and not re.search(r"not (?:be )?(?:accepted|allowed)", expected, re.I))


def classify_outcome(texts: list[str]) -> str:
    """'accepted' if the page confirms the transfer, 'rejected' if it shows an error, else 'other'."""
    joined = " ".join(texts)
    if "Transfer Complete" in joined:
        return "accepted"
    if re.search(r"error|invalid|required|must", joined, re.I):
        return "rejected"
    return "other"
