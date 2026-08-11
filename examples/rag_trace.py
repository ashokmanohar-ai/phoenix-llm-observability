"""Run the fictional company-policy RAG pipeline as one end-to-end trace."""

from phoenix_observability.bootstrap import build_demo_rag
from phoenix_observability.config import Settings


def main() -> None:
    settings = Settings.from_env().validated(require_azure=True)
    pipeline, telemetry, _, _ = build_demo_rag(settings)
    result = pipeline.answer("How do I cancel my subscription?")
    telemetry.flush()
    print(result.answer)
    print("Documents:", ", ".join(result.document_ids) or "none")
    print("Tokens:", result.usage.total_tokens)
    print(f"Inspect the trace at {settings.phoenix_endpoint}")


if __name__ == "__main__":
    main()
