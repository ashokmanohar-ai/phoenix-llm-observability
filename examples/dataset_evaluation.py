"""Evaluate a JSON dataset and write JSON/CSV summaries without hard-coded scores."""

from pathlib import Path

from phoenix_observability.config import Settings
from phoenix_observability.datasets import load_cases
from phoenix_observability.evaluation.evaluator import PhoenixRAGEvaluator, summarize
from phoenix_observability.reporting import write_reports
from phoenix_observability.telemetry import configure_telemetry


def main() -> None:
    settings = Settings.from_env().validated(require_azure=True)
    telemetry = configure_telemetry(settings)
    evaluator = PhoenixRAGEvaluator(settings)
    cases = load_cases("datasets/rag_eval_dataset.json")
    results = [evaluator.evaluate_case(case) for case in cases]
    summary = summarize(results)
    paths = write_reports(results, summary, Path("reports"))
    print(summary)
    print("Reports:", *(str(path) for path in paths))
    telemetry.flush()


if __name__ == "__main__":
    main()
