"""Generate intentionally broken traces for retrieval, prompt, and context debugging."""

from __future__ import annotations

import argparse

from phoenix_observability.azure_openai_client import AzureOpenAIService
from phoenix_observability.config import Settings
from phoenix_observability.rag_pipeline import RAGPipeline
from phoenix_observability.retriever import LexicalRetriever, SearchResult, load_documents
from phoenix_observability.telemetry import configure_telemetry


class BrokenRetriever:
    def __init__(self, result: SearchResult) -> None:
        self.result = result

    def search(self, query: str, *, top_k: int) -> list[SearchResult]:
        del query, top_k
        return [self.result]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "case",
        choices=["broken-retriever", "broken-prompt", "excessive-context", "missing-context"],
    )
    args = parser.parse_args()
    settings = Settings.from_env().validated(require_azure=True)
    telemetry = configure_telemetry(settings)
    llm = AzureOpenAIService(settings)
    documents = load_documents("knowledge_base/company_policies.json")
    retriever = LexicalRetriever(documents, telemetry.tracer, settings)
    prompt_version = "v2"
    top_k = settings.rag_top_k
    query = "What is the refund window?"

    if args.case == "broken-retriever":
        password = next(doc for doc in documents if doc.id == "policy-password-001")
        retriever = BrokenRetriever(SearchResult(password, 0.99))  # type: ignore[assignment]
    elif args.case == "broken-prompt":
        prompt_version = "v1"
    elif args.case == "excessive-context":
        top_k = len(documents)
    elif args.case == "missing-context":
        query = "Do you ship to the Moon?"

    pipeline = RAGPipeline(
        retriever,
        llm,
        telemetry.tracer,
        settings,
        prompt_version=prompt_version,
        top_k=top_k,
    )
    result = pipeline.answer(query, session_id=f"troubleshooting-{args.case}")
    telemetry.flush()
    print(result.answer)
    print("Retrieved:", result.document_ids)


if __name__ == "__main__":
    main()
