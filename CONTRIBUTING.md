# Contributing

1. Create a focused branch.
2. Install with `python -m pip install -e ".[dev]"`.
3. Run `ruff check .` and `pytest --cov=phoenix_observability`.
4. Add a sanitized regression case for every fixed LLM/RAG failure.
5. Explain any threshold or evaluator-prompt change in the pull request.

Do not commit `.env`, secrets, customer data, raw production traces, or generated evaluation reports.

