"""Shared signal schema constants and validation helpers."""

from __future__ import annotations

import pandas as pd

SIGNAL_COLUMNS = [
    "timestamp",
    "asset",
    "venue",
    "frequency",
    "source",
    "source_subtype",
    "strategy_name",
    "model_family",
    "task",
    "signal_score",
    "predicted_class",
    "expected_return_bps",
    "signal_threshold",
    "threshold_objective",
    "prediction_mode",
    "calibration_method",
    "feature_importance_method",
    "selected_hyperparameters_json",
    "suggested_direction",
    "confidence",
    "should_trade",
    "split",
    "metadata_json",
]

PREDICTION_REQUIRED_COLUMNS = [
    "timestamp",
    "split",
    "model_name",
    "model_family",
    "task",
    "signal_direction",
    "signal",
    "decision_score",
    "signal_threshold",
    "signal_strength",
    "predicted_probability",
    "predicted_return_bps",
    "predicted_label",
]



def validate_prediction_columns(frame: pd.DataFrame, source_name: str) -> None:
    """Ensure an upstream prediction artifact contains the expected columns."""
    missing = [column for column in PREDICTION_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Prediction artifact for source '{source_name}' is missing columns: {missing_text}")



def ensure_signal_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a frame ordered by the normalized signal schema."""
    missing = [column for column in SIGNAL_COLUMNS if column not in frame.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Signal frame is missing required columns: {missing_text}")
    return frame[SIGNAL_COLUMNS].copy()
