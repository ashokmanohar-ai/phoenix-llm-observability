from __future__ import annotations

import json

from phoenix_observability.evaluation.evaluator import EvaluationResult
from phoenix_observability.reporting import write_reports


def test_reports_are_machine_and_human_readable(tmp_path) -> None:  # noqa: ANN001
    result = EvaluationResult(
        case_id="case-1",
        faithfulness=1.0,
        answer_relevance=1.0,
        retrieval_relevance=1.0,
        correctness=1.0,
        labels={"faithfulness": "faithful"},
        explanations={"faithfulness": "supported"},
    )
    json_path, csv_path = write_reports([result], {"example_count": 1}, tmp_path)
    assert json.loads(json_path.read_text())["summary"]["example_count"] == 1
    assert "case-1" in csv_path.read_text()
