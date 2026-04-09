"""Helpers for loading repository config files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a JSON-compatible config file into a dictionary."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping at the top of {config_path}.")
    return data


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Backward-compatible alias kept for early scaffold references."""
    return load_config(path)
