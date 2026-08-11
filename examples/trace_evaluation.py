"""Evaluate one case and attach its four quality signals to an existing Phoenix span."""

from __future__ import annotations

import argparse

from phoenix_observability.config import Settings
from phoenix_observability.datasets import load_cases
from phoenix_observability.evaluation.evaluator import PhoenixRAGEvaluator
from phoenix_observability.evaluation.trace_annotations import attach_evaluations_to_span
from phoenix_observability.telemetry import configure_telemetry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--span-id", required=True, help="Phoenix span ID to annotate")
    parser.add_argument("--case-id", default="rag-001-correct")
    args = parser.parse_args()
    settings = Settings.from_env().validated(require_azure=True)
    telemetry = configure_telemetry(settings)
    case = next(
        item for item in load_cases("datasets/rag_eval_dataset.json") if item["id"] == args.case_id
    )
    result = PhoenixRAGEvaluator(settings).evaluate_case(case)
    attach_evaluations_to_span(span_id=args.span_id, result=result, settings=settings)
    telemetry.flush()
    print(f"Attached evaluations for {args.case_id} to span {args.span_id}")


if __name__ == "__main__":
    main()
