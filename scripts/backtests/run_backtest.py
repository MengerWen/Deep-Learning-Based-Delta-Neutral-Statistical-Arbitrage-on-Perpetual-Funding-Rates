"""CLI entry point for the backtest scaffold."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from funding_arb.backtest.engine import describe_backtest_job
from funding_arb.utils.config import load_yaml_config



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a delta-neutral backtest.")
    parser.add_argument("--config", required=True, help="Path to a YAML config file.")
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    config = load_yaml_config(args.config)
    print(describe_backtest_job(config))
    return 0



if __name__ == "__main__":
    raise SystemExit(main())