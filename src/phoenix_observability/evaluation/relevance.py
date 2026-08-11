"""Answer relevance is an application-specific Phoenix ClassificationEvaluator."""

from __future__ import annotations

from typing import Any

ANSWER_RELEVANCE_TEMPLATE = """Evaluate whether the answer directly addresses the user's question.

Question: {{input}}
Answer: {{output}}

Choose exactly one label:
- relevant: directly and usefully answers the question
- partially_relevant: addresses only part of the question or adds substantial distraction
- irrelevant: does not answer the question
"""


def create_answer_relevance_evaluator(llm: Any) -> Any:
    from phoenix.evals import ClassificationEvaluator

    return ClassificationEvaluator(
        name="answer_relevance",
        llm=llm,
        prompt_template=ANSWER_RELEVANCE_TEMPLATE,
        choices={"irrelevant": 0.0, "partially_relevant": 0.5, "relevant": 1.0},
        temperature=0.0,
    )
