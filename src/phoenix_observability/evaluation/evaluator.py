"""Evaluate RAG outputs with Phoenix Evals or deterministic offline heuristics."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any

from phoenix_observability.azure_openai_client import create_azure_evaluator_llm
from phoenix_observability.config import Settings
from phoenix_observability.evaluation.correctness import (
    create_reference_correctness_evaluator,
)
from phoenix_observability.evaluation.faithfulness import create_faithfulness_evaluator
from phoenix_observability.evaluation.relevance import create_answer_relevance_evaluator
from phoenix_observability.evaluation.retrieval import create_document_relevance_evaluator

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "within",
    "you",
}


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    faithfulness: float
    answer_relevance: float
    retrieval_relevance: float
    correctness: float
    labels: dict[str, str]
    explanations: dict[str, str]
    latency_seconds: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PhoenixRAGEvaluator:
    """LLM-as-judge evaluation using the Phoenix Evals 3.x API."""

    def __init__(self, settings: Settings) -> None:
        llm = create_azure_evaluator_llm(settings)
        self.faithfulness = create_faithfulness_evaluator(llm)
        self.answer_relevance = create_answer_relevance_evaluator(llm)
        self.document_relevance = create_document_relevance_evaluator(llm)
        self.correctness = create_reference_correctness_evaluator(llm)

    def evaluate_case(self, case: dict[str, Any]) -> EvaluationResult:
        query = case["query"]
        answer = case["generated_answer"]
        contexts = case.get("retrieved_context", [])
        reference = case.get("reference_answer", "")
        faithful = _first_score(
            self.faithfulness.evaluate(
                {"input": query, "output": answer, "context": "\n\n".join(contexts)}
            )
        )
        relevant = _first_score(self.answer_relevance.evaluate({"input": query, "output": answer}))
        document_scores = [
            _first_score(
                self.document_relevance.evaluate({"input": query, "document_text": document})
            )
            for document in contexts
        ]
        correctness = _first_score(
            self.correctness.evaluate({"input": query, "output": answer, "reference": reference})
        )
        metrics = {
            "faithfulness": faithful,
            "answer_relevance": relevant,
            "retrieval_relevance": _aggregate_scores(document_scores),
            "correctness": correctness,
        }
        return EvaluationResult(
            case_id=case.get("id", "unknown"),
            faithfulness=metrics["faithfulness"][0],
            answer_relevance=metrics["answer_relevance"][0],
            retrieval_relevance=metrics["retrieval_relevance"][0],
            correctness=metrics["correctness"][0],
            labels={name: score[1] for name, score in metrics.items()},
            explanations={name: score[2] for name, score in metrics.items()},
            **_operational_fields(case),
        )


class OfflineRAGEvaluator:
    """Cheap deterministic smoke signal for unit tests and pull requests.

    These heuristics are not a substitute for Phoenix LLM evaluators. They make
    CI reproducible when Azure credentials are intentionally unavailable.
    """

    def evaluate_case(self, case: dict[str, Any]) -> EvaluationResult:
        query = case["query"]
        answer = case["generated_answer"]
        contexts = case.get("retrieved_context", [])
        reference = case.get("reference_answer", "")
        context = " ".join(contexts)
        correctness = token_f1(answer, reference)
        faithfulness = max(token_recall(answer, context), correctness)
        answer_relevance = max(
            token_recall(query, answer), token_recall(answer, query), correctness
        )
        retrieval_relevance = max(
            (
                max(
                    token_recall(query, document),
                    token_recall(document, query),
                    token_f1(reference, document),
                )
                for document in contexts
            ),
            default=0.0,
        )
        scores = {
            "faithfulness": faithfulness,
            "answer_relevance": answer_relevance,
            "retrieval_relevance": retrieval_relevance,
            "correctness": correctness,
        }
        return EvaluationResult(
            case_id=case.get("id", "unknown"),
            faithfulness=faithfulness,
            answer_relevance=answer_relevance,
            retrieval_relevance=retrieval_relevance,
            correctness=correctness,
            labels={name: "pass" if value >= 0.70 else "review" for name, value in scores.items()},
            explanations={
                name: (
                    "Deterministic token-overlap smoke signal; run Azure judge mode "
                    "for semantic quality."
                )
                for name in scores
            },
            **_operational_fields(case),
        )


def summarize(results: Iterable[EvaluationResult]) -> dict[str, Any]:
    items = list(results)
    metric_names = (
        "faithfulness",
        "answer_relevance",
        "retrieval_relevance",
        "correctness",
    )
    averages = {
        name: round(mean(getattr(item, name) for item in items), 4) if items else 0.0
        for name in metric_names
    }
    latencies = [item.latency_seconds for item in items if item.latency_seconds is not None]
    return {
        "example_count": len(items),
        "averages": averages,
        "failure_count": sum(
            1 for item in items if min(getattr(item, name) for name in metric_names) < 0.70
        ),
        "latency_seconds": {
            "average": round(mean(latencies), 4) if latencies else None,
            "maximum": round(max(latencies), 4) if latencies else None,
        },
        "total_tokens": sum(item.total_tokens or 0 for item in items),
    }


def gate_failures(summary: dict[str, Any], thresholds: dict[str, float]) -> list[str]:
    averages = summary["averages"]
    return [
        f"{name}: {averages.get(name, 0.0):.3f} < {minimum:.3f}"
        for name, minimum in thresholds.items()
        if averages.get(name, 0.0) < minimum
    ]


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOP_WORDS and len(token) > 1
    }


def token_recall(source: str, evidence: str) -> float:
    source_tokens = _tokens(source)
    if not source_tokens:
        return 1.0
    return len(source_tokens & _tokens(evidence)) / len(source_tokens)


def token_f1(candidate: str, reference: str) -> float:
    candidate_tokens = _tokens(candidate)
    reference_tokens = _tokens(reference)
    if not candidate_tokens or not reference_tokens:
        return float(candidate_tokens == reference_tokens)
    overlap = len(candidate_tokens & reference_tokens)
    precision = overlap / len(candidate_tokens)
    recall = overlap / len(reference_tokens)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _first_score(scores: list[Any]) -> tuple[float, str, str]:
    if not scores:
        return 0.0, "missing", "Evaluator returned no score."
    score = scores[0]
    return (
        float(score.score if score.score is not None else 0.0),
        str(score.label or "unlabeled"),
        str(score.explanation or ""),
    )


def _aggregate_scores(scores: list[tuple[float, str, str]]) -> tuple[float, str, str]:
    if not scores:
        return 0.0, "no_context", "No documents were retrieved."
    value = mean(score[0] for score in scores)
    return value, "relevant" if value >= 0.5 else "unrelated", "Average per-document relevance."


def _operational_fields(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "latency_seconds": case.get("latency_seconds"),
        "prompt_tokens": case.get("prompt_tokens"),
        "completion_tokens": case.get("completion_tokens"),
        "total_tokens": case.get("total_tokens"),
    }
