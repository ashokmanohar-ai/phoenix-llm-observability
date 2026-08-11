from __future__ import annotations

from phoenix_observability import telemetry as telemetry_module
from phoenix_observability.config import Settings


class FakeProvider:
    def __init__(self) -> None:
        self.tracer = object()

    def get_tracer(self, name: str):  # noqa: ANN201
        assert name == "phoenix_observability"
        return self.tracer

    def force_flush(self, *, timeout_millis: int) -> bool:
        return timeout_millis == 123


class FakeInstrumentor:
    calls: list[dict] = []

    def instrument(self, **kwargs) -> None:  # noqa: ANN003
        self.calls.append(kwargs)


def test_configure_telemetry_registers_exporter_and_instrumentor(monkeypatch) -> None:  # noqa: ANN001
    provider = FakeProvider()
    register_calls = []

    def fake_register(**kwargs):  # noqa: ANN003, ANN201
        register_calls.append(kwargs)
        return provider

    monkeypatch.setattr(telemetry_module, "register", fake_register)
    monkeypatch.setattr(telemetry_module, "OpenAIInstrumentor", FakeInstrumentor)
    monkeypatch.setattr(telemetry_module, "_OPENAI_INSTRUMENTED", False)
    result = telemetry_module.configure_telemetry(
        Settings(phoenix_api_key="secret", trace_content=False)
    )
    assert register_calls[0]["protocol"] == "http/protobuf"
    assert register_calls[0]["api_key"] == "secret"
    assert FakeInstrumentor.calls
    assert result.flush(timeout_millis=123)


def test_configure_telemetry_can_skip_openai(monkeypatch) -> None:  # noqa: ANN001
    provider = FakeProvider()
    monkeypatch.setattr(telemetry_module, "register", lambda **_: provider)
    monkeypatch.setattr(telemetry_module, "_OPENAI_INSTRUMENTED", False)
    result = telemetry_module.configure_telemetry(Settings(), instrument_openai=False)
    assert result.tracer is provider.tracer
