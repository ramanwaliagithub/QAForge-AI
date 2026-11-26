"""The service under test: `POST /ask` answers a question from the help-center passages with a local model.

Deliberately ordinary: retrieval of the 3 closest passages, a prompt that tells the model to answer only from them and to say it does not know
otherwise, a default sampling temperature (0.7) like most applications ship with. Nothing here is built to be easy to test, because the point
of Phase 4 is what testing it takes.
"""
import os
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from framework.llm_client import LLMClient
from rag_app.knowledge_base import KnowledgeBase

NO_ANSWER = "I don't know based on the help center."
TOP_K = 3

PROMPT = """You are the help-center assistant of the ParaBank online bank. Answer the customer's question using ONLY the passages below.
If the passages do not contain the answer, reply exactly: {no_answer}
Keep the answer to one to three sentences.

PASSAGES:
{passages}

QUESTION: {question}"""


class AskRequest(BaseModel):
    """A customer question: 1 to 500 characters."""

    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    """The answer, the ids of the passages the model was shown (retrieval, not the model's own claim), the model and the time taken."""

    answer: str
    sources: list[str]
    model: str
    latency_ms: int


def create_app(client: LLMClient, knowledge: KnowledgeBase | None = None, temperature: float | None = None, prompt: str = PROMPT) -> FastAPI:
    """Build the service around a model client (a real one, or a scripted one in tests). `knowledge`, `temperature` and `prompt` can be
    replaced, which is how the evals break it on purpose.
    """
    kb = knowledge or KnowledgeBase(client)
    temp = float(os.getenv("ASK_TEMPERATURE", "0.7")) if temperature is None else temperature
    app = FastAPI(title="ParaBank help-center assistant")

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        """Answer one question from the top-k passages; 503 when the model cannot be reached."""
        start = time.perf_counter()
        try:
            hits = kb.search(request.question, TOP_K)
            passages = "\n".join(f"[{p.id}] {p.title}: {p.text}" for p, _ in hits)
            reply = client.generate(prompt.format(no_answer=NO_ANSWER, passages=passages, question=request.question), temperature=temp)
        except Exception as error:  # the model server being down is an outage, not a bug in the request
            raise HTTPException(status_code=503, detail=f"the model is not available: {error}") from error
        return AskResponse(answer=reply.text.strip(), sources=[p.id for p, _ in hits], model=reply.model,
                           latency_ms=round((time.perf_counter() - start) * 1000))

    return app
