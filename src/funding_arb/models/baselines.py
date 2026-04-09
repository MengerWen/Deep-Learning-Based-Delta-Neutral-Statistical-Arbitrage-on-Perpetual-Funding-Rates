"""Scaffold helpers for baseline model training."""

from __future__ import annotations

from typing import Any


def describe_baseline_job(config: dict[str, Any]) -> str:
    """Return a short summary of the baseline training scaffold."""
    model_cfg = config.get("model", {})
    name = model_cfg.get("name", "unknown_model")
    entry = model_cfg.get("entry_threshold", "n/a")
    exit_ = model_cfg.get("exit_threshold", "n/a")
    return (
        f"Baseline model scaffold ready for '{name}' "
        f"(entry={entry}, exit={exit_}). "
        "Implement feature consumption and signal generation next."
    )

