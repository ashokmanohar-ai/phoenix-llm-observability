"""Headless evaluation report and optional CI quality gate."""

from __future__ import annotations

import argparse
import sys

from phoenix_observability.config import Settings
from phoenix_observability.datasets import load_cases
from phoenix_observability.evaluation.evaluator import (
    OfflineRAGEvaluator,
    PhoenixRAGEvaluator,
    gate_failures,
    summarize,
)
from phoenix_observability.reporting import write_reports
from phoenix_observability.telemetry import configure_telemetry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="datasets/rag_eval_dataset.json")
    parser.add_argument("--mode", choices=["offline", "azure"], default="offline")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--enforce", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = Settings.from_env()
    telemetry = None
    if args.mode == "azure":
        settings.validated(require_azure=True)
        telemetry = configure_telemetry(settings)
        evaluator = PhoenixRAGEvaluator(settings)
    else:
        evaluator = OfflineRAGEvaluator()
    results = [evaluator.evaluate_case(case) for case in load_cases(args.dataset)]
    summary = summarize(results)
    paths = write_reports(results, summary, args.output_dir)
    failures = gate_failures(summary, settings.quality_thresholds)
    if telemetry:
        telemetry.flush()
    print(f"Mode: {args.mode}")
    print(f"Summary: {summary}")
    print("Reports:", *(str(path) for path in paths))
    if args.enforce and failures:
        print("Quality gate failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Quality gate passed." if args.enforce else "Quality gate not enforced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
