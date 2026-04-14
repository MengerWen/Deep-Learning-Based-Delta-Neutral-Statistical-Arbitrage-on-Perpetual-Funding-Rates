from __future__ import annotations

from pathlib import Path

from funding_arb.config.loader import get_command_settings, load_command_settings, load_settings
from funding_arb.config.models import (
    BacktestSettings,
    BaselineSettings,
    DataQualityReportSettings,
    DataSettings,
    DemoWorkflowSettings,
    DeepLearningSettings,
    FeatureSettings,
    IntegrationSettings,
    LabelPipelineSettings,
    RobustnessReportSettings,
    SignalSettings,
)


def test_fetch_data_default_config_loads_typed_model() -> None:
    config = load_command_settings("fetch-data")
    assert isinstance(config, DataSettings)
    assert config.dataset.symbol == "BTCUSDT"
    assert config.source.provider == "binance"
    assert config.sources["funding"].enabled is True


def test_report_data_quality_default_config_loads_typed_model() -> None:
    config = load_command_settings("report-data-quality")
    assert isinstance(config, DataQualityReportSettings)
    assert config.input.symbol == "BTCUSDT"
    assert config.output.output_dir == "reports/data_quality"


def test_build_features_default_config_loads_typed_model() -> None:
    config = load_command_settings("build-features")
    assert isinstance(config, FeatureSettings)
    assert config.input.dataset_path.endswith("hourly_market_data.parquet")
    assert config.feature_set.rolling_windows == [8, 24, 72, 168]
    assert config.labels.forward_horizon_hours == 8


def test_build_labels_default_config_loads_typed_model() -> None:
    config = load_command_settings("build-labels")
    assert isinstance(config, LabelPipelineSettings)
    assert config.input.feature_table_path.endswith("btcusdt_feature_set.parquet")
    assert config.target.holding_windows_hours == [8, 24]
    assert config.target.primary_horizon_hours == 8


def test_train_baseline_default_config_loads_typed_model() -> None:
    config = load_command_settings("train-baseline")
    assert isinstance(config, BaselineSettings)
    assert config.input.dataset_path.endswith("btcusdt_supervised_dataset.parquet")
    assert config.target.classification_column == "target_is_profitable_24h"
    assert config.predictive.classification.enabled is True
    assert config.tuning.gap == 24
    assert config.threshold_search.objective == "avg_signal_return_bps"
    assert config.imputation.add_missing_indicators is True
    assert len(config.predictive.classification.additional_models) >= 2
    assert config.predictive.classification.calibration_method == "sigmoid"
    assert len(config.rules) >= 1


def test_train_dl_default_config_loads_typed_model() -> None:
    config = load_command_settings("train-dl")
    assert isinstance(config, DeepLearningSettings)
    assert config.input.dataset_path.endswith("btcusdt_supervised_dataset.parquet")
    assert config.target.task == "regression"
    assert config.sequence.lookback_steps == 48
    assert config.model.name == "lstm"
    assert config.training.selection_metric == "validation_avg_signal_return_bps"
    assert config.threshold_search.enabled is True
    assert config.preprocessing.scaler == "robust"
    assert config.prediction.mode == "static"


def test_additional_dl_model_configs_load_typed_models() -> None:
    gru = load_settings(Path("configs/models/gru.yaml"), DeepLearningSettings)
    tcn = load_settings(Path("configs/models/tcn.yaml"), DeepLearningSettings)
    transformer = load_settings(Path("configs/models/transformer.yaml"), DeepLearningSettings)

    assert gru.model.name == "gru"
    assert gru.output.run_name == "gru_regression_24h_default"
    assert tcn.model.name == "tcn"
    assert tcn.model.tcn_num_blocks == 4
    assert transformer.model.name == "transformer_encoder"
    assert transformer.model.transformer_nhead == 4


def test_generate_signals_default_config_loads_typed_model() -> None:
    config = load_command_settings("generate-signals")
    assert isinstance(config, SignalSettings)
    assert config.input.baseline_predictions_path.endswith(
        "baseline_predictions.parquet"
    )
    assert config.input.dl_predictions_path.endswith("dl_predictions.parquet")
    assert config.source.name == "baseline"


def test_backtest_default_config_loads_typed_model() -> None:
    config = load_command_settings("backtest")
    assert isinstance(config, BacktestSettings)
    assert config.input.signal_path.endswith("signals.parquet")
    assert config.input.market_dataset_path.endswith("hourly_market_data.parquet")
    assert config.execution.holding_window_hours == 24
    assert config.reporting.run_name == "baseline_signals_default"


def test_robustness_report_default_config_loads_typed_model() -> None:
    config = load_command_settings("robustness-report")
    assert isinstance(config, RobustnessReportSettings)
    assert config.input.symbol == "BTCUSDT"
    assert config.evaluation.split_filter == ["test"]
    assert len(config.families) == 3
    assert config.families[0].name == "rule_based"
    assert len(config.feature_ablation.groups) >= 3


def test_evaluate_baseline_metadata_points_to_expected_default_file() -> None:
    settings = get_command_settings("evaluate-baseline")
    assert settings.default_config_path.name == "baseline.yaml"
    assert settings.config_model is BaselineSettings


def test_sync_vault_default_config_loads_typed_model() -> None:
    config = load_command_settings("sync-vault")
    assert isinstance(config, IntegrationSettings)
    assert config.input.signals_path.endswith("signals.parquet")
    assert config.input.leaderboard_path.endswith("leaderboard.parquet")
    assert config.contract.broadcast is False
    assert config.contract.update_nav is True


def test_run_demo_default_config_loads_typed_model() -> None:
    config = load_command_settings("run-demo")
    assert isinstance(config, DemoWorkflowSettings)
    assert config.commands.fetch_data_config_path.endswith("configs/data/default.yaml")
    assert config.stages.train_deep_learning.optional is True
    assert config.stages.generate_deep_learning_signals.optional is True
    assert config.output.run_name == "full_demo_default"
