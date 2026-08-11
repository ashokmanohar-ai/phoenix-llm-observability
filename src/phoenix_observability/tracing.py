"""Small tracing utilities shared by custom application components."""

from __future__ import annotations

import json
from typing import Any

from opentelemetry.trace import Status, StatusCode
from phoenix.otel import OpenInferenceMimeTypeValues, SpanAttributes


def set_span_input(span: Any, value: Any, *, visible: bool) -> None:
    payload = value if visible else "[REDACTED]"
    span.set_attribute(SpanAttributes.INPUT_VALUE, _serialize(payload))
    span.set_attribute(SpanAttributes.INPUT_MIME_TYPE, _mime(value))


def set_span_output(span: Any, value: Any, *, visible: bool) -> None:
    payload = value if visible else "[REDACTED]"
    span.set_attribute(SpanAttributes.OUTPUT_VALUE, _serialize(payload))
    span.set_attribute(SpanAttributes.OUTPUT_MIME_TYPE, _mime(value))


def mark_ok(span: Any) -> None:
    span.set_status(Status(StatusCode.OK))


def mark_error(span: Any, exc: BaseException) -> None:
    span.record_exception(exc)
    span.set_status(Status(StatusCode.ERROR, str(exc)))


def _serialize(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, default=str, ensure_ascii=False)


def _mime(value: Any) -> str:
    if isinstance(value, str):
        return OpenInferenceMimeTypeValues.TEXT.value
    return OpenInferenceMimeTypeValues.JSON.value
