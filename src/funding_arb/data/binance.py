"""Binance public REST adapter for historical market data."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd
import requests

from funding_arb.data.interfaces import HistoricalMarketDataSource, MarketDataRequest, OpenInterestRequest
from funding_arb.data.schemas import FUNDING_COLUMNS, OPEN_INTEREST_COLUMNS, RAW_BAR_COLUMNS

LOGGER = logging.getLogger(__name__)

SPOT_API_BASE = "https://api.binance.com/api/v3"
FUTURES_API_BASE = "https://fapi.binance.com/fapi/v1"
FUTURES_DATA_API_BASE = "https://fapi.binance.com/futures/data"
INTERVAL_TO_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


@dataclass
class BinanceHistoricalDataSource(HistoricalMarketDataSource):
    """Simple Binance adapter for the first working research pipeline."""

    timeout_seconds: int = 30
    limit_per_request: int = 1000
    session: requests.Session = field(default_factory=requests.Session)

    def _get_json(self, base_url: str, path: str, params: dict[str, object]) -> list[object] | dict[str, object]:
        response = self.session.get(f"{base_url}{path}", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def _paginate_klines(self, base_url: str, path: str, request: MarketDataRequest) -> pd.DataFrame:
        interval_ms = INTERVAL_TO_MS[request.interval]
        current_start = request.start_time_ms
        chunks: list[pd.DataFrame] = []

        while current_start < request.end_time_ms:
            payload = self._get_json(
                base_url,
                path,
                {
                    "symbol": request.symbol,
                    "interval": request.interval,
                    "startTime": current_start,
                    "endTime": request.end_time_ms - 1,
                    "limit": self.limit_per_request,
                },
            )
            if not payload:
                break
            chunk = self._standardize_ohlcv(payload)
            chunk = chunk[chunk["timestamp"] < pd.to_datetime(request.end_time_ms, unit="ms", utc=True)]
            chunks.append(chunk)
            last_open_time = int(payload[-1][0])
            next_start = last_open_time + interval_ms
            if next_start <= current_start:
                break
            current_start = next_start

        if not chunks:
            return pd.DataFrame(columns=RAW_BAR_COLUMNS)
        return pd.concat(chunks, ignore_index=True)

    def _paginate_funding_rates(self, request: MarketDataRequest) -> pd.DataFrame:
        current_start = request.start_time_ms
        chunks: list[pd.DataFrame] = []

        while current_start < request.end_time_ms:
            payload = self._get_json(
                FUTURES_API_BASE,
                "/fundingRate",
                {
                    "symbol": request.symbol,
                    "startTime": current_start,
                    "endTime": request.end_time_ms - 1,
                    "limit": self.limit_per_request,
                },
            )
            if not payload:
                break
            chunk = pd.DataFrame(payload)
            chunk["timestamp"] = pd.to_datetime(chunk["fundingTime"], unit="ms", utc=True)
            chunk["funding_rate"] = pd.to_numeric(chunk["fundingRate"], errors="coerce")
            chunk["mark_price"] = pd.to_numeric(chunk.get("markPrice"), errors="coerce")
            chunks.append(chunk[FUNDING_COLUMNS])
            last_funding_time = int(payload[-1]["fundingTime"])
            next_start = last_funding_time + 1
            if next_start <= current_start:
                break
            current_start = next_start

        if not chunks:
            return pd.DataFrame(columns=FUNDING_COLUMNS)
        frame = pd.concat(chunks, ignore_index=True)
        return frame[frame["timestamp"] < pd.to_datetime(request.end_time_ms, unit="ms", utc=True)]

    def _paginate_open_interest(self, request: OpenInterestRequest) -> pd.DataFrame:
        interval_ms = INTERVAL_TO_MS[request.period]
        current_start = request.start_time_ms
        chunks: list[pd.DataFrame] = []

        while current_start < request.end_time_ms:
            payload = self._get_json(
                FUTURES_DATA_API_BASE,
                "/openInterestHist",
                {
                    "symbol": request.symbol,
                    "period": request.period,
                    "startTime": current_start,
                    "endTime": request.end_time_ms - 1,
                    "limit": self.limit_per_request,
                },
            )
            if not payload:
                break
            chunk = pd.DataFrame(payload)
            chunk["timestamp"] = pd.to_datetime(chunk["timestamp"], unit="ms", utc=True)
            chunk["open_interest"] = pd.to_numeric(chunk["sumOpenInterest"], errors="coerce")
            chunk["open_interest_value"] = pd.to_numeric(chunk["sumOpenInterestValue"], errors="coerce")
            chunks.append(chunk[OPEN_INTEREST_COLUMNS])
            last_timestamp = int(payload[-1]["timestamp"])
            next_start = last_timestamp + interval_ms
            if next_start <= current_start:
                break
            current_start = next_start

        if not chunks:
            return pd.DataFrame(columns=OPEN_INTEREST_COLUMNS)
        frame = pd.concat(chunks, ignore_index=True)
        return frame[frame["timestamp"] < pd.to_datetime(request.end_time_ms, unit="ms", utc=True)]

    @staticmethod
    def _standardize_ohlcv(payload: list[object]) -> pd.DataFrame:
        frame = pd.DataFrame(
            payload,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "trade_count",
                "taker_buy_base_volume",
                "taker_buy_quote_volume",
                "ignore",
            ],
        )
        frame["timestamp"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
        for column in [
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
        ]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        return frame[RAW_BAR_COLUMNS]

    def fetch_perpetual_bars(self, request: MarketDataRequest) -> pd.DataFrame:
        LOGGER.info("Fetching Binance perpetual klines for %s (%s)", request.symbol, request.interval)
        return self._paginate_klines(FUTURES_API_BASE, "/klines", request)

    def fetch_spot_bars(self, request: MarketDataRequest) -> pd.DataFrame:
        LOGGER.info("Fetching Binance spot klines for %s (%s)", request.symbol, request.interval)
        return self._paginate_klines(SPOT_API_BASE, "/klines", request)

    def fetch_funding_rates(self, request: MarketDataRequest) -> pd.DataFrame:
        LOGGER.info("Fetching Binance funding rates for %s", request.symbol)
        return self._paginate_funding_rates(request)

    def fetch_open_interest(self, request: OpenInterestRequest) -> pd.DataFrame:
        LOGGER.info("Fetching Binance open interest history for %s (%s)", request.symbol, request.period)
        return self._paginate_open_interest(request)