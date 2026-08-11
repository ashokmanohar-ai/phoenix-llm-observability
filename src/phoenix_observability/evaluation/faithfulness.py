"""Faithfulness and conversation hallucination evaluators."""

from __future__ import annotations

from typing import Any


def create_faithfulness_evaluator(llm: Any) -> Any:
    from phoenix.evals.metrics import FaithfulnessEvaluator

    return FaithfulnessEvaluator(llm=llm, temperature=0.0)


def create_hallucination_evaluator(llm: Any) -> Any:
    from phoenix.evals.metrics import HallucinationEvaluator

    return HallucinationEvaluator(llm=llm, temperature=0.0)
