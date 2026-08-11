"""End-to-end RAG pipeline represented as a trace tree in Phoenix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from phoenix.otel import using_attributes

from phoenix_observability.azure_openai_client import LLMResponse, Usage
from phoenix_observability.config import Settings
from phoenix_observability.llm_service import CompletionService, build_grounded_messages
from phoenix_observability.retriever import Retriever, SearchResult
from phoenix_observability.tracing import mark_error, mark_ok, set_span_input, set_span_output


@dataclass(frozen=True)
class RAGResult:
    query: str
    answer: str
    contexts: list[str]
    document_ids: list[str]
    scores: list[float]
    usage: Usage
    llm_latency_seconds: float


class RAGPipeline:
    def __init__(
        self,
        retriever: Retriever,
        llm: CompletionService,
        tracer: Any,
        settings: Settings,
        *,
        prompt_version: str = "v2",
        top_k: int | None = None,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.tracer = tracer
        self.settings = settings
        self.prompt_version = prompt_version
        self.top_k = top_k or settings.rag_top_k

    def answer(
        self,
        query: str,
        *,
        user_id: str = "demo-user",
        session_id: str = "demo-session",
    ) -> RAGResult:
        metadata = {
            "environment": "demo",
            "prompt_version": self.prompt_version,
            "retriever_mode": self.settings.retriever_mode,
            "top_k": self.top_k,
        }
        with (
            using_attributes(
                user_id=user_id,
                session_id=session_id,
                metadata=metadata,
                tags=["rag", "azure-openai", "fictional-data"],
            ),
            self.tracer.start_as_current_span(
                "rag_request", openinference_span_kind="chain"
            ) as root_span,
        ):
            set_span_input(root_span, query, visible=self.settings.trace_content)
            try:
                results = self.retriever.search(query, top_k=self.top_k)
                context = self._build_context(results)
                messages = self._build_prompt(query, context)
                response = self.llm.complete(messages)
                result = RAGResult(
                    query=query,
                    answer=response.text,
                    contexts=[item.document.text for item in results],
                    document_ids=[item.document.id for item in results],
                    scores=[item.score for item in results],
                    usage=response.usage,
                    llm_latency_seconds=response.latency_seconds,
                )
                root_span.set_attribute("app.retrieved_document_count", len(results))
                root_span.set_attribute("app.prompt_version", self.prompt_version)
                root_span.set_attribute("app.llm_latency_seconds", response.latency_seconds)
                root_span.set_attribute("app.token_count.total", response.usage.total_tokens)
                set_span_output(root_span, response.text, visible=self.settings.trace_content)
                mark_ok(root_span)
                return result
            except Exception as exc:
                mark_error(root_span, exc)
                raise

    def _build_context(self, results: list[SearchResult]) -> str:
        with self.tracer.start_as_current_span(
            "prompt.context_assembly", openinference_span_kind="chain"
        ) as span:
            chunks = [
                f"[{item.document.id}] {item.document.title}\n{item.document.text}"
                for item in results
            ]
            context = "\n\n---\n\n".join(chunks) if chunks else "No relevant context was retrieved."
            span.set_attribute("app.context_chunk_count", len(chunks))
            span.set_attribute("app.context_character_count", len(context))
            set_span_output(span, context, visible=self.settings.trace_content)
            mark_ok(span)
            return context

    def _build_prompt(self, query: str, context: str) -> list[dict[str, str]]:
        with self.tracer.start_as_current_span(
            "prompt.construction", openinference_span_kind="chain"
        ) as span:
            messages = build_grounded_messages(query, context, prompt_version=self.prompt_version)
            span.set_attribute("llm.prompt_template.version", self.prompt_version)
            set_span_input(
                span, {"query": query, "context": context}, visible=self.settings.trace_content
            )
            set_span_output(span, messages, visible=self.settings.trace_content)
            mark_ok(span)
            return messages


def empty_response(text: str) -> LLMResponse:
    """Convenience for deterministic fakes and examples."""
    return LLMResponse(text=text, deployment="fake", latency_seconds=0.0, usage=Usage())
