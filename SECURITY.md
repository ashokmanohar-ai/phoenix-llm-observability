# Security policy

Do not report credentials, customer prompts, trace payloads, or production records in a public issue.
Rotate any credential that may have been exposed and use GitHub's private vulnerability reporting.

This repository redacts trace content by default. Before production use, define PII redaction,
sampling, access control, retention, environment separation, encryption, and data-residency rules.
Never copy authorization headers or unreviewed production traces into an evaluation dataset.

