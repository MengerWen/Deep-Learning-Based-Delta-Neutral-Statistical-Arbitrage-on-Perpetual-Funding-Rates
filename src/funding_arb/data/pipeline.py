"""Scaffold helpers for the market-data ingestion layer."""

from __future__ import annotations

from typing import Any


def describe_ingestion_job(config: dict[str, Any]) -> str:
    """Return a human-readable summary of the ingestion scaffold job."""
    dataset = config.get("dataset", {})
    symbol = dataset.get("symbol", "UNKNOWN")
    venue = dataset.get("venue", "unknown_venue")
    frequency = dataset.get("frequency", "unknown_frequency")
    start = dataset.get("start", "unknown_start")
    end = dataset.get("end", "unknown_end")

    return (
        "Ingestion scaffold ready for "
        f"{symbol} on {venue} at {frequency} frequency "
        f"from {start} to {end}. "
        "Implement real exchange adapters in src/funding_arb/data/ next."
    )

