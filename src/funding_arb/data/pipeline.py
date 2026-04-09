"""Historical data pipeline for perpetual-funding arbitrage research."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from funding_arb.config.models import DataProviderSettings, DataSettings
from funding_arb.data.binance import BinanceHistoricalDataSource
from funding_arb.data.cleaning import align_hourly_market_data, clean_source_frame, resolve_time_range
from funding_arb.data.interfaces import HistoricalMarketDataSource, MarketDataRequest, OpenInterestRequest
from funding_arb.utils.paths import ensure_directory, repo_path


@dataclass(frozen=True)
class DataPipelineArtifacts:
    """Paths produced by a full data-pipeline run."""

    raw_files: list[str]
    interim_files: list[str]
    processed_files: list[str]
    manifest_path: str


def describe_ingestion_job(config: DataSettings | dict[str, object]) -> str:
    """Return a human-readable summary of the ingestion job."""
    if isinstance(config, DataSettings):
        settings = config
    else:
        settings = DataSettings.model_validate(config)
    dataset = settings.dataset
    provider = settings.source.provider
    return (
        f"Historical ingestion ready for {dataset.symbol} via {provider} at {dataset.frequency} "
        f"from {dataset.start} to {dataset.end}. "
        f"Outputs will be written as {settings.output.format} under raw/interim/processed directories."
    )


def build_data_source(settings: DataProviderSettings) -> HistoricalMarketDataSource:
    """Construct the configured historical data source."""
    provider = settings.provider.lower()
    if provider == "binance":
        return BinanceHistoricalDataSource(
            timeout_seconds=settings.timeout_seconds,
            limit_per_request=settings.limit_per_request,
        )
    raise ValueError(f"Unsupported data provider: {settings.provider}")


def _resolve_subdir(path_text: str) -> Path:
    return repo_path(*Path(path_text).parts)


def _symbol_directory(base_dir: Path, provider: str, symbol: str, frequency: str) -> Path:
    return ensure_directory(base_dir / provider.lower() / symbol.lower() / frequency)


def _build_output_directories(settings: DataSettings) -> dict[str, Path]:
    provider = settings.source.provider
    symbol = settings.dataset.symbol
    frequency = settings.dataset.frequency
    return {
        "raw": _symbol_directory(_resolve_subdir(settings.output.raw_subdir), provider, symbol, frequency),
        "interim": _symbol_directory(_resolve_subdir(settings.output.interim_subdir), provider, symbol, frequency),
        "processed": _symbol_directory(_resolve_subdir(settings.output.processed_subdir), provider, symbol, frequency),
    }


def _write_frame(frame: pd.DataFrame, path: Path, file_format: str) -> Path:
    if file_format == "parquet":
        frame.to_parquet(path, index=False)
    elif file_format == "csv":
        frame.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {file_format}")
    return path


def _save_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_data_pipeline(settings: DataSettings) -> DataPipelineArtifacts:
    """Fetch, clean, align, and persist the first working historical dataset."""
    time_range = resolve_time_range(
        settings.dataset.start,
        settings.dataset.end,
        timezone=settings.cleaning.timezone,
    )
    data_source = build_data_source(settings.source)
    output_dirs = _build_output_directories(settings)
    output_format = settings.output.format.lower()

    interval = settings.dataset.frequency
    perpetual_symbol = settings.dataset.perpetual_symbol or settings.dataset.symbol
    spot_symbol = settings.dataset.spot_symbol or settings.dataset.symbol

    if not settings.sources.get("perpetual", None) or not settings.sources["perpetual"].enabled:
        raise ValueError("The first working pipeline requires perpetual bars to be enabled.")
    if not settings.sources.get("spot", None) or not settings.sources["spot"].enabled:
        raise ValueError("The first working pipeline requires spot bars to be enabled.")
    if not settings.sources.get("funding", None) or not settings.sources["funding"].enabled:
        raise ValueError("The first working pipeline requires funding history to be enabled.")

    bar_request = MarketDataRequest(
        symbol=perpetual_symbol,
        interval=interval,
        start_time_ms=int(time_range.start.timestamp() * 1000),
        end_time_ms=int(time_range.end_exclusive.timestamp() * 1000),
    )
    spot_request = MarketDataRequest(
        symbol=spot_symbol,
        interval=interval,
        start_time_ms=int(time_range.start.timestamp() * 1000),
        end_time_ms=int(time_range.end_exclusive.timestamp() * 1000),
    )

    raw_frames: dict[str, pd.DataFrame] = {
        "perpetual_bars": data_source.fetch_perpetual_bars(bar_request),
        "spot_bars": data_source.fetch_spot_bars(spot_request),
        "funding_rates": data_source.fetch_funding_rates(bar_request),
    }

    if settings.sources.get("open_interest") and settings.sources["open_interest"].enabled:
        raw_frames["open_interest"] = data_source.fetch_open_interest(
            OpenInterestRequest(
                symbol=perpetual_symbol,
                period=interval,
                start_time_ms=int(time_range.start.timestamp() * 1000),
                end_time_ms=int(time_range.end_exclusive.timestamp() * 1000),
            )
        )

    raw_files: list[str] = []
    for name, frame in raw_frames.items():
        extension = "parquet" if output_format == "parquet" else "csv"
        path = output_dirs["raw"] / f"{name}.{extension}"
        raw_files.append(str(_write_frame(frame, path, output_format)))

    cleaned_frames: dict[str, pd.DataFrame] = {
        "perpetual_bars": clean_source_frame(
            raw_frames["perpetual_bars"],
            timezone=settings.cleaning.timezone,
            numeric_columns=[
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
            ],
            expected_frequency=interval,
            drop_duplicates=settings.cleaning.drop_duplicates,
            sort_ascending=settings.cleaning.sort_ascending,
        ),
        "spot_bars": clean_source_frame(
            raw_frames["spot_bars"],
            timezone=settings.cleaning.timezone,
            numeric_columns=[
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
            ],
            expected_frequency=interval,
            drop_duplicates=settings.cleaning.drop_duplicates,
            sort_ascending=settings.cleaning.sort_ascending,
        ),
        "funding_rates": clean_source_frame(
            raw_frames["funding_rates"],
            timezone=settings.cleaning.timezone,
            numeric_columns=["funding_rate", "mark_price"],
            expected_frequency=None,
            drop_duplicates=settings.cleaning.drop_duplicates,
            sort_ascending=settings.cleaning.sort_ascending,
            allow_empty=True,
        ),
    }

    if "open_interest" in raw_frames:
        cleaned_frames["open_interest"] = clean_source_frame(
            raw_frames["open_interest"],
            timezone=settings.cleaning.timezone,
            numeric_columns=["open_interest", "open_interest_value"],
            expected_frequency=None,
            drop_duplicates=settings.cleaning.drop_duplicates,
            sort_ascending=settings.cleaning.sort_ascending,
            allow_empty=True,
        )

    interim_files: list[str] = []
    for name, frame in cleaned_frames.items():
        extension = "parquet" if output_format == "parquet" else "csv"
        path = output_dirs["interim"] / f"{name}_clean.{extension}"
        interim_files.append(str(_write_frame(frame, path, output_format)))

    canonical = align_hourly_market_data(
        cleaned_frames["perpetual_bars"],
        cleaned_frames["spot_bars"],
        cleaned_frames["funding_rates"],
        time_range=time_range,
        symbol=settings.dataset.symbol,
        venue=settings.dataset.venue,
        frequency=settings.dataset.frequency,
        open_interest=cleaned_frames.get("open_interest"),
        max_forward_fill_hours=settings.cleaning.max_forward_fill_hours,
        fill_volume_value=settings.cleaning.fill_volume_value,
        fill_funding_value=settings.cleaning.fill_funding_value,
        fill_price_method=settings.cleaning.fill_price_method,
        fill_open_interest_method=settings.cleaning.fill_open_interest_method,
        validate_frequency=settings.cleaning.validate_frequency,
    )

    processed_files: list[str] = []
    primary_extension = "parquet" if output_format == "parquet" else "csv"
    primary_path = output_dirs["processed"] / f"hourly_market_data.{primary_extension}"
    processed_files.append(str(_write_frame(canonical, primary_path, output_format)))

    if output_format != "csv" and settings.output.write_csv:
        csv_path = output_dirs["processed"] / "hourly_market_data.csv"
        processed_files.append(str(_write_frame(canonical, csv_path, "csv")))

    manifest_path = output_dirs["processed"] / "manifest.json"
    manifest = {
        "provider": settings.source.provider,
        "dataset": settings.dataset.model_dump(),
        "time_range": {
            "start": time_range.start.isoformat(),
            "end_exclusive": time_range.end_exclusive.isoformat(),
        },
        "row_counts": {name: int(frame.shape[0]) for name, frame in raw_frames.items()},
        "cleaned_row_counts": {name: int(frame.shape[0]) for name, frame in cleaned_frames.items()},
        "canonical_row_count": int(canonical.shape[0]),
        "raw_files": raw_files,
        "interim_files": interim_files,
        "processed_files": processed_files,
        "assumptions": settings.notes,
    }
    _save_manifest(manifest_path, manifest)

    return DataPipelineArtifacts(
        raw_files=raw_files,
        interim_files=interim_files,
        processed_files=processed_files,
        manifest_path=str(manifest_path),
    )