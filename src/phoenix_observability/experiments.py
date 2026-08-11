"""Phoenix Client 3.x dataset experiments for RAG, prompt, and model comparison."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from phoenix.client import Client

from phoenix_observability.config import Settings


def run_rag_experiment(
    *,
    dataset_name: str,
    task: Callable[..., Any],
    evaluators: list[Any],
    experiment_name: str,
    settings: Settings,
    metadata: dict[str, Any],
    dry_run: bool | int = False,
) -> Any:
    client = Client(
        base_url=settings.phoenix_endpoint,
        api_key=settings.phoenix_api_key or None,
    )
    dataset = client.datasets.get_dataset(dataset=dataset_name)
    return client.experiments.run_experiment(
        dataset=dataset,
        task=task,
        evaluators=evaluators,
        experiment_name=experiment_name,
        experiment_description="Compare RAG configurations on the same controlled examples.",
        experiment_metadata=metadata,
        dry_run=dry_run,
    )
