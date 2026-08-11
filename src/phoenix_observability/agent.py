"""Lightweight traced agent with deterministic tool selection and Azure final answer."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from openinference.semconv.trace import ToolAttributes

from phoenix_observability.config import Settings
from phoenix_observability.llm_service import CompletionService
from phoenix_observability.retriever import Retriever
from phoenix_observability.tracing import mark_error, mark_ok, set_span_input, set_span_output


class SupportAgent:
    def __init__(
        self,
        *,
        retriever: Retriever,
        llm: CompletionService,
        tracer: Any,
        settings: Settings,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.tracer = tracer
        self.settings = settings
        self.tools: dict[str, Callable[[str], str]] = {
            "search_policy": self._search_policy,
            "account_status": self._account_status,
            "billing_policy": self._billing_policy,
        }

    def run(self, query: str) -> str:
        with self.tracer.start_as_current_span(
            "agent_request", openinference_span_kind="agent"
        ) as span:
            set_span_input(span, query, visible=self.settings.trace_content)
            try:
                tool_name = self._select_tool(query)
                span.set_attribute("agent.name", "exampleco-support-agent")
                span.set_attribute("agent.selected_tool", tool_name)
                tool_result = self._call_tool(tool_name, query)
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Answer only from the tool result. If the tool failed, say so clearly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question: {query}\nTool ({tool_name}) result: {tool_result}",
                    },
                ]
                answer = self.llm.complete(messages).text
                set_span_output(span, answer, visible=self.settings.trace_content)
                mark_ok(span)
                return answer
            except Exception as exc:
                mark_error(span, exc)
                raise

    def _select_tool(self, query: str) -> str:
        lowered = query.lower()
        if any(word in lowered for word in ("account", "active", "suspended")):
            return "account_status"
        if any(word in lowered for word in ("bill", "invoice", "subscription", "cancel")):
            return "billing_policy"
        return "search_policy"

    def _call_tool(self, name: str, argument: str) -> str:
        schema = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }
        with self.tracer.start_as_current_span(
            f"tool.{name}", openinference_span_kind="tool"
        ) as span:
            span.set_attribute(ToolAttributes.TOOL_JSON_SCHEMA, json.dumps(schema))
            set_span_input(span, {"query": argument}, visible=self.settings.trace_content)
            try:
                result = self.tools[name](argument)
                set_span_output(span, result, visible=self.settings.trace_content)
                mark_ok(span)
                return result
            except Exception as exc:
                mark_error(span, exc)
                raise

    def _search_policy(self, query: str) -> str:
        results = self.retriever.search(query, top_k=2)
        return "\n".join(f"[{item.document.id}] {item.document.text}" for item in results)

    @staticmethod
    def _account_status(_: str) -> str:
        return "Fictional demo account DEMO-001 is active. No real customer data was accessed."

    def _billing_policy(self, query: str) -> str:
        return self._search_policy(query)
