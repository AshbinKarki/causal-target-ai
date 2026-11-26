"""Cross-platform CLI for the reproducible ML lifecycle."""

import argparse
import json
from pathlib import Path

import pandas as pd

from causal_target.config import Config
from causal_target.data import download, ingest
from causal_target.inference import predict
from causal_target.monitoring import drift
from causal_target.utils import setup_logging


def main():
    parser = argparse.ArgumentParser(description="CausalTarget AI pipeline")
    parser.add_argument(
        "command", choices=["download", "process", "run", "train", "evaluate", "predict", "monitor"]
    )
    parser.add_argument("--profile", choices=["quick", "demo", "full"], default="demo")
    parser.add_argument("--source", choices=["criteo", "synthetic"], default="criteo")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--model", type=Path, default=Path("artifacts/models.joblib"))
    args = parser.parse_args()
    setup_logging()
    cfg = Config.read(args.root / "configs" / f"{args.profile}.yaml")
    if args.command == "download":
        print(download(args.root))
    elif args.command == "process":
        print(ingest(args.root, cfg, download(args.root)))
    elif args.command in {"run", "train"}:
        from causal_target.pipeline import run

        # Synthetic tests default to a separate output tree, preserving real reports.
        output = args.output or (
            args.root / "reports/runs/synthetic" if args.source == "synthetic" else args.root
        )
        print(json.dumps(run(args.root, cfg, args.source, output), indent=2))
    elif args.command == "evaluate":
        folder = (args.output or args.root) / "reports/metrics"
        for name in ["predictive_test.csv", "causal_test.csv", "strategies.csv"]:
            print(pd.read_csv(folder / name).to_string(index=False))
    elif args.command == "predict":
        if not args.input or not args.output:
            parser.error("predict requires --input and --output")
        print(predict(args.input, args.model, args.output).head().to_string(index=False))
    elif args.command == "monitor":
        if not args.input or not args.reference or not args.output:
            parser.error("monitor requires --input, --reference and --output")
        drift(pd.read_parquet(args.reference), pd.read_parquet(args.input)).to_csv(
            args.output, index=False
        )


if __name__ == "__main__":
    main()
