"""Upload/reuse a Phoenix dataset and run a trace-connected RAG experiment."""

from __future__ import annotations

import argparse

from phoenix_observability.bootstrap import build_demo_rag
from phoenix_observability.config import Settings
from phoenix_observability.datasets import upload_rag_dataset
from phoenix_observability.evaluation.evaluator import PhoenixRAGEvaluator
from phoenix_observability.experiments import run_rag_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="exampleco-rag-regression")
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--prompt-version", choices=["v1", "v2"], default="v2")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--dry-run", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env().validated(require_azure=True)
    if args.upload:
        upload_rag_dataset("datasets/regression_dataset.json", name=args.dataset, settings=settings)
    pipeline, telemetry, _, _ = build_demo_rag(
        settings, prompt_version=args.prompt_version, top_k=args.top_k
    )
    judge = PhoenixRAGEvaluator(settings)
    judge.faithfulness.bind(
        {
            "input": "input.query",
            "output": "output.answer",
            "context": lambda record: "\n\n".join(record["output"]["contexts"]),
        }
    )
    judge.answer_relevance.bind({"input": "input.query", "output": "output.answer"})
    judge.correctness.bind(
        {
            "input": "input.query",
            "output": "output.answer",
            "reference": "expected.reference_answer",
        }
    )

    def task(input: dict[str, str]) -> dict[str, object]:
        result = pipeline.answer(input["query"], session_id="phoenix-experiment")
        return {
            "answer": result.answer,
            "contexts": result.contexts,
            "document_ids": result.document_ids,
            "latency_seconds": result.llm_latency_seconds,
            "total_tokens": result.usage.total_tokens,
        }

    experiment = run_rag_experiment(
        dataset_name=args.dataset,
        task=task,
        evaluators=[judge.faithfulness, judge.answer_relevance, judge.correctness],
        experiment_name=f"prompt-{args.prompt_version}-top-k-{args.top_k}",
        settings=settings,
        metadata={
            "prompt_version": args.prompt_version,
            "top_k": args.top_k,
            "chat_deployment": settings.azure_chat_deployment,
            "retriever_mode": settings.retriever_mode,
        },
        dry_run=args.dry_run or False,
    )
    telemetry.flush()
    print(experiment)


if __name__ == "__main__":
    main()
