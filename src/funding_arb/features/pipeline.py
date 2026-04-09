"""Scaffold helpers for the feature-engineering layer."""

from __future__ import annotations

from typing import Any


def describe_feature_job(config: dict[str, Any]) -> str:
    """Return a human-readable summary of the feature scaffold job."""
    feature_set = config.get("feature_set", {})
    windows = feature_set.get("rolling_windows", [])
    label_cfg = config.get("labels", {})
    horizon = label_cfg.get("forward_horizon_hours", "unknown")

    return (
        "Feature scaffold ready with rolling windows "
        f"{windows} and forward horizon {horizon} hours. "
        "Add canonical feature computations in src/funding_arb/features/ next."
    )

