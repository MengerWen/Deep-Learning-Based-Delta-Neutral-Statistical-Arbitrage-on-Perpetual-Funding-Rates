from __future__ import annotations

from funding_arb.config.loader import get_command_settings, load_command_settings
from funding_arb.config.models import BaselineSettings, DataSettings, FeatureSettings


def test_fetch_data_default_config_loads_typed_model() -> None:
    config = load_command_settings("fetch-data")
    assert isinstance(config, DataSettings)
    assert config.dataset.symbol == "BTCUSDT"
    assert config.source.provider == "binance"
    assert config.sources["funding"].enabled is True


def test_build_features_default_config_loads_typed_model() -> None:
    config = load_command_settings("build-features")
    assert isinstance(config, FeatureSettings)
    assert config.labels.forward_horizon_hours == 8


def test_train_baseline_metadata_points_to_expected_default_file() -> None:
    settings = get_command_settings("train-baseline")
    assert settings.default_config_path.name == "baseline.yaml"
    assert settings.config_model is BaselineSettings