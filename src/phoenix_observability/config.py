"""Environment-driven configuration with no secret logging or hard-coded credentials."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be numeric") from exc


def _as_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Secret values are intentionally excluded from ``safe_summary``."""

    azure_api_key: str = ""
    azure_endpoint: str = ""
    azure_api_version: str = ""
    azure_chat_deployment: str = ""
    azure_embedding_deployment: str = ""
    azure_evaluator_deployment: str = ""
    phoenix_endpoint: str = "http://localhost:6006"
    phoenix_collector_endpoint: str = "http://localhost:6006"
    phoenix_project_name: str = "phoenix-llm-observability-dev"
    phoenix_api_key: str = ""
    phoenix_protocol: str = "http/protobuf"
    phoenix_batch_export: bool = False
    trace_content: bool = False
    document_preview_chars: int = 200
    retriever_mode: str = "lexical"
    rag_top_k: int = 3
    rag_min_score: float = 0.05
    min_faithfulness: float = 0.80
    min_answer_relevance: float = 0.75
    min_retrieval_relevance: float = 0.75
    min_correctness: float = 0.75

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> Settings:
        if env_file:
            load_dotenv(env_file, override=False)
        return cls(
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/"),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", ""),
            azure_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", ""),
            azure_embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", ""),
            azure_evaluator_deployment=os.getenv(
                "AZURE_OPENAI_EVALUATOR_DEPLOYMENT",
                os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", ""),
            ),
            phoenix_endpoint=os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006").rstrip("/"),
            phoenix_collector_endpoint=os.getenv(
                "PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:6006"
            ).rstrip("/"),
            phoenix_project_name=os.getenv("PHOENIX_PROJECT_NAME", "phoenix-llm-observability-dev"),
            phoenix_api_key=os.getenv("PHOENIX_API_KEY", ""),
            phoenix_protocol=os.getenv("PHOENIX_PROTOCOL", "http/protobuf"),
            phoenix_batch_export=_as_bool(os.getenv("PHOENIX_BATCH_EXPORT")),
            trace_content=_as_bool(os.getenv("PHOENIX_TRACE_CONTENT")),
            document_preview_chars=_as_int("PHOENIX_DOCUMENT_PREVIEW_CHARS", 200),
            retriever_mode=os.getenv("RAG_RETRIEVER_MODE", "lexical").lower(),
            rag_top_k=_as_int("RAG_TOP_K", 3),
            rag_min_score=_as_float("RAG_MIN_SCORE", 0.05),
            min_faithfulness=_as_float("MIN_FAITHFULNESS", 0.80),
            min_answer_relevance=_as_float("MIN_ANSWER_RELEVANCE", 0.75),
            min_retrieval_relevance=_as_float("MIN_RETRIEVAL_RELEVANCE", 0.75),
            min_correctness=_as_float("MIN_CORRECTNESS", 0.75),
        ).validated()

    def validated(self, *, require_azure: bool = False) -> Settings:
        if self.phoenix_protocol not in {"http/protobuf", "grpc"}:
            raise ValueError("PHOENIX_PROTOCOL must be 'http/protobuf' or 'grpc'")
        if self.retriever_mode not in {"lexical", "azure_embeddings"}:
            raise ValueError("RAG_RETRIEVER_MODE must be 'lexical' or 'azure_embeddings'")
        if self.rag_top_k < 1:
            raise ValueError("RAG_TOP_K must be at least 1")
        if self.document_preview_chars < 0:
            raise ValueError("PHOENIX_DOCUMENT_PREVIEW_CHARS cannot be negative")
        for name, value in self.quality_thresholds.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if require_azure:
            required = {
                "AZURE_OPENAI_API_KEY": self.azure_api_key,
                "AZURE_OPENAI_ENDPOINT": self.azure_endpoint,
                "AZURE_OPENAI_API_VERSION": self.azure_api_version,
                "AZURE_OPENAI_CHAT_DEPLOYMENT": self.azure_chat_deployment,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError("Missing required Azure OpenAI settings: " + ", ".join(missing))
        if self.retriever_mode == "azure_embeddings" and not self.azure_embedding_deployment:
            raise ValueError(
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT is required for azure_embeddings mode"
            )
        return self

    @property
    def quality_thresholds(self) -> dict[str, float]:
        return {
            "faithfulness": self.min_faithfulness,
            "answer_relevance": self.min_answer_relevance,
            "retrieval_relevance": self.min_retrieval_relevance,
            "correctness": self.min_correctness,
        }

    def safe_summary(self) -> dict[str, object]:
        """Return operational configuration without secret values."""
        return {
            "azure_endpoint_configured": bool(self.azure_endpoint),
            "chat_deployment": self.azure_chat_deployment,
            "embedding_deployment": self.azure_embedding_deployment,
            "evaluator_deployment": self.azure_evaluator_deployment,
            "phoenix_endpoint": self.phoenix_endpoint,
            "phoenix_project_name": self.phoenix_project_name,
            "trace_content": self.trace_content,
            "retriever_mode": self.retriever_mode,
            "rag_top_k": self.rag_top_k,
        }
