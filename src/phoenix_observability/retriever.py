"""Traceable lexical and Azure-embedding retrievers over fictional JSON documents."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from openinference.semconv.trace import DocumentAttributes
from phoenix.otel import SpanAttributes

from phoenix_observability.config import Settings
from phoenix_observability.tracing import mark_error, mark_ok, set_span_input, set_span_output

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {"a", "an", "and", "are", "can", "do", "for", "how", "i", "is", "my", "the", "to"}


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class SearchResult:
    document: Document
    score: float


class Retriever(Protocol):
    def search(self, query: str, *, top_k: int) -> list[SearchResult]: ...


def load_documents(path: str | Path) -> list[Document]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Document(
            id=item["id"],
            title=item["title"],
            text=item["text"],
            metadata=item.get("metadata", {}),
        )
        for item in payload
    ]


def _tokens(text: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOP_WORDS}


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


class _TraceableRetriever:
    def __init__(self, documents: Sequence[Document], tracer: Any, settings: Settings) -> None:
        self.documents = list(documents)
        self.tracer = tracer
        self.settings = settings

    def _trace_results(
        self, span: Any, query: str, top_k: int, results: list[SearchResult]
    ) -> None:
        set_span_input(span, query, visible=self.settings.trace_content)
        span.set_attribute("retriever.top_k", top_k)
        span.set_attribute("retriever.result_count", len(results))
        output: list[dict[str, Any]] = []
        for index, result in enumerate(results):
            prefix = f"{SpanAttributes.RETRIEVAL_DOCUMENTS}.{index}"
            span.set_attribute(f"{prefix}.{DocumentAttributes.DOCUMENT_ID}", result.document.id)
            span.set_attribute(f"{prefix}.{DocumentAttributes.DOCUMENT_SCORE}", result.score)
            span.set_attribute(
                f"{prefix}.{DocumentAttributes.DOCUMENT_METADATA}",
                json.dumps(result.document.metadata),
            )
            if self.settings.trace_content:
                preview = result.document.text[: self.settings.document_preview_chars]
                span.set_attribute(f"{prefix}.{DocumentAttributes.DOCUMENT_CONTENT}", preview)
            output.append({"id": result.document.id, "score": round(result.score, 6)})
        set_span_output(span, output, visible=True)


class LexicalRetriever(_TraceableRetriever):
    """Dependency-free starter retriever with transparent, deterministic scoring."""

    def search(self, query: str, *, top_k: int) -> list[SearchResult]:
        with self.tracer.start_as_current_span(
            "retrieval.lexical", openinference_span_kind="retriever"
        ) as span:
            try:
                query_tokens = _tokens(query)
                scored = []
                for document in self.documents:
                    document_tokens = _tokens(f"{document.title} {document.text}")
                    union = query_tokens | document_tokens
                    score = len(query_tokens & document_tokens) / len(union) if union else 0.0
                    if score >= self.settings.rag_min_score:
                        scored.append(SearchResult(document, score))
                results = sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]
                self._trace_results(span, query, top_k, results)
                mark_ok(span)
                return results
            except Exception as exc:
                mark_error(span, exc)
                raise


class AzureEmbeddingRetriever(_TraceableRetriever):
    """Semantic retriever whose Azure embedding calls are auto-instrumented."""

    def __init__(
        self, documents: Sequence[Document], tracer: Any, settings: Settings, llm: Any
    ) -> None:
        super().__init__(documents, tracer, settings)
        self.llm = llm
        self._document_vectors: list[list[float]] | None = None

    def search(self, query: str, *, top_k: int) -> list[SearchResult]:
        with self.tracer.start_as_current_span(
            "retrieval.azure_embeddings", openinference_span_kind="retriever"
        ) as span:
            try:
                if self._document_vectors is None:
                    self._document_vectors = self.llm.embed(
                        [f"{doc.title}\n{doc.text}" for doc in self.documents]
                    )
                query_vector = self.llm.embed([query])[0]
                scored = [
                    SearchResult(document, _cosine(query_vector, vector))
                    for document, vector in zip(
                        self.documents, self._document_vectors, strict=False
                    )
                ]
                results = [
                    item
                    for item in sorted(scored, key=lambda item: item.score, reverse=True)
                    if item.score >= self.settings.rag_min_score
                ][:top_k]
                self._trace_results(span, query, top_k, results)
                mark_ok(span)
                return results
            except Exception as exc:
                mark_error(span, exc)
                raise


def create_retriever(
    documents: Sequence[Document], tracer: Any, settings: Settings, llm: Any | None = None
) -> Retriever:
    if settings.retriever_mode == "azure_embeddings":
        if llm is None:
            raise ValueError("An AzureOpenAIService is required for azure_embeddings mode")
        return AzureEmbeddingRetriever(documents, tracer, settings, llm)
    return LexicalRetriever(documents, tracer, settings)
