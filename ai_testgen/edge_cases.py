"""Edge cases for a form, proposed by an LLM from the real page snapshot, then checked against the app."""
import json
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field, ValidationError

from framework.llm_client import LLMClient

PROMPT = """You are a QA engineer doing exploratory testing of the Transfer Funds page of a web banking app.

Page snapshot (what the page really contains):
{snapshot}

The logged-in customer has exactly two accounts, so the only valid values of "from_index" and "to_index" are 0 and 1
(never 2 or higher; there is no third account). The form has an amount field, a "from" account dropdown, a "to" account
dropdown and a Transfer button. Index 0 and 1 may be equal (same account for both dropdowns).

Propose {n} edge cases that are most likely to expose bugs. Each must be something you can do with only those
controls. Respond with JSON only, in this shape:
{{"edge_cases": [{{"title": "short title", "amount": "text typed into the amount field ('' for empty)",
"from_index": 0 or 1, "to_index": 0 or 1, "expected": "what a correct banking app should do (say whether the transfer is accepted or rejected)"}}]}}
"""


class EdgeCase(BaseModel):
    title: str = Field(min_length=3)
    amount: str
    from_index: int = Field(ge=0, le=1)
    to_index: int = Field(ge=0, le=1)
    expected: str = Field(min_length=3)


class EdgeCaseError(ValueError):
    pass


@dataclass
class Proposal:
    cases: list[EdgeCase]
    rejected: list[dict] = field(default_factory=list)  # proposals that cannot be done with the page's controls


def parse_edge_cases(text: str) -> Proposal:
    """Validate item by item: keep feasible cases, collect the rest (e.g. an account index that does not exist)."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise EdgeCaseError("No JSON object in the response.")
    try:
        data = json.loads(text[start : end + 1])
        items = data["edge_cases"] if isinstance(data, dict) else data
        if not isinstance(items, list):
            raise TypeError("edge_cases is not a list")
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise EdgeCaseError(f"Invalid edge case JSON: {e}") from e
    proposal = Proposal(cases=[])
    for item in items:
        try:
            proposal.cases.append(EdgeCase.model_validate(item))
        except ValidationError as e:
            proposal.rejected.append({"item": item, "why": "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())})
    if not proposal.cases:
        raise EdgeCaseError("No valid edge cases in the list.")
    return proposal


def propose_edge_cases(client: LLMClient, snapshot: str, n: int = 5, max_retries: int = 2) -> Proposal:
    prompt = PROMPT.format(snapshot=snapshot, n=n + 2)  # ask for a few extra: some proposals will be infeasible
    rejected, last = [], None
    for _ in range(max_retries + 1):
        reply = client.generate(prompt, temperature=0.0, json_mode=True, num_ctx=8192).text
        try:
            proposal = parse_edge_cases(reply)
        except EdgeCaseError as e:
            last = e
            prompt += f"\n\nYour previous answer was rejected: {e}\nReturn corrected JSON only."
            continue
        rejected += proposal.rejected
        return Proposal(cases=proposal.cases[:n], rejected=rejected)
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
