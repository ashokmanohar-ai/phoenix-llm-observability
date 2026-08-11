from __future__ import annotations

import pytest
from conftest import make_test_tracer

from phoenix_observability.config import Settings
from phoenix_observability.retriever import (
    AzureEmbeddingRetriever,
    create_retriever,
    load_documents,
)


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[1.0, 0.0] if "refund" in text.lower() else [0.0, 1.0] for text in texts]


def test_load_documents_and_embedding_retrieval_cache() -> None:
    documents = load_documents("knowledge_base/company_policies.json")[:2]
    service = FakeEmbeddingService()
    settings = Settings(
        retriever_mode="azure_embeddings",
        azure_embedding_deployment="embedding",
        rag_min_score=0.0,
    )
    retriever = AzureEmbeddingRetriever(documents, make_test_tracer(), settings, service)
    assert retriever.search("refund", top_k=1)
    assert retriever.search("refund", top_k=1)
    assert service.calls == 3  # one document batch plus one query per search


def test_factory_requires_service_for_embedding_mode() -> None:
    settings = Settings(retriever_mode="azure_embeddings", azure_embedding_deployment="embedding")
    with pytest.raises(ValueError, match="AzureOpenAIService"):
        create_retriever([], make_test_tracer(), settings)
