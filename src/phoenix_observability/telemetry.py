"""Phoenix/OpenTelemetry registration and OpenAI automatic instrumentation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openinference.instrumentation import TraceConfig
from openinference.instrumentation.openai import OpenAIInstrumentor
from phoenix.otel import register

from phoenix_observability.config import Settings


@dataclass
class Telemetry:
    tracer_provider: Any
    tracer: Any

    def flush(self, timeout_millis: int = 10_000) -> bool:
        result = self.tracer_provider.force_flush(timeout_millis=timeout_millis)
        return bool(result)


_OPENAI_INSTRUMENTED = False


def configure_telemetry(
    settings: Settings,
    *,
    instrument_openai: bool = True,
    verbose: bool = False,
) -> Telemetry:
    """Register an OTLP exporter and return the OpenInference-aware tracer.

    ``PHOENIX_COLLECTOR_ENDPOINT`` is a Phoenix base URL. ``register`` appends
    the appropriate OTLP path for the chosen protocol.
    """

    provider = register(
        endpoint=settings.phoenix_collector_endpoint,
        project_name=settings.phoenix_project_name,
        batch=settings.phoenix_batch_export,
        protocol=settings.phoenix_protocol,
        verbose=verbose,
        api_key=settings.phoenix_api_key or None,
    )

    global _OPENAI_INSTRUMENTED
    if instrument_openai and not _OPENAI_INSTRUMENTED:
        redact = not settings.trace_content
        config = TraceConfig(
            hide_inputs=redact,
            hide_outputs=redact,
            hide_input_messages=redact,
            hide_output_messages=redact,
            hide_prompts=redact,
            hide_embeddings_text=redact,
            hide_embedding_vectors=True,
        )
        OpenAIInstrumentor().instrument(tracer_provider=provider, config=config)
        _OPENAI_INSTRUMENTED = True

    return Telemetry(provider, provider.get_tracer("phoenix_observability"))
