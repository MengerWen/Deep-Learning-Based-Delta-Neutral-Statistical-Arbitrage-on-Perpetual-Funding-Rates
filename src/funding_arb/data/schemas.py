"""Column schemas for raw, cleaned, and canonical market datasets."""

from __future__ import annotations

RAW_BAR_COLUMNS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
    "close_time",
]

FUNDING_COLUMNS = [
    "timestamp",
    "funding_rate",
    "mark_price",
]

OPEN_INTEREST_COLUMNS = [
    "timestamp",
    "open_interest",
    "open_interest_value",
]

CANONICAL_COLUMNS = [
    "timestamp",
    "symbol",
    "venue",
    "frequency",
    "perp_open",
    "perp_high",
    "perp_low",
    "perp_close",
    "perp_volume",
    "spot_open",
    "spot_high",
    "spot_low",
    "spot_close",
    "spot_volume",
    "funding_rate",
    "funding_event",
    "open_interest",
    "perp_close_was_missing",
    "spot_close_was_missing",
    "open_interest_was_missing",
]