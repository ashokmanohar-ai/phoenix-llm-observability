"""Upload the local regression suite through Phoenix Client 3.x."""

from phoenix_observability.config import Settings
from phoenix_observability.datasets import upload_rag_dataset


def main() -> None:
    dataset = upload_rag_dataset(
        "datasets/regression_dataset.json",
        name="exampleco-rag-regression",
        settings=Settings.from_env(),
    )
    print(f"Uploaded dataset: {dataset.name} ({len(dataset)} examples)")


if __name__ == "__main__":
    main()
