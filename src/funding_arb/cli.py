"""Unified CLI command wiring for the Python-side pipeline."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from funding_arb.backtest.engine import describe_backtest_job
from funding_arb.config.loader import COMMAND_SETTINGS, load_command_settings
from funding_arb.data.pipeline import describe_ingestion_job, run_data_pipeline
from funding_arb.features.pipeline import describe_feature_job, run_feature_pipeline
from funding_arb.labels.generator import describe_labeling_assumption
from funding_arb.labels.pipeline import describe_supervised_dataset_job, run_label_pipeline
from funding_arb.models.baselines import (
    describe_baseline_evaluation_job,
    describe_baseline_job,
    run_baseline_pipeline,
)
from funding_arb.models.deep_learning import describe_deep_learning_job, run_deep_learning_pipeline
from funding_arb.reporting.data_quality import describe_data_quality_job, run_data_quality_report
from funding_arb.signals.pipeline import describe_signal_job, run_signal_generation
from funding_arb.utils.logging import configure_logging

LOGGER = logging.getLogger(__name__)



def _log_config_summary(command_name: str, config_path: Path, config: Any) -> None:
    LOGGER.info("Command: %s", command_name)
    LOGGER.info("Config path: %s", config_path)
    LOGGER.info("Config model: %s", type(config).__name__)



def _run_fetch_data(config: Any, config_path: Path) -> int:
    _log_config_summary("fetch-data", config_path, config)
    LOGGER.info(describe_ingestion_job(config))
    artifacts = run_data_pipeline(config)
    LOGGER.info("Raw outputs: %s", ", ".join(artifacts.raw_files))
    LOGGER.info("Interim outputs: %s", ", ".join(artifacts.interim_files))
    LOGGER.info("Processed outputs: %s", ", ".join(artifacts.processed_files))
    LOGGER.info("Manifest: %s", artifacts.manifest_path)
    return 0



def _run_report_data_quality(config: Any, config_path: Path) -> int:
    _log_config_summary("report-data-quality", config_path, config)
    LOGGER.info(describe_data_quality_job(config))
    artifacts = run_data_quality_report(config)
    LOGGER.info("Report tables: %s", ", ".join(artifacts.table_paths))
    LOGGER.info("Report figures: %s", ", ".join(artifacts.figure_paths))
    if artifacts.summary_json_path is not None:
        LOGGER.info("Summary JSON: %s", artifacts.summary_json_path)
    if artifacts.markdown_report_path is not None:
        LOGGER.info("Markdown report: %s", artifacts.markdown_report_path)
    return 0



def _run_build_features(config: Any, config_path: Path) -> int:
    _log_config_summary("build-features", config_path, config)
    LOGGER.info(describe_feature_job(config))
    LOGGER.info(describe_labeling_assumption(config.model_dump()))
    artifacts = run_feature_pipeline(config)
    LOGGER.info("Feature table: %s", artifacts.feature_table_path)
    if artifacts.feature_table_csv_path is not None:
        LOGGER.info("Feature table CSV: %s", artifacts.feature_table_csv_path)
    LOGGER.info("Feature manifest: %s", artifacts.manifest_path)
    return 0



def _run_build_labels(config: Any, config_path: Path) -> int:
    _log_config_summary("build-labels", config_path, config)
    LOGGER.info(describe_supervised_dataset_job(config))
    LOGGER.info(describe_labeling_assumption(config.model_dump()))
    artifacts = run_label_pipeline(config)
    LOGGER.info("Supervised dataset: %s", artifacts.supervised_dataset_path)
    if artifacts.supervised_dataset_csv_path is not None:
        LOGGER.info("Supervised dataset CSV: %s", artifacts.supervised_dataset_csv_path)
    LOGGER.info("Label table: %s", artifacts.label_table_path)
    if artifacts.label_table_csv_path is not None:
        LOGGER.info("Label table CSV: %s", artifacts.label_table_csv_path)
    if artifacts.split_paths:
        LOGGER.info("Split datasets: %s", ", ".join(f"{name}={path}" for name, path in artifacts.split_paths.items()))
    LOGGER.info("Supervised manifest: %s", artifacts.manifest_path)
    return 0



def _run_train_baseline(config: Any, config_path: Path) -> int:
    _log_config_summary("train-baseline", config_path, config)
    LOGGER.info(describe_baseline_job(config))
    artifacts = run_baseline_pipeline(config, train_models=True)
    LOGGER.info("Predictions: %s", artifacts.predictions_path)
    if artifacts.predictions_csv_path is not None:
        LOGGER.info("Predictions CSV: %s", artifacts.predictions_csv_path)
    LOGGER.info("Metrics: %s", artifacts.metrics_path)
    if artifacts.metrics_csv_path is not None:
        LOGGER.info("Metrics CSV: %s", artifacts.metrics_csv_path)
    LOGGER.info("Leaderboard: %s", artifacts.leaderboard_path)
    if artifacts.leaderboard_csv_path is not None:
        LOGGER.info("Leaderboard CSV: %s", artifacts.leaderboard_csv_path)
    if artifacts.report_path is not None:
        LOGGER.info("Markdown report: %s", artifacts.report_path)
    LOGGER.info("Feature columns: %s", artifacts.feature_columns_path)
    LOGGER.info("Model manifest: %s", artifacts.manifest_path)
    if artifacts.model_paths:
        LOGGER.info("Model artifacts: %s", ", ".join(f"{name}={path}" for name, path in artifacts.model_paths.items()))
    if artifacts.diagnostic_paths:
        LOGGER.info("Diagnostics: %s", ", ".join(f"{name}={path}" for name, path in artifacts.diagnostic_paths.items()))
    return 0



def _run_evaluate_baseline(config: Any, config_path: Path) -> int:
    _log_config_summary("evaluate-baseline", config_path, config)
    LOGGER.info(describe_baseline_evaluation_job(config))
    artifacts = run_baseline_pipeline(config, train_models=False)
    LOGGER.info("Predictions: %s", artifacts.predictions_path)
    if artifacts.predictions_csv_path is not None:
        LOGGER.info("Predictions CSV: %s", artifacts.predictions_csv_path)
    LOGGER.info("Metrics: %s", artifacts.metrics_path)
    if artifacts.metrics_csv_path is not None:
        LOGGER.info("Metrics CSV: %s", artifacts.metrics_csv_path)
    LOGGER.info("Leaderboard: %s", artifacts.leaderboard_path)
    if artifacts.leaderboard_csv_path is not None:
        LOGGER.info("Leaderboard CSV: %s", artifacts.leaderboard_csv_path)
    if artifacts.report_path is not None:
        LOGGER.info("Markdown report: %s", artifacts.report_path)
    LOGGER.info("Feature columns: %s", artifacts.feature_columns_path)
    LOGGER.info("Model manifest: %s", artifacts.manifest_path)
    return 0



def _run_train_dl(config: Any, config_path: Path) -> int:
    _log_config_summary("train-dl", config_path, config)
    LOGGER.info(describe_deep_learning_job(config))
    artifacts = run_deep_learning_pipeline(config)
    LOGGER.info("Checkpoint: %s", artifacts.checkpoint_path)
    LOGGER.info("Training history: %s", artifacts.history_path)
    LOGGER.info("Predictions: %s", artifacts.predictions_path)
    if artifacts.predictions_csv_path is not None:
        LOGGER.info("Predictions CSV: %s", artifacts.predictions_csv_path)
    LOGGER.info("Metrics: %s", artifacts.metrics_path)
    if artifacts.metrics_csv_path is not None:
        LOGGER.info("Metrics CSV: %s", artifacts.metrics_csv_path)
    LOGGER.info("Leaderboard: %s", artifacts.leaderboard_path)
    if artifacts.leaderboard_csv_path is not None:
        LOGGER.info("Leaderboard CSV: %s", artifacts.leaderboard_csv_path)
    if artifacts.report_path is not None:
        LOGGER.info("Markdown report: %s", artifacts.report_path)
    LOGGER.info("Feature columns: %s", artifacts.feature_columns_path)
    LOGGER.info("Normalization stats: %s", artifacts.normalization_path)
    LOGGER.info("Experiment manifest: %s", artifacts.manifest_path)
    return 0



def _run_generate_signals(config: Any, config_path: Path) -> int:
    _log_config_summary("generate-signals", config_path, config)
    LOGGER.info(describe_signal_job(config))
    artifacts = run_signal_generation(config)
    LOGGER.info("Signals: %s", artifacts.signals_path)
    if artifacts.signals_csv_path is not None:
        LOGGER.info("Signals CSV: %s", artifacts.signals_csv_path)
    LOGGER.info("Signal manifest: %s", artifacts.manifest_path)
    return 0



def _run_backtest(config: Any, config_path: Path) -> int:
    _log_config_summary("backtest", config_path, config)
    LOGGER.info(describe_backtest_job(config.model_dump()))
    return 0


COMMAND_HANDLERS: dict[str, Callable[[Any, Path], int]] = {
    "fetch-data": _run_fetch_data,
    "report-data-quality": _run_report_data_quality,
    "build-features": _run_build_features,
    "build-labels": _run_build_labels,
    "train-baseline": _run_train_baseline,
    "evaluate-baseline": _run_evaluate_baseline,
    "train-dl": _run_train_dl,
    "generate-signals": _run_generate_signals,
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
        if command_name == "generate-signals":
            subparser.add_argument(
                "--source",
                default=None,
                help="Optional source override, e.g. baseline, rules, baseline-ml, or dl.",
            )
    return parser



def run_command(
    command_name: str,
    config_path: str | Path,
    log_level: str = "INFO",
    source_override: str | None = None,
) -> int:
    """Run a named CLI command with the provided config path."""
    configure_logging(log_level)
    resolved_path = Path(config_path)
    config = load_command_settings(command_name, resolved_path)
    if source_override is not None and hasattr(config, "source"):
        config.source.name = source_override
    handler = COMMAND_HANDLERS[command_name]
    return handler(config, resolved_path)



def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the unified Python CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_command(
        args.command,
        args.config,
        args.log_level,
        source_override=getattr(args, "source", None),
    )
