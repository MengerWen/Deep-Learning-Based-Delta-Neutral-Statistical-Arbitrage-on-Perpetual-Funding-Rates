from __future__ import annotations

import pandas as pd

from funding_arb.config.models import BaselineSettings, RuleBaselineSpec
from funding_arb.models.baselines import _rule_prediction_frame, evaluate_prediction_table, select_feature_columns


def _baseline_settings() -> BaselineSettings:
    return BaselineSettings.model_validate(
        {
            "input": {
                "dataset_path": "data/processed/supervised/binance/btcusdt/1h/btcusdt_supervised_dataset.parquet",
                "provider": "binance",
                "symbol": "BTCUSDT",
                "venue": "binance",
                "frequency": "1h",
            },
            "target": {
                "timestamp_column": "timestamp",
                "split_column": "split",
                "ready_column": "supervised_ready",
                "classification_column": "target_is_profitable_24h",
                "regression_column": "target_future_net_return_bps_24h",
            },
            "feature_selection": {
                "exclude_columns": [
                    "timestamp",
                    "split",
                    "feature_ready",
                    "supervised_ready",
                ],
                "exclude_prefixes": ["target_"],
                "max_missing_fraction": 0.4,
                "drop_constant_features": True,
            },
            "rules": [],
            "predictive": {},
            "output": {
                "model_dir": "data/artifacts/models/baselines",
                "run_name": "unit_test",
                "write_csv": True,
                "write_markdown_report": False,
            },
        }
    )


def test_select_feature_columns_excludes_targets_constants_and_sparse_columns() -> None:
    settings = _baseline_settings()
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=4, freq="h", tz="UTC"),
            "split": ["train", "train", "validation", "test"],
            "supervised_ready": [1, 1, 1, 1],
            "feature_ready": [1, 1, 1, 1],
            "funding_rate_bps": [0.1, 0.2, 0.3, 0.4],
            "spread_zscore_72h": [1.0, 0.5, 0.0, -0.5],
            "always_one": [1, 1, 1, 1],
            "mostly_missing": [1.0, None, None, None],
            "target_is_profitable_24h": [0, 1, 0, 0],
            "target_future_net_return_bps_24h": [1.0, 2.0, 3.0, 4.0],
        }
    )

    columns = select_feature_columns(frame, settings)

    assert columns == ["funding_rate_bps", "spread_zscore_72h"]


def test_rule_prediction_frame_applies_combined_threshold_and_regime_filter() -> None:
    settings = _baseline_settings()
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=3, freq="h", tz="UTC"),
            "split": ["train", "validation", "test"],
            "funding_rate_bps": [1.2, 0.8, 1.4],
            "spread_zscore_72h": [1.6, 1.8, 1.4],
            "positive_funding_regime": [1, 1, 1],
            "target_is_profitable_24h": [1, 0, 1],
            "target_future_net_return_bps_24h": [12.0, -4.0, 8.0],
        }
    )
    rule = RuleBaselineSpec(
        name="combined",
        kind="combined_threshold",
        funding_column="funding_rate_bps",
        funding_threshold_bps=1.0,
        spread_column="spread_zscore_72h",
        spread_threshold=1.5,
        regime_column="positive_funding_regime",
        regime_value=1,
    )

    predictions = _rule_prediction_frame(frame, settings, rule)

    assert predictions["signal"].tolist() == [1, 0, 0]
    assert predictions["predicted_label"].tolist() == [1, 0, 0]
    assert predictions["model_family"].unique().tolist() == ["rule_based"]


def test_evaluate_prediction_table_returns_split_metrics_for_classification_and_regression() -> None:
    predictions = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=6, freq="h", tz="UTC"),
            "split": ["train", "train", "validation", "validation", "test", "test"],
            "model_name": ["logit", "logit", "logit", "logit", "ridge", "ridge"],
            "model_family": ["linear", "linear", "linear", "linear", "linear", "linear"],
            "task": ["classification", "classification", "classification", "classification", "regression", "regression"],
            "signal_direction": ["short_perp_long_spot"] * 6,
            "signal": [1, 0, 1, 0, 1, 0],
            "decision_score": [0.8, 0.2, 0.6, 0.4, 10.0, -5.0],
            "signal_threshold": [0.5, 0.5, 0.5, 0.5, 0.0, 0.0],
            "signal_strength": [0.3, -0.3, 0.1, -0.1, 10.0, -5.0],
            "predicted_probability": [0.8, 0.2, 0.6, 0.4, None, None],
            "predicted_return_bps": [None, None, None, None, 10.0, -5.0],
            "predicted_label": [1, 0, 1, 0, 1, 0],
            "actual_label": [1, 0, 0, 0, 1, 0],
            "actual_return_bps": [5.0, -2.0, -1.0, -3.0, 8.0, -6.0],
        }
    )

    metrics = evaluate_prediction_table(predictions)

    assert set(metrics["task"].tolist()) == {"classification", "regression"}
    classification_row = metrics[(metrics["model_name"] == "logit") & (metrics["split"] == "train")].iloc[0]
    regression_row = metrics[(metrics["model_name"] == "ridge") & (metrics["split"] == "test")].iloc[0]
    assert classification_row["signal_count"] == 1
    assert regression_row["signal_count"] == 1
    assert regression_row["mae"] == 1.5
