"""Attach computed evaluation results to a Phoenix span for in-context diagnosis."""

from __future__ import annotations

from phoenix.client import Client

from phoenix_observability.config import Settings
from phoenix_observability.evaluation.evaluator import EvaluationResult


def attach_evaluations_to_span(
    *, span_id: str, result: EvaluationResult, settings: Settings
) -> None:
    client = Client(
        base_url=settings.phoenix_endpoint,
        api_key=settings.phoenix_api_key or None,
    )
    values = {
        "faithfulness": result.faithfulness,
        "answer_relevance": result.answer_relevance,
        "retrieval_relevance": result.retrieval_relevance,
        "correctness": result.correctness,
    }
    for name, score in values.items():
        client.spans.add_span_annotation(
            span_id=span_id,
            annotation_name=name,
            annotator_kind="LLM",
            score=score,
            label=result.labels.get(name),
            explanation=result.explanations.get(name),
            metadata={"case_id": result.case_id, "repository_example": True},
            sync=True,
        )
