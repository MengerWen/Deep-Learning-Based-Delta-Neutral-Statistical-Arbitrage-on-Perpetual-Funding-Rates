"""CLI entry point for the market-data ingestion scaffold."""

from __future__ import annotations

import argparse

from funding_arb.data.pipeline import describe_ingestion_job
from funding_arb.utils.config import load_yaml_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch market data for the research pipeline.")
    parser.add_argument("--config", required=True, help="Path to a YAML config file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml_config(args.config)
    print(describe_ingestion_job(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

