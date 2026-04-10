from __future__ import annotations

from funding_arb.cli import build_parser



def test_cli_parser_accepts_fetch_data_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["fetch-data"])
    assert args.command == "fetch-data"
    assert args.config.endswith("configs\\data\\default.yaml") or args.config.endswith("configs/data/default.yaml")



def test_cli_parser_accepts_report_data_quality_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["report-data-quality"])
    assert args.command == "report-data-quality"
    assert args.config.endswith("configs\\reports\\data_quality.yaml") or args.config.endswith("configs/reports/data_quality.yaml")



def test_cli_parser_accepts_build_labels_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["build-labels"])
    assert args.command == "build-labels"
    assert args.config.endswith("configs\\labels\\default.yaml") or args.config.endswith("configs/labels/default.yaml")



def test_cli_parser_accepts_generate_signals_with_source_override() -> None:
    parser = build_parser()
    args = parser.parse_args(["generate-signals", "--source", "dl"])
    assert args.command == "generate-signals"
    assert args.source == "dl"
    assert args.config.endswith("configs\\signals\\default.yaml") or args.config.endswith("configs/signals/default.yaml")



def test_cli_parser_accepts_evaluate_baseline_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["evaluate-baseline"])
    assert args.command == "evaluate-baseline"
    assert args.config.endswith("configs\\models\\baseline.yaml") or args.config.endswith("configs/models/baseline.yaml")



def test_cli_parser_accepts_backtest_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["backtest"])
    assert args.command == "backtest"
    assert args.config.endswith("configs\\backtests\\default.yaml") or args.config.endswith("configs/backtests/default.yaml")


def test_cli_parser_accepts_train_dl_command_with_log_level() -> None:
    parser = build_parser()
    args = parser.parse_args(["train-dl", "--log-level", "DEBUG"])
    assert args.command == "train-dl"
    assert args.log_level == "DEBUG"
