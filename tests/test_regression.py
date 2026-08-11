from __future__ import annotations

from phoenix_observability.config import Settings
from phoenix_observability.datasets import load_cases, production_failure_to_example
from phoenix_observability.evaluation.evaluator import (
    OfflineRAGEvaluator,
    gate_failures,
    summarize,
)


def test_regression_dataset_passes_offline_smoke_gate() -> None:
    results = [
        OfflineRAGEvaluator().evaluate_case(case)
        for case in load_cases("datasets/regression_dataset.json")
    ]
    assert not gate_failures(summarize(results), Settings().quality_thresholds)


def test_production_failure_conversion_preserves_trace_link_without_secrets() -> None:
    example = production_failure_to_example(
        trace_id="abc123456789",
        query="refund?",
        bad_answer="60 days",
        retrieved_context=["30 days"],
        reference_answer="30 days",
        root_cause="generation",
    )
    assert example["metadata"]["source_trace_id"] == "abc123456789"
    assert example["metadata"]["privacy_reviewed"] is False
