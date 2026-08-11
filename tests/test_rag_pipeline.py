from __future__ import annotations

from conftest import make_test_tracer

from phoenix_observability.azure_openai_client import LLMResponse, Usage
from phoenix_observability.config import Settings
from phoenix_observability.rag_pipeline import RAGPipeline
from phoenix_observability.retriever import Document, LexicalRetriever


class FakeLLM:
    def complete(self, messages, **kwargs):  # noqa: ANN001, ANN003, ANN201
        del kwargs
        assert "30 calendar days" in messages[1]["content"]
        return LLMResponse(
            text="Refunds are available for 30 calendar days [policy-refund-001].",
            deployment="fake",
            latency_seconds=0.01,
            usage=Usage(20, 10, 30),
        )


def test_lexical_retriever_returns_refund_policy() -> None:
    settings = Settings(trace_content=True, rag_min_score=0.01)
    documents = [
        Document("refund", "Refund", "Refunds are allowed for 30 days.", {}),
        Document("password", "Password", "Reset links expire in 15 minutes.", {}),
    ]
    retriever = LexicalRetriever(documents, make_test_tracer(), settings)
    assert retriever.search("What is the refund period?", top_k=1)[0].document.id == "refund"


def test_rag_pipeline_propagates_context_usage_and_document_ids() -> None:
    settings = Settings(trace_content=False, rag_min_score=0.01)
    document = Document(
        "policy-refund-001",
        "Refund policy",
        "Customers may request a refund within 30 calendar days.",
        {},
    )
    tracer = make_test_tracer()
    retriever = LexicalRetriever([document], tracer, settings)
    result = RAGPipeline(retriever, FakeLLM(), tracer, settings).answer(
        "What is the refund window?"
    )
    assert result.document_ids == ["policy-refund-001"]
    assert result.usage.total_tokens == 30
    assert result.contexts == [document.text]
