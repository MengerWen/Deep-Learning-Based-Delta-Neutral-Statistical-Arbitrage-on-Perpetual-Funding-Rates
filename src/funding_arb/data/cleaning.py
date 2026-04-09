"""Cleaning and alignment utilities for historical market datasets."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from pandas.tseries.frequencies import to_offset

from funding_arb.data.schemas import CANONICAL_COLUMNS

DATE_ONLY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class TimeRange:
    """Inclusive start and exclusive end timestamps for extraction windows."""

    start: pd.Timestamp
    end_exclusive: pd.Timestamp


def parse_timestamp(value: object, timezone: str = "UTC") -> pd.Timestamp:
    """Parse a timestamp-like value into a timezone-aware pandas timestamp."""
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize(timezone)
    return timestamp.tz_convert(timezone)


def resolve_time_range(start: object, end: object, timezone: str = "UTC") -> TimeRange:
    """Resolve config dates into an inclusive-start, exclusive-end extraction range."""
    start_ts = parse_timestamp(start, timezone)
    end_text = str(end).strip()
    end_ts = parse_timestamp(end, timezone)
    if DATE_ONLY_PATTERN.match(end_text):
        end_ts = end_ts + pd.Timedelta(days=1)
    if end_ts <= start_ts:
        raise ValueError("End timestamp must be greater than start timestamp.")
    return TimeRange(start=start_ts, end_exclusive=end_ts)


def normalize_timestamp_column(
    frame: pd.DataFrame,
    column: str = "timestamp",
    timezone: str = "UTC",
) -> pd.DataFrame:
    """Return a copy with a normalized timezone-aware timestamp column."""
    normalized = frame.copy()
    timestamps = pd.to_datetime(normalized[column], utc=True)
    if timezone.upper() != "UTC":
        timestamps = timestamps.dt.tz_convert(timezone)
    normalized[column] = timestamps
    return normalized


def drop_duplicates_and_sort(
    frame: pd.DataFrame,
    subset: Iterable[str] = ("timestamp",),
    ascending: bool = True,
) -> pd.DataFrame:
    """Drop duplicate records by key while keeping the last observation, then sort."""
    deduplicated = frame.drop_duplicates(subset=list(subset), keep="last")
    return deduplicated.sort_values(list(subset), ascending=ascending).reset_index(drop=True)


def assert_integrity(frame: pd.DataFrame, expected_frequency: str | None = None) -> None:
    """Raise if timestamps are missing, unsorted, duplicated, or off-frequency."""
    if frame.empty:
        raise ValueError("Frame is empty after cleaning.")
    timestamps = frame["timestamp"]
    if timestamps.isna().any():
        raise ValueError("Timestamp column contains missing values.")
    if not timestamps.is_monotonic_increasing:
        raise ValueError("Timestamp column must be sorted in ascending order.")
    if timestamps.duplicated().any():
        raise ValueError("Timestamp column contains duplicate values.")
    if expected_frequency is not None and len(frame) > 1:
        expected_delta = pd.Timedelta(to_offset(expected_frequency))
        deltas = timestamps.diff().dropna()
        if not deltas.eq(expected_delta).all():
            raise ValueError(f"Timestamp spacing does not match expected frequency {expected_frequency}.")


def clean_source_frame(
    frame: pd.DataFrame,
    *,
    timezone: str = "UTC",
    numeric_columns: Iterable[str] | None = None,
    expected_frequency: str | None = None,
    drop_duplicates: bool = True,
    sort_ascending: bool = True,
    allow_empty: bool = False,
) -> pd.DataFrame:
    """Normalize types and ordering for a single source frame."""
    cleaned = normalize_timestamp_column(frame, timezone=timezone)
    for column in numeric_columns or []:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    if drop_duplicates:
        cleaned = drop_duplicates_and_sort(cleaned, ascending=sort_ascending)
    else:
        cleaned = cleaned.sort_values("timestamp", ascending=sort_ascending).reset_index(drop=True)
    if cleaned.empty:
        if allow_empty:
            return cleaned.reset_index(drop=True)
        raise ValueError("Frame is empty after cleaning.")
    if expected_frequency is not None:
        assert_integrity(cleaned, expected_frequency=expected_frequency)
    else:
        assert_integrity(cleaned)
    return cleaned


def _rename_bar_columns(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    renamed = frame.copy()
    mapping = {
        "open": f"{prefix}_open",
        "high": f"{prefix}_high",
        "low": f"{prefix}_low",
        "close": f"{prefix}_close",
        "volume": f"{prefix}_volume",
    }
    return renamed.rename(columns=mapping)


def _fill_price_columns(
    frame: pd.DataFrame,
    prefix: str,
    method: str,
    limit: int,
) -> pd.DataFrame:
    filled = frame.copy()
    columns = [f"{prefix}_open", f"{prefix}_high", f"{prefix}_low", f"{prefix}_close"]
    if method == "ffill":
        filled[columns] = filled[columns].ffill(limit=limit)
    elif method not in {"none", ""}:
        raise ValueError(f"Unsupported fill_price_method: {method}")
    return filled


def align_hourly_market_data(
    perpetual: pd.DataFrame,
    spot: pd.DataFrame,
    funding: pd.DataFrame,
    *,
    time_range: TimeRange,
    symbol: str,
    venue: str,
    frequency: str = "1h",
    open_interest: pd.DataFrame | None = None,
    max_forward_fill_hours: int = 3,
    fill_volume_value: float = 0.0,
    fill_funding_value: float = 0.0,
    fill_price_method: str = "ffill",
    fill_open_interest_method: str = "ffill",
    validate_frequency: bool = True,
) -> pd.DataFrame:
    """Align cleaned source tables onto a canonical hourly research grid."""
    hourly_index = pd.date_range(
        start=time_range.start,
        end=time_range.end_exclusive,
        freq=frequency,
        inclusive="left",
        tz=time_range.start.tz,
    )
    aligned = pd.DataFrame({"timestamp": hourly_index})

    perp = _rename_bar_columns(perpetual[["timestamp", "open", "high", "low", "close", "volume"]], "perp")
    spot_frame = _rename_bar_columns(spot[["timestamp", "open", "high", "low", "close", "volume"]], "spot")
    funding_frame = funding[["timestamp", "funding_rate"]].copy()

    aligned = aligned.merge(perp, on="timestamp", how="left")
    aligned = aligned.merge(spot_frame, on="timestamp", how="left")
    aligned = aligned.merge(funding_frame, on="timestamp", how="left")

    aligned["perp_close_was_missing"] = aligned["perp_close"].isna()
    aligned["spot_close_was_missing"] = aligned["spot_close"].isna()

    aligned = _fill_price_columns(aligned, "perp", fill_price_method, max_forward_fill_hours)
    aligned = _fill_price_columns(aligned, "spot", fill_price_method, max_forward_fill_hours)

    aligned["perp_volume"] = aligned["perp_volume"].fillna(fill_volume_value)
    aligned["spot_volume"] = aligned["spot_volume"].fillna(fill_volume_value)

    aligned["funding_event"] = aligned["funding_rate"].notna().astype(int)
    aligned["funding_rate"] = aligned["funding_rate"].fillna(fill_funding_value)

    if open_interest is not None and not open_interest.empty:
        oi_frame = open_interest[["timestamp", "open_interest"]].copy()
        aligned = aligned.merge(oi_frame, on="timestamp", how="left")
        aligned["open_interest_was_missing"] = aligned["open_interest"].isna()
        if fill_open_interest_method == "ffill":
            aligned["open_interest"] = aligned["open_interest"].ffill(limit=max_forward_fill_hours)
        elif fill_open_interest_method not in {"none", ""}:
            raise ValueError(f"Unsupported fill_open_interest_method: {fill_open_interest_method}")
    else:
        aligned["open_interest"] = pd.Series(pd.NA, index=aligned.index, dtype="Float64")
        aligned["open_interest_was_missing"] = True

    aligned["symbol"] = symbol
    aligned["venue"] = venue
    aligned["frequency"] = frequency

    if aligned["perp_close"].isna().any():
        missing = int(aligned["perp_close"].isna().sum())
        raise ValueError(f"Perpetual close contains {missing} missing rows after alignment and filling.")
    if aligned["spot_close"].isna().any():
        missing = int(aligned["spot_close"].isna().sum())
        raise ValueError(f"Spot close contains {missing} missing rows after alignment and filling.")

    ordered = aligned[CANONICAL_COLUMNS].copy()
    if validate_frequency:
        assert_integrity(ordered[["timestamp"]], expected_frequency=frequency)
    return ordered