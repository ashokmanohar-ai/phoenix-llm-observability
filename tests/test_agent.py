from __future__ import annotations

import pytest
from conftest import make_test_tracer

from phoenix_observability.agent import SupportAgent
from phoenix_observability.azure_openai_client import LLMResponse, Usage
from phoenix_observability.config import Settings
from phoenix_observability.retriever import Document, SearchResult


class FakeRetriever:
    def search(self, query: str, *, top_k: int) -> list[SearchResult]:
        del query, top_k
        return [
            SearchResult(
                Document(
                    "policy-cancel-001",
                    "Cancellation",
                    "Cancel from Settings > Billing.",
                    {},
                ),
                0.9,
            )
        ]


class FakeLLM:
    def complete(self, messages, **kwargs):  # noqa: ANN001, ANN003, ANN201
        del kwargs
        return LLMResponse(
            text=messages[-1]["content"],
            deployment="fake",
            latency_seconds=0.01,
            usage=Usage(),
        )


def make_agent() -> SupportAgent:
    return SupportAgent(
        retriever=FakeRetriever(),
        llm=FakeLLM(),
        tracer=make_test_tracer(),
        settings=Settings(trace_content=True),
    )


def test_agent_traces_billing_tool_and_final_answer() -> None:
    answer = make_agent().run("Where do I cancel my subscription?")
    assert "Settings > Billing" in answer
    assert "billing_policy" in answer


def test_agent_routes_account_status_without_real_customer_data() -> None:
    answer = make_agent().run("Is my account active?")
    assert "DEMO-001 is active" in answer


def test_tool_failure_is_recorded_and_propagated() -> None:
    agent = make_agent()

    def fail(_: str) -> str:
        raise RuntimeError("tool unavailable")

    agent.tools["search_policy"] = fail
    with pytest.raises(RuntimeError, match="tool unavailable"):
        agent.run("Tell me about returns")
