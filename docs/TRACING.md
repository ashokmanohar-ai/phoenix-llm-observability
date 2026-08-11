# Tracing LLM applications

## OpenTelemetry in this project

OpenTelemetry defines traces, spans, attributes, events, status, exporters, and OTLP. Phoenix is the
collector and analysis UI. `phoenix.otel.register()` creates an OpenTelemetry tracer provider and an
OTLP exporter pointed at Phoenix.

- **Trace:** one complete request path.
- **Span:** one timed operation such as retrieval, embedding, LLM generation, or a tool call.
- **Attribute:** searchable context such as deployment, Top-K, or document ID.
- **Event:** a point-in-time occurrence; exceptions are recorded as events.
- **Status:** `OK`, `ERROR`, or unset.
- **Exporter:** sends completed spans to Phoenix.
- **OTLP:** the protocol used to transport telemetry.

`PHOENIX_PROTOCOL=http/protobuf` uses the Phoenix base URL on port 6006. `grpc` can use port 4317.

## OpenInference

OpenInference extends OpenTelemetry with AI semantics. Phoenix gives first-class rendering to
`openinference.span.kind` and attributes such as `llm.model_name`, `llm.token_count.total`,
`retrieval.documents`, `tool.json_schema`, `input.value`, and `output.value`.

Current kinds include `LLM`, `CHAIN`, `AGENT`, `TOOL`, `RETRIEVER`, `EMBEDDING`, `RERANKER`,
`GUARDRAIL`, and `EVALUATOR`. This repository uses the current OpenInference conventions for new
instrumentation rather than raw, unstable GenAI convention keys.

## Automatic instrumentation

`configure_telemetry()` registers Phoenix and instruments the OpenAI Python SDK:

```python
provider = register(
    endpoint=settings.phoenix_collector_endpoint,
    project_name=settings.phoenix_project_name,
    protocol="http/protobuf",
)
OpenAIInstrumentor().instrument(tracer_provider=provider, config=trace_config)
```

The instrumentor supports `AzureOpenAI` and emits spans for chat completions and embeddings. It
captures SDK-returned usage and actual duration. Instrument once at process startup, before SDK
calls.

## Manual instrumentation

Custom application logic needs manual spans:

```python
with tracer.start_as_current_span(
    "retrieval.lexical", openinference_span_kind="retriever"
) as span:
    span.set_attribute("retriever.top_k", top_k)
    results = search(query)
```

Use manual spans for proprietary retrieval, business rules, context assembly, agents, custom tools,
and multi-stage pipelines. Always set an OpenInference kind so Phoenix can render the span correctly.
Set root `input.value` and `output.value` if you want the Phoenix trace list to display them.

## Trace content and redaction

`PHOENIX_TRACE_CONTENT=false` configures OpenInference `TraceConfig` to hide inputs, outputs,
messages, prompts, and embedding text. Embedding vectors are always hidden. Manual spans follow the
same flag. Document IDs, scores, metadata, counts, and operational timings remain useful.

Do not trace API keys, authorization headers, passwords, reset codes, raw customer records, or hidden
chain-of-thought. Agent spans record observable orchestration decisions and tool activity, not private
reasoning.

## Errors

Every custom span catches exceptions only to record them, marks `ERROR`, and re-raises. The parent
trace therefore shows which component failed without concealing the application error. Azure SDK
timeouts, rate limits, and invalid requests are captured by automatic instrumentation.

## What to inspect

1. Root trace input/output and total duration.
2. Span tree and which child dominates duration.
3. Retriever query, document IDs/scores, result count, and errors.
4. Prompt version and context size.
5. Azure deployment, messages (when approved), token usage, and status.
6. Agent tool selection, repeated calls, and tool failures.
7. Evaluations or annotations associated with the relevant trace/span.

