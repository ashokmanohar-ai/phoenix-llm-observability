from __future__ import annotations

from types import SimpleNamespace

from phoenix_observability.azure_openai_client import AzureOpenAIService
from phoenix_observability.config import Settings


class FakeCompletions:
    def create(self, **kwargs):  # noqa: ANN001, ANN201
        assert kwargs["model"] == "chat-deployment"
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="grounded answer"))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=3, total_tokens=13),
        )


class FakeEmbeddings:
    def create(self, **kwargs):  # noqa: ANN001, ANN201
        assert kwargs["model"] == "embedding-deployment"
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=index, embedding=[float(index), 1.0])
                for index, _ in enumerate(kwargs["input"])
            ]
        )


class FakeClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions())
        self.embeddings = FakeEmbeddings()


def settings() -> Settings:
    return Settings(
        azure_api_key="fake",
        azure_endpoint="https://example.openai.azure.com",
        azure_api_version="2026-01-01",
        azure_chat_deployment="chat-deployment",
        azure_embedding_deployment="embedding-deployment",
    )


def test_azure_wrapper_extracts_actual_usage() -> None:
    service = AzureOpenAIService(settings(), client=FakeClient())  # type: ignore[arg-type]
    response = service.complete([{"role": "user", "content": "hello"}])
    assert response.text == "grounded answer"
    assert response.usage.total_tokens == 13
    assert response.latency_seconds >= 0


def test_azure_wrapper_preserves_embedding_order() -> None:
    service = AzureOpenAIService(settings(), client=FakeClient())  # type: ignore[arg-type]
    assert service.embed(["a", "b"]) == [[0.0, 1.0], [1.0, 1.0]]
