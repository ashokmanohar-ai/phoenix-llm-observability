from __future__ import annotations

from openinference.instrumentation import OITracer, TraceConfig
from opentelemetry.sdk.trace import TracerProvider


def make_test_tracer() -> OITracer:
    provider = TracerProvider()
    return OITracer(provider.get_tracer("test"), TraceConfig())
