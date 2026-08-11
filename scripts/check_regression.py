"""Compare two computed Phoenix evaluation reports and fail on excessive metric drops."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_averages(path: str) -> dict[str, float]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {name: float(value) for name, value in payload["summary"]["averages"].items()}


def regressions(
    baseline: dict[str, float], candidate: dict[str, float], max_drop: float
) -> list[str]:
    return [
        f"{name}: baseline={value:.3f}, candidate={candidate.get(name, 0.0):.3f}, "
        f"drop={value - candidate.get(name, 0.0):.3f}"
        for name, value in baseline.items()
        if value - candidate.get(name, 0.0) > max_drop
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--max-drop", type=float, default=0.05)
    args = parser.parse_args()
    failures = regressions(
        load_averages(args.baseline), load_averages(args.candidate), args.max_drop
    )
    if failures:
        print("Regression gate failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Regression gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
