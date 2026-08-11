"""Azure OpenAI application client. OpenInference auto-instrumentation traces SDK calls."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from openai import AzureOpenAI

from phoenix_observability.config import Settings


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class LLMResponse:
    text: str
    deployment: str
    latency_seconds: float
    usage: Usage


class AzureOpenAIService:
    """Thin, injectable wrapper around ``openai.AzureOpenAI``."""

    def __init__(self, settings: Settings, client: AzureOpenAI | None = None) -> None:
        settings.validated(require_azure=True)
        self.settings = settings
        self.client = client or AzureOpenAI(
            api_key=settings.azure_api_key,
            azure_endpoint=settings.azure_endpoint,
            api_version=settings.azure_api_version,
            timeout=60.0,
            max_retries=2,
        )

    def complete(
        self,
        messages: Sequence[dict[str, str]],
        *,
        deployment: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> LLMResponse:
        model = deployment or self.settings.azure_chat_deployment
        started = perf_counter()
        response = self.client.chat.completions.create(
            model=model,
            messages=list(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = perf_counter() - started
        usage = response.usage
        text = response.choices[0].message.content or ""
        return LLMResponse(
            text=text,
            deployment=model,
            latency_seconds=latency,
            usage=Usage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                total_tokens=getattr(usage, "total_tokens", 0) or 0,
            ),
        )

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not self.settings.azure_embedding_deployment:
            raise ValueError("AZURE_OPENAI_EMBEDDING_DEPLOYMENT is not configured")
        response = self.client.embeddings.create(
            model=self.settings.azure_embedding_deployment,
            input=list(texts),
        )
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


def create_azure_evaluator_llm(settings: Settings) -> Any:
    """Build Phoenix Evals' current Azure adapter using a separate judge deployment."""
    from phoenix.evals.llm import LLM

    deployment = settings.azure_evaluator_deployment or settings.azure_chat_deployment
    if not deployment:
        raise ValueError("AZURE_OPENAI_EVALUATOR_DEPLOYMENT or chat deployment is required")
    settings.validated(require_azure=True)
    return LLM(
        provider="azure",
        model=deployment,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
        azure_endpoint=settings.azure_endpoint,
        timeout=60.0,
    )
