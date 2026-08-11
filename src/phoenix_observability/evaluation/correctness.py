"""General and reference-aware answer correctness evaluator factories."""

from __future__ import annotations

from typing import Any

REFERENCE_CORRECTNESS_TEMPLATE = """Compare the candidate answer with the reference answer.

Question: {{input}}
Candidate answer: {{output}}
Reference answer: {{reference}}

Choose exactly one label:
- correct: factually consistent with and as complete as the reference
- partially_correct: contains the core answer but is incomplete or has a minor issue
- incorrect: contradicts or misses the reference answer
"""


def create_general_correctness_evaluator(llm: Any) -> Any:
    from phoenix.evals.metrics import CorrectnessEvaluator

    return CorrectnessEvaluator(llm=llm, temperature=0.0)


def create_reference_correctness_evaluator(llm: Any) -> Any:
    """Use a custom modern evaluator because built-in Correctness has no reference input."""
    from phoenix.evals import ClassificationEvaluator

    return ClassificationEvaluator(
        name="reference_correctness",
        llm=llm,
        prompt_template=REFERENCE_CORRECTNESS_TEMPLATE,
        choices={"incorrect": 0.0, "partially_correct": 0.5, "correct": 1.0},
        temperature=0.0,
    )
