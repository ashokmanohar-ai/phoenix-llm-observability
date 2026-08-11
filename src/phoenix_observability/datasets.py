"""Local dataset loading, Phoenix upload, and production-failure conversion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phoenix.client import Client

from phoenix_observability.config import Settings


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Dataset file must contain a JSON array")
    return payload


def upload_rag_dataset(
    path: str | Path,
    *,
    name: str,
    settings: Settings,
    description: str = "Repeatable fictional RAG evaluation cases",
) -> Any:
    cases = load_cases(path)
    client = Client(
        base_url=settings.phoenix_endpoint,
        api_key=settings.phoenix_api_key or None,
    )
    return client.datasets.create_dataset(
        name=name,
        dataset_description=description,
        inputs=[{"query": case["query"]} for case in cases],
        outputs=[{"reference_answer": case.get("reference_answer", "")} for case in cases],
        metadata=[
            {
                "case_id": case.get("id"),
                "category": case.get("category"),
                "expected_behavior": case.get("expected_behavior"),
            }
            for case in cases
        ],
    )


def production_failure_to_example(
    *,
    trace_id: str,
    query: str,
    bad_answer: str,
    retrieved_context: list[str],
    reference_answer: str,
    root_cause: str,
) -> dict[str, Any]:
    """Create a durable regression case without copying credentials or headers."""
    return {
        "id": f"production-{trace_id[-8:]}",
        "query": query,
        "retrieved_context": retrieved_context,
        "generated_answer": bad_answer,
        "reference_answer": reference_answer,
        "metadata": {
            "source_trace_id": trace_id,
            "root_cause": root_cause,
            "privacy_reviewed": False,
        },
    }
