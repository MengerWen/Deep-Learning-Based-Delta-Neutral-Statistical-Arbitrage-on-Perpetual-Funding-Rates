from __future__ import annotations

from funding_arb.cli import build_parser



def test_cli_parser_accepts_fetch_data_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["fetch-data"])
    assert args.command == "fetch-data"
    assert args.config.endswith("configs\\data\\default.yaml") or args.config.endswith("configs/data/default.yaml")



def test_cli_parser_accepts_train_dl_command_with_log_level() -> None:
    parser = build_parser()
    args = parser.parse_args(["train-dl", "--log-level", "DEBUG"])
    assert args.command == "train-dl"
    assert args.log_level == "DEBUG"