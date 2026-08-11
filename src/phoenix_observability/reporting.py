"""Portable JSON/CSV evaluation reports for artifacts and quality gates."""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from phoenix_observability.evaluation.evaluator import EvaluationResult


def write_reports(
    results: Sequence[EvaluationResult], summary: dict[str, Any], output_dir: str | Path
) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "evaluation_results.json"
    csv_path = directory / "evaluation_results.csv"
    json_path.write_text(
        json.dumps(
            {"summary": summary, "results": [item.to_dict() for item in results]},
            indent=2,
        ),
        encoding="utf-8",
    )
    rows = [item.to_dict() for item in results]
    fieldnames = [
        "case_id",
        "faithfulness",
        "answer_relevance",
        "retrieval_relevance",
        "correctness",
        "latency_seconds",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "labels",
        "explanations",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row["labels"] = json.dumps(row["labels"], sort_keys=True)
            row["explanations"] = json.dumps(row["explanations"], sort_keys=True)
            writer.writerow(row)
    return json_path, csv_path
