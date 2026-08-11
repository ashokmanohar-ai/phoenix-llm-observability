"""Composition helpers used by runnable examples."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from phoenix_observability.azure_openai_client import AzureOpenAIService
from phoenix_observability.config import Settings
from phoenix_observability.rag_pipeline import RAGPipeline
from phoenix_observability.retriever import create_retriever, load_documents
from phoenix_observability.telemetry import Telemetry, configure_telemetry

ROOT = Path(__file__).resolve().parents[2]


def build_demo_rag(
    settings: Settings,
    *,
    prompt_version: str = "v2",
    top_k: int | None = None,
) -> tuple[RAGPipeline, Telemetry, AzureOpenAIService, Any]:
    telemetry = configure_telemetry(settings)
    llm = AzureOpenAIService(settings)
    documents = load_documents(ROOT / "knowledge_base" / "company_policies.json")
    retriever = create_retriever(documents, telemetry.tracer, settings, llm)
    pipeline = RAGPipeline(
        retriever,
        llm,
        telemetry.tracer,
        settings,
        prompt_version=prompt_version,
        top_k=top_k,
    )
    return pipeline, telemetry, llm, retriever
