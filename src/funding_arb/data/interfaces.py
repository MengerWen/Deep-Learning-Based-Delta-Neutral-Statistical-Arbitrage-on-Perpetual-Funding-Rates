"""Interfaces for historical market-data adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class MarketDataRequest:
    symbol: str
    interval: str
    start_time_ms: int
    end_time_ms: int


@dataclass(frozen=True)
class OpenInterestRequest:
    symbol: str
    period: str
    start_time_ms: int
    end_time_ms: int


class HistoricalMarketDataSource(ABC):
    """Exchange-agnostic interface for historical perpetual-arbitrage research data."""

    @abstractmethod
    def fetch_perpetual_bars(self, request: MarketDataRequest) -> pd.DataFrame:
        """Fetch perpetual futures OHLCV bars."""

    @abstractmethod
    def fetch_spot_bars(self, request: MarketDataRequest) -> pd.DataFrame:
        """Fetch spot or index-reference OHLCV bars."""

    @abstractmethod
    def fetch_funding_rates(self, request: MarketDataRequest) -> pd.DataFrame:
        """Fetch historical funding-rate events."""

    def fetch_index_bars(self, request: MarketDataRequest) -> pd.DataFrame:
        """Fetch index bars when the venue supports them."""
        raise NotImplementedError("This data source does not implement index-price history.")

    def fetch_open_interest(self, request: OpenInterestRequest) -> pd.DataFrame:
        """Fetch optional open-interest history."""
        raise NotImplementedError("This data source does not implement open-interest history.")