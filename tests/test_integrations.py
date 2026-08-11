from __future__ import annotations

from types import SimpleNamespace

from phoenix_observability import bootstrap, datasets, experiments
from phoenix_observability.config import Settings


class FakeDatasets:
    def __init__(self) -> None:
        self.created = None

    def create_dataset(self, **kwargs):  # noqa: ANN003, ANN201
        self.created = kwargs
        return SimpleNamespace(name=kwargs["name"])

    def get_dataset(self, *, dataset: str):  # noqa: ANN201
        return {"name": dataset}


class FakeExperiments:
    def run_experiment(self, **kwargs):  # noqa: ANN003, ANN201
        return kwargs


class FakeClient:
    instance = None

    def __init__(self, **kwargs) -> None:  # noqa: ANN003
        self.configuration = kwargs
        self.datasets = FakeDatasets()
        self.experiments = FakeExperiments()
        FakeClient.instance = self


def test_dataset_upload_uses_current_client_shape(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(datasets, "Client", FakeClient)
    result = datasets.upload_rag_dataset(
        "datasets/regression_dataset.json",
        name="regression",
        settings=Settings(),
    )
    assert result.name == "regression"
    assert len(FakeClient.instance.datasets.created["inputs"]) == 5


def test_experiment_records_configuration_metadata(monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(experiments, "Client", FakeClient)
    result = experiments.run_rag_experiment(
        dataset_name="regression",
        task=lambda input: input,
        evaluators=[],
        experiment_name="candidate",
        settings=Settings(),
        metadata={"top_k": 3},
        dry_run=1,
    )
    assert result["experiment_name"] == "candidate"
    assert result["experiment_metadata"] == {"top_k": 3}


def test_bootstrap_wires_pipeline_without_network(monkeypatch) -> None:  # noqa: ANN001
    fake_telemetry = SimpleNamespace(tracer=object())
    fake_llm = object()
    fake_retriever = object()
    monkeypatch.setattr(bootstrap, "configure_telemetry", lambda settings: fake_telemetry)
    monkeypatch.setattr(bootstrap, "AzureOpenAIService", lambda settings: fake_llm)
    monkeypatch.setattr(bootstrap, "load_documents", lambda path: ["doc"])
    monkeypatch.setattr(
        bootstrap,
        "create_retriever",
        lambda documents, tracer, settings, llm: fake_retriever,
    )
    pipeline, telemetry, llm, retriever = bootstrap.build_demo_rag(Settings())
    assert pipeline.llm is fake_llm
    assert telemetry is fake_telemetry
    assert llm is fake_llm
    assert retriever is fake_retriever
