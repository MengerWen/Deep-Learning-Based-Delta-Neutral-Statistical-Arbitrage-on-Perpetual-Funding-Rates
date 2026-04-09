from __future__ import annotations

from funding_arb.config.loader import get_command_settings, load_command_settings
from funding_arb.config.models import (
    BaselineSettings,
    DataQualityReportSettings,
    DataSettings,
    FeatureSettings,
    LabelPipelineSettings,
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
    assert len(config.rules) >= 1


def test_evaluate_baseline_metadata_points_to_expected_default_file() -> None:
    settings = get_command_settings("evaluate-baseline")
    assert settings.default_config_path.name == "baseline.yaml"
    assert settings.config_model is BaselineSettings
