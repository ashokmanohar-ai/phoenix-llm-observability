# Production observability

## Deployment

Docker Compose is a local starter. Production Phoenix should use a version-pinned container,
PostgreSQL 14+, TLS, authentication/RBAC, durable storage, backups, health monitoring, resource
limits, and tested upgrades. Separate development, staging, production, and CI projects. Do not
expose a local Phoenix UI from CI.

## Sampling and retention

Trace enough traffic to represent use cases and failures without collecting everything blindly.
Consider head sampling for baseline traffic and targeted sampling for errors, low evaluations, new
versions, or important segments. Retention is a data-governance decision; the Compose sample uses 30
days only as a demonstrative default.

## Privacy and security

- Trace content is redacted by default.
- Never emit API keys, bearer tokens, cookies, authorization headers, passwords, or reset codes.
- Treat prompts, outputs, tool results, and retrieved documents as sensitive.
- Prefer document identifiers, scores, versions, and categories to full text.
- Apply PII detection/redaction before export, not only in the Phoenix UI.
- Enforce tenant authorization in the application and retrieval layer.
- Limit who can view, export, annotate, or convert traces to datasets.
- Review data residency, subprocessors, encryption, backups, and deletion requirements.

## Quality monitoring

Use a validated sample of production traces for online evaluation. Run judges asynchronously so
evaluation latency does not affect the user path. Budget evaluation calls separately, cap concurrency,
and monitor evaluator failures. Version the judge deployment, prompt/rubric, mapping, and score
direction. Periodically compare automated labels with human annotations.

## Operational monitoring

Monitor volume, trace export failures, dropped spans, ingestion lag, database/storage growth, Phoenix
health, request/error rate, latency distributions, token distributions, tool loops, and quality by
application version. An average can hide segment regressions, so break down results by safe metadata.

## Cost

Token attributes support application-side cost analysis. Do not assume one global price. Azure costs
depend on deployment/model, region, contract, token type, and date. Maintain a versioned price table,
calculate outside the instrumentor if necessary, label values as estimates, and reconcile with Azure
billing data.

## Release workflow

1. Instrument locally and inspect trace shape.
2. Build a representative, versioned dataset.
3. Calibrate evaluators against human review.
4. Compare baseline and candidate experiments.
5. Enforce agreed regression gates.
6. Deploy progressively and monitor sampled traces.
7. Convert new confirmed failures into permanent regression cases.

## Incident response

Preserve trace IDs and configuration versions, not secrets. Identify the failing component using span
and evaluation evidence. Check whether source data changed. Apply the smallest targeted fix. Rerun the
exact sanitized case and broader dataset. Document residual risk and remove incident-only elevated
trace content after the investigation.

