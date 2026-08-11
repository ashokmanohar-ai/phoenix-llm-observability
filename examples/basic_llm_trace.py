"""Send one Azure OpenAI request and inspect the root + auto-instrumented LLM span."""

from phoenix.otel import using_attributes

from phoenix_observability.azure_openai_client import AzureOpenAIService
from phoenix_observability.config import Settings
from phoenix_observability.telemetry import configure_telemetry
from phoenix_observability.tracing import mark_error, mark_ok, set_span_input, set_span_output


def main() -> None:
    settings = Settings.from_env().validated(require_azure=True)
    telemetry = configure_telemetry(settings)
    llm = AzureOpenAIService(settings)
    question = "Explain what retrieval-augmented generation is."

    with (
        using_attributes(
            session_id="basic-trace-demo",
            user_id="demo-user",
            tags=["llm", "azure-openai", "fictional-data"],
            metadata={"example": "basic_llm_trace"},
        ),
        telemetry.tracer.start_as_current_span(
            "llm_request", openinference_span_kind="chain"
        ) as span,
    ):
        set_span_input(span, question, visible=settings.trace_content)
        try:
            response = llm.complete(
                [
                    {
                        "role": "system",
                        "content": "Explain technical concepts accurately and concisely.",
                    },
                    {"role": "user", "content": question},
                ]
            )
            span.set_attribute("app.llm_latency_seconds", response.latency_seconds)
            span.set_attribute("app.token_count.total", response.usage.total_tokens)
            set_span_output(span, response.text, visible=settings.trace_content)
            mark_ok(span)
            print(response.text)
        except Exception as exc:
            mark_error(span, exc)
            raise
    telemetry.flush()
    print(f"Phoenix UI: {settings.phoenix_endpoint}")


if __name__ == "__main__":
    main()
