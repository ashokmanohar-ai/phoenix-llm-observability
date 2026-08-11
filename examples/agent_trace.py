"""Trace an agent, selected tool, tool result, Azure LLM call, and final answer."""

from phoenix_observability.agent import SupportAgent
from phoenix_observability.bootstrap import build_demo_rag
from phoenix_observability.config import Settings


def main() -> None:
    settings = Settings.from_env().validated(require_azure=True)
    _, telemetry, llm, retriever = build_demo_rag(settings)
    agent = SupportAgent(
        retriever=retriever,
        llm=llm,
        tracer=telemetry.tracer,
        settings=settings,
    )
    print(agent.run("Where can I cancel my subscription?"))
    telemetry.flush()
    print(f"Inspect agent and tool spans at {settings.phoenix_endpoint}")


if __name__ == "__main__":
    main()
