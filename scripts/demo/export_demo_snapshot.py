"""CLI entry point for exporting a future demo snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from funding_arb.utils.config import load_yaml_config



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export demo artifacts for the frontend.")
    parser.add_argument("--config", required=True, help="Path to a YAML config file.")
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    config = load_yaml_config(args.config)
    title = config.get("demo", {}).get("title", "Funding-Rate Arbitrage Prototype Dashboard")
    artifact_dir = config.get("demo", {}).get("artifact_dir", "data/artifacts/demo")
    print(f"Demo scaffold ready for '{title}' with artifact directory '{artifact_dir}'.")
    return 0



if __name__ == "__main__":
    raise SystemExit(main())