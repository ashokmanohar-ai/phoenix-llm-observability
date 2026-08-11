"""Phoenix's current per-document retrieval relevance evaluator."""

from __future__ import annotations

from typing import Any


def create_document_relevance_evaluator(llm: Any) -> Any:
    from phoenix.evals.metrics import DocumentRelevanceEvaluator

    return DocumentRelevanceEvaluator(llm=llm, temperature=0.0)
