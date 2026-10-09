from framework.llm_client import OllamaClient


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
