"""Scaffold helpers for deep-learning model training."""

from __future__ import annotations

from typing import Any



def describe_deep_learning_job(config: dict[str, Any]) -> str:
    """Return a short summary of the deep-learning training scaffold."""
    model_cfg = config.get("model", {})
    training_cfg = config.get("training", {})
    name = model_cfg.get("name", "unknown_model")
    lookback = model_cfg.get("lookback_steps", "n/a")
    epochs = training_cfg.get("epochs", "n/a")
    batch_size = training_cfg.get("batch_size", "n/a")
    return (
        f"Deep-learning scaffold ready for '{name}' "
        f"(lookback={lookback}, epochs={epochs}, batch_size={batch_size}). "
        "Implement PyTorch dataset wiring and training loops next."
    )