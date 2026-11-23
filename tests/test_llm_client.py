import pytest

from framework.llm_client import OllamaClient, ScriptedClient


class FakeOllama:
    def __init__(self):
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return {"message": {"content": "hi"}, "prompt_eval_count": 7, "eval_count": 2}

    def embeddings(self, **kwargs):
        return {"embedding": [0.1, 0.2]}


def test_generate_builds_messages_and_options():
    fake = FakeOllama()
    client = OllamaClient(model="m", client=fake)
    out = client.generate("question", system="be brief", temperature=0.7, json_mode=True, num_ctx=2048)

    call = fake.calls[0]
    assert call["messages"] == [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "question"},
    ]
    assert call["options"] == {"temperature": 0.7, "num_ctx": 2048}
    assert call["format"] == "json"
    assert (out.text, out.model, out.prompt_tokens, out.completion_tokens) == ("hi", "m", 7, 2)


def test_generate_without_system_or_json():
    fake = FakeOllama()
    OllamaClient(model="m", client=fake).generate("q")
    assert fake.calls[0]["messages"] == [{"role": "user", "content": "q"}]
    assert fake.calls[0]["format"] is None


def test_embed_returns_vector():
    assert OllamaClient(client=FakeOllama()).embed("x") == [0.1, 0.2]


def test_scripted_client_answers_in_order_records_calls_and_encodes_non_strings():
    client = ScriptedClient("plain", {"a": 1}, ["x"], latency_s=0.25)
    assert [client.generate("p1", json_mode=True).text, client.generate("p2").text, client.generate("p3").text] == ["plain", '{"a": 1}', '["x"]']
    assert client.prompts == ["p1", "p2", "p3"] and client.kwargs[0]["json_mode"] is True and client.kwargs[1]["json_mode"] is False
    assert ScriptedClient("x", latency_s=0.25).generate("p").latency_s == 0.25


def test_scripted_client_raises_its_message_when_the_answers_run_out():
    client = ScriptedClient("only", exhausted="model is down")
    client.generate("one")
    with pytest.raises(RuntimeError, match="model is down"):
        client.generate("two")
    assert client.prompts == ["one", "two"]  # the unexpected call is recorded too
