"""Unified CLI command wiring for the Python-side pipeline."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from funding_arb.backtest.engine import describe_backtest_job
from funding_arb.config.loader import COMMAND_SETTINGS, load_command_settings
from funding_arb.data.pipeline import describe_ingestion_job
from funding_arb.features.pipeline import describe_feature_job
from funding_arb.labels.generator import describe_labeling_assumption
from funding_arb.models.baselines import describe_baseline_job
from funding_arb.models.deep_learning import describe_deep_learning_job
from funding_arb.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)



def _log_config_summary(command_name: str, config_path: Path, config: Any) -> None:
    LOGGER.info("Command: %s", command_name)
    LOGGER.info("Config path: %s", config_path)
    LOGGER.info("Config model: %s", type(config).__name__)



def _run_fetch_data(config: Any, config_path: Path) -> int:
    _log_config_summary("fetch-data", config_path, config)
    LOGGER.info(describe_ingestion_job(config.model_dump()))
    return 0



def _run_build_features(config: Any, config_path: Path) -> int:
    payload = config.model_dump()
    _log_config_summary("build-features", config_path, config)
    LOGGER.info(describe_feature_job(payload))
    LOGGER.info(describe_labeling_assumption(payload))
    return 0



def _run_train_baseline(config: Any, config_path: Path) -> int:
    _log_config_summary("train-baseline", config_path, config)
    LOGGER.info(describe_baseline_job(config.model_dump()))
    return 0



def _run_train_dl(config: Any, config_path: Path) -> int:
    _log_config_summary("train-dl", config_path, config)
    LOGGER.info(describe_deep_learning_job(config.model_dump()))
    return 0



def _run_backtest(config: Any, config_path: Path) -> int:
    _log_config_summary("backtest", config_path, config)
    LOGGER.info(describe_backtest_job(config.model_dump()))
    return 0


COMMAND_HANDLERS: dict[str, Callable[[Any, Path], int]] = {
    "fetch-data": _run_fetch_data,
    "build-features": _run_build_features,
    "train-baseline": _run_train_baseline,
    "train-dl": _run_train_dl,
    "backtest": _run_backtest,
}



def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(description="Funding-rate arbitrage project CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command_name, settings in COMMAND_SETTINGS.items():
        help_text = f"Run the {command_name} pipeline stage."
        subparser = subparsers.add_parser(command_name, help=help_text, description=help_text)
        subparser.add_argument(
            "--config",
            default=str(settings.default_config_path),
            help=f"Path to config file. Defaults to {settings.default_config_path}.",
        )
        subparser.add_argument("--log-level", default="INFO", help="Logging level, e.g. INFO or DEBUG.")
    return parser



def run_command(command_name: str, config_path: str | Path, log_level: str = "INFO") -> int:
    """Run a named CLI command with the provided config path."""
    configure_logging(log_level)
    resolved_path = Path(config_path)
    config = load_command_settings(command_name, resolved_path)
    handler = COMMAND_HANDLERS[command_name]
    return handler(config, resolved_path)



def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the unified Python CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_command(args.command, args.config, args.log_level)