"""Run current Phoenix LLM evaluators against a good and a bad RAG answer."""

from phoenix_observability.config import Settings
from phoenix_observability.evaluation.evaluator import PhoenixRAGEvaluator
from phoenix_observability.telemetry import configure_telemetry


def main() -> None:
    settings = Settings.from_env().validated(require_azure=True)
    telemetry = configure_telemetry(settings)
    evaluator = PhoenixRAGEvaluator(settings)
    cases = [
        {
            "id": "faithful",
            "query": "What is the refund window?",
            "retrieved_context": ["Customers may request a refund within 30 days."],
            "generated_answer": "Customers may request a refund within 30 days.",
            "reference_answer": "Customers may request a refund within 30 days.",
        },
        {
            "id": "unfaithful",
            "query": "What is the refund window?",
            "retrieved_context": ["Customers may request a refund within 30 days."],
            "generated_answer": "Customers may request a refund within 60 days.",
            "reference_answer": "Customers may request a refund within 30 days.",
        },
    ]
    for case in cases:
        result = evaluator.evaluate_case(case)
        print(result.to_dict())
    telemetry.flush()


if __name__ == "__main__":
    main()
