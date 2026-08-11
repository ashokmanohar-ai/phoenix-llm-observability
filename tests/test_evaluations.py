from __future__ import annotations

from phoenix_observability.evaluation.evaluator import (
    OfflineRAGEvaluator,
    gate_failures,
    summarize,
    token_f1,
    token_recall,
)


def test_token_metrics_distinguish_supported_and_unsupported_answers() -> None:
    context = "Customers may request a refund within 30 calendar days."
    assert token_recall("refund within 30 days", context) > token_recall(
        "refund within 60 days", context
    )
    assert token_f1(context, context) == 1.0


def test_summary_and_gate_are_computed_not_hard_coded() -> None:
    evaluator = OfflineRAGEvaluator()
    result = evaluator.evaluate_case(
        {
            "id": "case",
            "query": "refund 30 days",
            "retrieved_context": ["refund 30 days"],
            "generated_answer": "refund 30 days",
            "reference_answer": "refund 30 days",
        }
    )
    summary = summarize([result])
    assert summary["averages"]["faithfulness"] == 1.0
    assert gate_failures(summary, {"faithfulness": 0.8}) == []
    assert gate_failures(summary, {"faithfulness": 1.1})
