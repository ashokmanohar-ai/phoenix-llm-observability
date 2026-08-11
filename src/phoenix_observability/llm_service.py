"""Prompt construction and grounded generation service."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from phoenix_observability.azure_openai_client import LLMResponse

GROUNDING_SYSTEM_PROMPT = """You are a customer-support assistant for ExampleCo.
Answer only from the supplied context. If the context does not contain the answer, say:
"I don't have enough information in the knowledge base to answer that."
Do not invent policy details. Keep the answer concise and cite document IDs in square brackets."""


class CompletionService(Protocol):
    def complete(
        self,
        messages: Sequence[dict[str, str]],
        *,
        deployment: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> LLMResponse: ...


def build_grounded_messages(
    query: str, context: str, *, prompt_version: str = "v2"
) -> list[dict[str, str]]:
    instruction = GROUNDING_SYSTEM_PROMPT
    if prompt_version == "v1":
        instruction = "Answer the user using the supplied company context."
    return [
        {"role": "system", "content": instruction},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}",
        },
    ]
