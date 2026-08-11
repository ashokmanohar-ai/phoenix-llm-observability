# Evaluation

Observability asks what happened. Evaluation asks whether the result was good. Phoenix connects
scores with trace context, enabling component-level diagnosis.

## Modern Phoenix Evals API

This repository targets `arize-phoenix-evals==3.4.0` and avoids legacy Q&A/RAG templates.

```python
from phoenix.evals.llm import LLM
from phoenix.evals.metrics import FaithfulnessEvaluator

judge = LLM(
    provider="azure",
    model=settings.azure_evaluator_deployment,
    api_key=settings.azure_api_key,
    api_version=settings.azure_api_version,
    azure_endpoint=settings.azure_endpoint,
)
faithfulness = FaithfulnessEvaluator(llm=judge, temperature=0.0)
scores = faithfulness.evaluate({
    "input": question,
    "output": answer,
    "context": context,
})
```

Each evaluator returns `Score` objects containing a numeric score, label, explanation, direction,
kind, and metadata. Do not compare scores without checking direction: Hallucination is minimized,
while Faithfulness is maximized.

## Metrics

### Faithfulness

Inputs: user question, generated answer, and retrieved context. A faithful answer contains no claim
unsupported by or contradictory to context. It does not prove the source itself is correct.

### Hallucination

Inputs: a role-labelled conversation/tool transcript and the latest output. Use it for multi-turn or
tool-using agents where grounding comes from more than one RAG context block.

### Document relevance

Inputs: query and one document. Evaluate documents separately, then analyze their distribution.
An average alone can conceal one highly relevant document among many noisy chunks.

### Answer relevance

The current pre-built list does not expose a generic answer-relevance evaluator, so the repository
defines a modern `ClassificationEvaluator` with relevant, partially relevant, and irrelevant labels.

### Correctness

Phoenix's built-in Correctness metric judges general factual accuracy using input and output. For
reference-answer comparison, this project defines a reference-aware `ClassificationEvaluator` with
correct, partially correct, and incorrect labels.

## Interpretation patterns

| Context relevance | Faithfulness | Answer relevance | Interpretation |
|---|---|---|---|
| Low | High | Low | Model faithfully used the wrong evidence; fix retrieval |
| High | Low | Any | Correct evidence was available; fix prompt/model grounding |
| High | High | Low | Correct evidence used, but question/instructions were mishandled |
| High | High | High | Inspect reference/source quality if humans still report an error |

## Offline and online evaluation

**Offline:** curated datasets before deployment for prompt/model/retriever comparison and regression.

**Online:** sampled production traces for emerging behavior. Run asynchronously where possible;
control cost and sampling; redact PII; validate evaluator latency; and attach results to the relevant
span/trace.

## Evaluator quality

An LLM judge is another model, not ground truth. Build a human-labelled calibration set, measure
agreement and category-level errors, keep temperature low, version judge deployment and rubric, and
review threshold changes. Use deterministic code evaluators for objective checks.

## Reports

`scripts/run_evaluation.py` computes averages, failure count, actual operational data when supplied,
and JSON/CSV outputs. Scores are never hard-coded as runtime results. Reports intentionally exclude
keys, headers, and raw environment data.

`examples/trace_evaluation.py` demonstrates logging the computed values back to a span through
Phoenix Client `add_span_annotation`. Experiments associate evaluator results with their task runs
automatically, which lets the UI show quality and trace execution together.
