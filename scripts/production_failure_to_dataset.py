"""Convert a sanitized production failure into a reproducible local regression example."""

import json

from phoenix_observability.datasets import production_failure_to_example


def main() -> None:
    example = production_failure_to_example(
        trace_id="0123456789abcdef",
        query="Can I get a refund after 45 days?",
        bad_answer="Yes, refunds are available for 60 days.",
        retrieved_context=["Customers may request a refund within 30 calendar days."],
        reference_answer="No. The refund window is 30 calendar days.",
        root_cause="generation_hallucination",
    )
    print(json.dumps(example, indent=2))
    print("Review/redact the example before adding it to datasets/regression_dataset.json.")


if __name__ == "__main__":
    main()
