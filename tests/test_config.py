from __future__ import annotations

import pytest

from phoenix_observability.config import Settings


def test_safe_summary_never_returns_secrets() -> None:
    settings = Settings(azure_api_key="super-secret", phoenix_api_key="also-secret")
    summary = settings.safe_summary()
    assert "super-secret" not in str(summary)
    assert "also-secret" not in str(summary)
    assert "azure_api_key" not in summary


def test_require_azure_reports_missing_variable_names() -> None:
    with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY"):
        Settings().validated(require_azure=True)


def test_validation_rejects_bad_retriever_mode() -> None:
    with pytest.raises(ValueError, match="RAG_RETRIEVER_MODE"):
        Settings(retriever_mode="unknown").validated()
