"""Scaffold helpers for post-cost label generation."""

from __future__ import annotations

from typing import Any


def describe_labeling_assumption(config: dict[str, Any]) -> str:
    """Summarize the current label-generation assumptions."""
    label_cfg = config.get("labels", {})
    horizon = label_cfg.get("forward_horizon_hours", "unknown")
    edge = label_cfg.get("min_expected_edge_bps", "unknown")
    return (
        f"Labels will target a {horizon}-hour horizon with minimum expected edge "
        f"of {edge} bps after costs."
    )

