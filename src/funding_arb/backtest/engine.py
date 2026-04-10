"""Explicit delta-neutral prototype backtesting engine for perpetual funding-rate arbitrage."""

from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from funding_arb.config.models import BacktestSettings
from funding_arb.evaluation.metrics import calculate_max_drawdown, calculate_sharpe_ratio, calculate_total_return
from funding_arb.utils.paths import ensure_directory, repo_path

PLOT_COLORS = [
    "#0f766e",
    "#1d4ed8",
    "#b45309",
    "#b91c1c",
    "#7c3aed",
    "#0891b2",
    "#65a30d",
]
PERIODS_PER_YEAR_1H = 24 * 365


@dataclass(frozen=True)
class BacktestArtifacts:
    """Files produced by the backtest pipeline."""

    output_dir: str
    trade_log_path: str
    trade_log_csv_path: str | None
    equity_curve_path: str
    equity_curve_csv_path: str | None
    strategy_metrics_path: str
    strategy_metrics_csv_path: str | None
    split_summary_path: str
    split_summary_csv_path: str | None
    leaderboard_path: str
    leaderboard_csv_path: str | None
    report_path: str | None
    figure_paths: list[str]
    manifest_path: str


@dataclass(frozen=True)
class OpenPosition:
    """Single delta-neutral position in the prototype backtester."""

    strategy_name: str
    source: str
    source_subtype: str
    task: str
    signal_timestamp: pd.Timestamp
    signal_split: str
    signal_score: float | None
    predicted_class: float | None
    expected_return_bps: float | None
    confidence: float | None
    metadata_json: str
    direction: str
    entry_signal_index: int
    entry_market_index: int
    entry_timestamp: pd.Timestamp
    position_notional_usd: float
    perp_entry_price_raw: float
    spot_entry_price_raw: float


def describe_backtest_job(config: BacktestSettings | dict[str, Any]) -> str:
    """Return a human-readable summary of the backtest job."""
    settings = config if isinstance(config, BacktestSettings) else BacktestSettings.model_validate(config)
    strategy_count = "all strategies" if not settings.selection.strategy_names else f"{len(settings.selection.strategy_names)} strategy filters"
    return (
        f"Backtest ready for {settings.input.symbol} on {settings.input.provider} at {settings.input.frequency}, "
        f"reading {settings.input.signal_path} and {settings.input.market_dataset_path}. "
        f"It will simulate {strategy_count} with holding window {settings.execution.holding_window_hours}h, "
        f"maximum holding {settings.execution.maximum_holding_hours}h, and write artifacts under "
        f"{settings.reporting.output_dir}/{settings.input.provider}/{settings.input.symbol.lower()}/"
        f"{settings.input.frequency}/{settings.reporting.run_name}."
    )


def _resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_path(*path.parts)


def _load_frame(path_text: str | Path) -> pd.DataFrame:
    path = _resolve_path(path_text)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file format: {path.suffix}")


def _load_signal_table(settings: BacktestSettings) -> pd.DataFrame:
    frame = _load_frame(settings.input.signal_path)
    required = {
        "timestamp",
        "asset",
        "source",
        "source_subtype",
        "strategy_name",
        "task",
        "signal_score",
        "predicted_class",
        "expected_return_bps",
        "suggested_direction",
        "confidence",
        "should_trade",
        "split",
        "metadata_json",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Signal artifact is missing required columns: {', '.join(missing)}")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.sort_values(["strategy_name", "timestamp"]).reset_index(drop=True)
    split_filter = set(settings.selection.split_filter)
    if split_filter:
        frame = frame[frame["split"].isin(split_filter)].copy()
    if settings.selection.strategy_names:
        allowed = set(settings.selection.strategy_names)
        frame = frame[frame["strategy_name"].isin(allowed)].copy()
    if frame.empty:
        raise ValueError("No signal rows remain after applying backtest filters.")
    return frame


def _load_market_table(settings: BacktestSettings) -> pd.DataFrame:
    frame = _load_frame(settings.input.market_dataset_path)
    required = {
        "timestamp",
        "symbol",
        "venue",
        "frequency",
        "perp_open",
        "perp_close",
        "spot_open",
        "spot_close",
        "funding_rate",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Market dataset is missing required columns: {', '.join(missing)}")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    return frame


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(converted) or math.isinf(converted):
        return None
    return converted


def _price_column(prefix: str, field: str) -> str:
    return f"{prefix}_{field}"


def _direction_signs(direction: str) -> tuple[int, int]:
    if direction == "short_perp_long_spot":
        return -1, 1
    if direction == "long_perp_short_spot":
        return 1, -1
    raise ValueError(f"Unsupported direction: {direction}")


def _effective_price(raw_price: float, position_sign: int, *, is_entry: bool, slippage_bps: float) -> float:
    slippage = float(slippage_bps) / 10_000.0
    if position_sign > 0:
        multiplier = 1.0 + slippage if is_entry else 1.0 - slippage
    else:
        multiplier = 1.0 - slippage if is_entry else 1.0 + slippage
    return float(raw_price) * multiplier


def _funding_rate_sum(cumulative_rates: pd.Series, start_index: int, end_index: int) -> float:
    """Return cumulative funding rate from start_index through end_index - 1."""
    if end_index <= start_index:
        return 0.0
    end_value = float(cumulative_rates.iloc[end_index - 1])
    start_value = float(cumulative_rates.iloc[start_index - 1]) if start_index > 0 else 0.0
    return end_value - start_value


def calculate_trade_pnl(
    *,
    direction: str,
    position_notional_usd: float,
    perp_entry_price_raw: float,
    perp_exit_price_raw: float,
    spot_entry_price_raw: float,
    spot_exit_price_raw: float,
    funding_rate_sum: float,
    taker_fee_bps: float,
    slippage_bps: float,
    gas_cost_usd: float,
    other_friction_bps: float,
) -> dict[str, float]:
    """Calculate explicit trade-level PnL for a delta-neutral position."""
    if position_notional_usd <= 0:
        raise ValueError("position_notional_usd must be positive.")
    prices = [perp_entry_price_raw, perp_exit_price_raw, spot_entry_price_raw, spot_exit_price_raw]
    if any(float(price) <= 0 for price in prices):
        raise ValueError("All trade prices must be strictly positive.")

    perp_sign, hedge_sign = _direction_signs(direction)
    perp_entry_price_effective = _effective_price(perp_entry_price_raw, perp_sign, is_entry=True, slippage_bps=slippage_bps)
    perp_exit_price_effective = _effective_price(perp_exit_price_raw, perp_sign, is_entry=False, slippage_bps=slippage_bps)
    spot_entry_price_effective = _effective_price(spot_entry_price_raw, hedge_sign, is_entry=True, slippage_bps=slippage_bps)
    spot_exit_price_effective = _effective_price(spot_exit_price_raw, hedge_sign, is_entry=False, slippage_bps=slippage_bps)

    perp_quantity = float(position_notional_usd) / perp_entry_price_effective
    spot_quantity = float(position_notional_usd) / spot_entry_price_effective

    perp_leg_pnl_usd = perp_quantity * (perp_exit_price_effective - perp_entry_price_effective)
    if perp_sign < 0:
        perp_leg_pnl_usd *= -1.0
    spot_leg_pnl_usd = spot_quantity * (spot_exit_price_effective - spot_entry_price_effective)
    if hedge_sign < 0:
        spot_leg_pnl_usd *= -1.0

    funding_pnl_usd = (-perp_sign) * float(funding_rate_sum) * float(position_notional_usd)
    trading_fees_usd = 4.0 * float(position_notional_usd) * (float(taker_fee_bps) / 10_000.0)
    gas_cost_usd = float(gas_cost_usd)
    other_friction_usd = float(position_notional_usd) * (float(other_friction_bps) / 10_000.0)
    turnover_usd = 4.0 * float(position_notional_usd)
    estimated_slippage_cost_usd = turnover_usd * (float(slippage_bps) / 10_000.0)

    gross_pnl_usd = perp_leg_pnl_usd + spot_leg_pnl_usd + funding_pnl_usd
    net_pnl_usd = gross_pnl_usd - trading_fees_usd - gas_cost_usd - other_friction_usd
    gross_return_bps = gross_pnl_usd / float(position_notional_usd) * 10_000.0
    net_return_bps = net_pnl_usd / float(position_notional_usd) * 10_000.0

    return {
        "perp_entry_price_effective": float(perp_entry_price_effective),
        "perp_exit_price_effective": float(perp_exit_price_effective),
        "spot_entry_price_effective": float(spot_entry_price_effective),
        "spot_exit_price_effective": float(spot_exit_price_effective),
        "perp_quantity": float(perp_quantity),
        "spot_quantity": float(spot_quantity),
        "perp_leg_pnl_usd": float(perp_leg_pnl_usd),
        "spot_leg_pnl_usd": float(spot_leg_pnl_usd),
        "funding_pnl_usd": float(funding_pnl_usd),
        "gross_pnl_usd": float(gross_pnl_usd),
        "trading_fees_usd": float(trading_fees_usd),
        "gas_cost_usd": float(gas_cost_usd),
        "other_friction_usd": float(other_friction_usd),
        "estimated_slippage_cost_usd": float(estimated_slippage_cost_usd),
        "net_pnl_usd": float(net_pnl_usd),
        "gross_return_bps": float(gross_return_bps),
        "net_return_bps": float(net_return_bps),
        "turnover_usd": float(turnover_usd),
    }


def _entry_conditions_met(row: pd.Series, settings: BacktestSettings) -> bool:
    direction = str(row.get("suggested_direction", "flat"))
    if direction != settings.selection.direction:
        return False
    if settings.selection.require_should_trade and int(row.get("should_trade", 0)) != 1:
        return False
    if settings.selection.min_signal_score is not None:
        score = _safe_float(row.get("signal_score"))
        if score is None or score < float(settings.selection.min_signal_score):
            return False
    if settings.selection.min_confidence is not None:
        confidence = _safe_float(row.get("confidence"))
        if confidence is None or confidence < float(settings.selection.min_confidence):
            return False
    if settings.selection.min_expected_return_bps is not None:
        expected_return = _safe_float(row.get("expected_return_bps"))
        if expected_return is None or expected_return < float(settings.selection.min_expected_return_bps):
            return False
    return True


def _open_position(row: pd.Series, market: pd.DataFrame, entry_market_index: int, settings: BacktestSettings) -> OpenPosition:
    execution_price_field = settings.execution.execution_price_field
    perp_entry_price_raw = float(market.iloc[entry_market_index][_price_column("perp", execution_price_field)])
    spot_entry_price_raw = float(market.iloc[entry_market_index][_price_column("spot", execution_price_field)])
    return OpenPosition(
        strategy_name=str(row["strategy_name"]),
        source=str(row["source"]),
        source_subtype=str(row["source_subtype"]),
        task=str(row["task"]),
        signal_timestamp=pd.Timestamp(row["timestamp"]),
        signal_split=str(row["split"]),
        signal_score=_safe_float(row.get("signal_score")),
        predicted_class=_safe_float(row.get("predicted_class")),
        expected_return_bps=_safe_float(row.get("expected_return_bps")),
        confidence=_safe_float(row.get("confidence")),
        metadata_json=str(row.get("metadata_json", "{}")),
        direction=str(row["suggested_direction"]),
        entry_signal_index=int(row["market_index"]),
        entry_market_index=int(entry_market_index),
        entry_timestamp=pd.Timestamp(market.iloc[entry_market_index]["timestamp"]),
        position_notional_usd=float(settings.portfolio.position_notional),
        perp_entry_price_raw=perp_entry_price_raw,
        spot_entry_price_raw=spot_entry_price_raw,
    )


def _mark_trade_return_bps(
    position: OpenPosition,
    market: pd.DataFrame,
    funding_cumulative: pd.Series,
    current_market_index: int,
    settings: BacktestSettings,
) -> float:
    funding_sum = _funding_rate_sum(funding_cumulative, position.entry_market_index, current_market_index + 1)
    pnl = calculate_trade_pnl(
        direction=position.direction,
        position_notional_usd=position.position_notional_usd,
        perp_entry_price_raw=position.perp_entry_price_raw,
        perp_exit_price_raw=float(market.iloc[current_market_index]["perp_close"]),
        spot_entry_price_raw=position.spot_entry_price_raw,
        spot_exit_price_raw=float(market.iloc[current_market_index]["spot_close"]),
        funding_rate_sum=funding_sum,
        taker_fee_bps=settings.costs.taker_fee_bps,
        slippage_bps=settings.costs.slippage_bps,
        gas_cost_usd=settings.costs.gas_cost_usd,
        other_friction_bps=settings.costs.other_friction_bps,
    )
    return float(pnl["net_return_bps"])


def _close_position(
    position: OpenPosition,
    *,
    exit_market_index: int,
    exit_reason: str,
    observed_market_index: int,
    market: pd.DataFrame,
    funding_cumulative: pd.Series,
    settings: BacktestSettings,
) -> dict[str, Any]:
    execution_price_field = settings.execution.execution_price_field
    perp_exit_price_raw = float(market.iloc[exit_market_index][_price_column("perp", execution_price_field)])
    spot_exit_price_raw = float(market.iloc[exit_market_index][_price_column("spot", execution_price_field)])
    funding_sum = _funding_rate_sum(funding_cumulative, position.entry_market_index, exit_market_index)
    pnl = calculate_trade_pnl(
        direction=position.direction,
        position_notional_usd=position.position_notional_usd,
        perp_entry_price_raw=position.perp_entry_price_raw,
        perp_exit_price_raw=perp_exit_price_raw,
        spot_entry_price_raw=position.spot_entry_price_raw,
        spot_exit_price_raw=spot_exit_price_raw,
        funding_rate_sum=funding_sum,
        taker_fee_bps=settings.costs.taker_fee_bps,
        slippage_bps=settings.costs.slippage_bps,
        gas_cost_usd=settings.costs.gas_cost_usd,
        other_friction_bps=settings.costs.other_friction_bps,
    )
    return {
        "strategy_name": position.strategy_name,
        "source": position.source,
        "source_subtype": position.source_subtype,
        "task": position.task,
        "signal_timestamp": position.signal_timestamp,
        "signal_split": position.signal_split,
        "entry_timestamp": position.entry_timestamp,
        "exit_timestamp": pd.Timestamp(market.iloc[exit_market_index]["timestamp"]),
        "entry_signal_index": int(position.entry_signal_index),
        "entry_market_index": int(position.entry_market_index),
        "observed_exit_signal_timestamp": pd.Timestamp(market.iloc[observed_market_index]["timestamp"]),
        "observed_exit_signal_index": int(observed_market_index),
        "exit_market_index": int(exit_market_index),
        "holding_hours": int(exit_market_index - position.entry_market_index),
        "entry_reason": "signal_entry",
        "exit_reason": exit_reason,
        "direction": position.direction,
        "position_notional_usd": float(position.position_notional_usd),
        "signal_score_at_entry": position.signal_score,
        "predicted_class_at_entry": position.predicted_class,
        "expected_return_bps_at_entry": position.expected_return_bps,
        "confidence_at_entry": position.confidence,
        "metadata_json_at_entry": position.metadata_json,
        "perp_entry_price_raw": float(position.perp_entry_price_raw),
        "perp_exit_price_raw": float(perp_exit_price_raw),
        "spot_entry_price_raw": float(position.spot_entry_price_raw),
        "spot_exit_price_raw": float(spot_exit_price_raw),
        "funding_rate_sum": float(funding_sum),
        **pnl,
    }


def _simulate_strategy(
    strategy_frame: pd.DataFrame,
    market: pd.DataFrame,
    timestamp_to_market_index: dict[pd.Timestamp, int],
    funding_cumulative: pd.Series,
    settings: BacktestSettings,
) -> pd.DataFrame:
    if strategy_frame.empty:
        return pd.DataFrame()
    if strategy_frame["timestamp"].duplicated().any():
        raise ValueError(f"Strategy {strategy_frame['strategy_name'].iloc[0]} has duplicate timestamps in the signal table.")

    delay = int(settings.execution.entry_delay_bars)
    holding_hours = int(settings.execution.holding_window_hours)
    maximum_holding_hours = int(settings.execution.maximum_holding_hours)
    stop_loss_bps = settings.execution.stop_loss_bps
    take_profit_bps = settings.execution.take_profit_bps

    trades: list[dict[str, Any]] = []
    open_position: OpenPosition | None = None

    for _, row in strategy_frame.iterrows():
        current_market_index = timestamp_to_market_index.get(pd.Timestamp(row["timestamp"]))
        if current_market_index is None:
            continue

        exited_on_this_signal = False
        if open_position is not None:
            exit_candidates: list[tuple[int, int, str]] = []
            marked_return_bps = _mark_trade_return_bps(open_position, market, funding_cumulative, current_market_index, settings)

            if stop_loss_bps is not None and marked_return_bps <= -abs(float(stop_loss_bps)):
                exit_candidates.append((current_market_index + delay, 0, "stop_loss"))
            if take_profit_bps is not None and marked_return_bps >= abs(float(take_profit_bps)):
                exit_candidates.append((current_market_index + delay, 1, "take_profit"))

            planned_exit_market_index = open_position.entry_market_index + holding_hours
            if current_market_index + delay >= planned_exit_market_index:
                exit_candidates.append((planned_exit_market_index, 2, "holding_window"))

            maximum_exit_market_index = open_position.entry_market_index + maximum_holding_hours
            if current_market_index + delay >= maximum_exit_market_index:
                exit_candidates.append((maximum_exit_market_index, 3, "maximum_holding"))

            if settings.execution.exit_on_signal_off and not _entry_conditions_met(row, settings):
                exit_candidates.append((current_market_index + delay, 4, "signal_off"))

            valid_candidates = [candidate for candidate in exit_candidates if open_position.entry_market_index < candidate[0] < len(market)]
            if valid_candidates:
                exit_market_index, _, exit_reason = sorted(valid_candidates, key=lambda item: (item[0], item[1]))[0]
                trades.append(
                    _close_position(
                        open_position,
                        exit_market_index=exit_market_index,
                        exit_reason=exit_reason,
                        observed_market_index=current_market_index,
                        market=market,
                        funding_cumulative=funding_cumulative,
                        settings=settings,
                    )
                )
                open_position = None
                exited_on_this_signal = True

        if exited_on_this_signal:
            continue

        if open_position is None and _entry_conditions_met(row, settings):
            entry_market_index = current_market_index + delay
            if entry_market_index >= len(market) - 1:
                continue
            open_position = _open_position(row, market, entry_market_index, settings)

    if open_position is not None:
        final_exit_market_index = len(market) - 1
        if final_exit_market_index > open_position.entry_market_index:
            trades.append(
                _close_position(
                    open_position,
                    exit_market_index=final_exit_market_index,
                    exit_reason="end_of_data",
                    observed_market_index=final_exit_market_index,
                    market=market,
                    funding_cumulative=funding_cumulative,
                    settings=settings,
                )
            )

    trade_log = pd.DataFrame(trades)
    if trade_log.empty:
        return pd.DataFrame(
            columns=[
                "strategy_name",
                "source",
                "source_subtype",
                "task",
                "signal_timestamp",
                "signal_split",
                "entry_timestamp",
                "exit_timestamp",
                "entry_signal_index",
                "entry_market_index",
                "observed_exit_signal_timestamp",
                "observed_exit_signal_index",
                "exit_market_index",
                "holding_hours",
                "entry_reason",
                "exit_reason",
                "direction",
                "position_notional_usd",
                "signal_score_at_entry",
                "predicted_class_at_entry",
                "expected_return_bps_at_entry",
                "confidence_at_entry",
                "metadata_json_at_entry",
                "perp_entry_price_raw",
                "perp_exit_price_raw",
                "spot_entry_price_raw",
                "spot_exit_price_raw",
                "funding_rate_sum",
                "perp_entry_price_effective",
                "perp_exit_price_effective",
                "spot_entry_price_effective",
                "spot_exit_price_effective",
                "perp_quantity",
                "spot_quantity",
                "perp_leg_pnl_usd",
                "spot_leg_pnl_usd",
                "funding_pnl_usd",
                "gross_pnl_usd",
                "trading_fees_usd",
                "gas_cost_usd",
                "other_friction_usd",
                "estimated_slippage_cost_usd",
                "net_pnl_usd",
                "gross_return_bps",
                "net_return_bps",
                "turnover_usd",
            ]
        )
    return trade_log.sort_values(["entry_timestamp", "exit_timestamp"]).reset_index(drop=True)


def build_realized_equity_curve(
    market_timestamps: pd.Series,
    trade_log: pd.DataFrame,
    *,
    initial_capital: float,
    strategy_name: str,
) -> pd.DataFrame:
    """Build a realized-PnL equity curve from closed trades only."""
    timestamps = pd.to_datetime(market_timestamps, utc=True)
    pnl_events = pd.Series(0.0, index=range(len(timestamps)), dtype="float64")
    if not trade_log.empty:
        for _, trade in trade_log.iterrows():
            pnl_events.iloc[int(trade["exit_market_index"])] += float(trade["net_pnl_usd"])
    equity = float(initial_capital) + pnl_events.cumsum()
    curve = pd.DataFrame(
        {
            "timestamp": timestamps,
            "strategy_name": strategy_name,
            "realized_pnl_event_usd": pnl_events.to_numpy(dtype=float),
            "equity_usd": equity.to_numpy(dtype=float),
        }
    )
    curve["period_return"] = curve["equity_usd"].pct_change().fillna(0.0)
    curve["cumulative_return"] = curve["equity_usd"] / float(initial_capital) - 1.0
    curve["drawdown"] = curve["equity_usd"] / curve["equity_usd"].cummax() - 1.0
    return curve


def _annualized_return(equity_curve: pd.DataFrame, initial_capital: float) -> float:
    if equity_curve.empty:
        return 0.0
    final_equity = float(equity_curve["equity_usd"].iloc[-1])
    periods = max(len(equity_curve) - 1, 0)
    if periods <= 0 or initial_capital <= 0 or final_equity <= 0:
        return 0.0
    total_growth = final_equity / float(initial_capital)
    return float(total_growth ** (PERIODS_PER_YEAR_1H / periods) - 1.0)


def summarize_strategy_backtest(
    *,
    strategy_name: str,
    source: str,
    source_subtype: str,
    task: str,
    equity_curve: pd.DataFrame,
    trade_log: pd.DataFrame,
    initial_capital: float,
) -> dict[str, Any]:
    """Summarize a realized backtest into report-friendly metrics."""
    trade_count = int(len(trade_log))
    win_rate = float((trade_log["net_pnl_usd"] > 0).mean()) if trade_count else 0.0
    average_trade_return_bps = float(trade_log["net_return_bps"].mean()) if trade_count else 0.0
    average_trade_pnl_usd = float(trade_log["net_pnl_usd"].mean()) if trade_count else 0.0
    total_turnover_usd = float(trade_log["turnover_usd"].sum()) if trade_count else 0.0
    total_fees_usd = float(trade_log["trading_fees_usd"].sum()) if trade_count else 0.0
    total_gas_cost_usd = float(trade_log["gas_cost_usd"].sum()) if trade_count else 0.0
    total_other_friction_usd = float(trade_log["other_friction_usd"].sum()) if trade_count else 0.0
    total_funding_pnl_usd = float(trade_log["funding_pnl_usd"].sum()) if trade_count else 0.0
    total_gross_pnl_usd = float(trade_log["gross_pnl_usd"].sum()) if trade_count else 0.0
    total_net_pnl_usd = float(trade_log["net_pnl_usd"].sum()) if trade_count else 0.0
    average_holding_hours = float(trade_log["holding_hours"].mean()) if trade_count else 0.0
    final_equity = float(equity_curve["equity_usd"].iloc[-1]) if not equity_curve.empty else float(initial_capital)
    total_return = calculate_total_return(equity_curve["period_return"]) if not equity_curve.empty else 0.0
    annualized_return = _annualized_return(equity_curve, initial_capital)
    sharpe_ratio = calculate_sharpe_ratio(equity_curve["period_return"], periods_per_year=PERIODS_PER_YEAR_1H) if not equity_curve.empty else 0.0
    max_drawdown = calculate_max_drawdown(equity_curve["equity_usd"]) if not equity_curve.empty else 0.0
    active_signal_count = int(trade_log["entry_timestamp"].count())
    return {
        "strategy_name": strategy_name,
        "source": source,
        "source_subtype": source_subtype,
        "task": task,
        "trade_count": trade_count,
        "active_position_count": active_signal_count,
        "cumulative_return": float(total_return),
        "annualized_return": float(annualized_return),
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": float(max_drawdown),
        "win_rate": float(win_rate),
        "average_trade_return_bps": float(average_trade_return_bps),
        "average_trade_pnl_usd": float(average_trade_pnl_usd),
        "average_holding_hours": float(average_holding_hours),
        "total_turnover_usd": float(total_turnover_usd),
        "total_fees_usd": float(total_fees_usd),
        "total_gas_cost_usd": float(total_gas_cost_usd),
        "total_other_friction_usd": float(total_other_friction_usd),
        "total_funding_pnl_usd": float(total_funding_pnl_usd),
        "total_gross_pnl_usd": float(total_gross_pnl_usd),
        "total_net_pnl_usd": float(total_net_pnl_usd),
        "final_equity_usd": float(final_equity),
    }


def _split_trade_summary(trade_log: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "strategy_name",
        "signal_split",
        "trade_count",
        "win_rate",
        "average_trade_return_bps",
        "average_holding_hours",
        "total_turnover_usd",
        "total_funding_pnl_usd",
        "total_net_pnl_usd",
    ]
    if trade_log.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict[str, Any]] = []
    for (strategy_name, signal_split), group in trade_log.groupby(["strategy_name", "signal_split"], dropna=False):
        rows.append(
            {
                "strategy_name": strategy_name,
                "signal_split": signal_split,
                "trade_count": int(len(group)),
                "win_rate": float((group["net_pnl_usd"] > 0).mean()) if len(group) else 0.0,
                "average_trade_return_bps": float(group["net_return_bps"].mean()) if len(group) else 0.0,
                "average_holding_hours": float(group["holding_hours"].mean()) if len(group) else 0.0,
                "total_turnover_usd": float(group["turnover_usd"].sum()),
                "total_funding_pnl_usd": float(group["funding_pnl_usd"].sum()),
                "total_net_pnl_usd": float(group["net_pnl_usd"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["strategy_name", "signal_split"]).reset_index(drop=True)


def _resolve_output_dir(settings: BacktestSettings) -> Path:
    return ensure_directory(
        _resolve_path(settings.reporting.output_dir)
        / settings.input.provider
        / settings.input.symbol.lower()
        / settings.input.frequency
        / settings.reporting.run_name
    )


def _write_frame(frame: pd.DataFrame, path: Path) -> str:
    if path.suffix.lower() == ".parquet":
        frame.to_parquet(path, index=False)
    elif path.suffix.lower() == ".csv":
        frame.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")
    return str(path)


def _dataframe_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "| Note |\n| --- |\n| No rows available |"
    columns = list(frame.columns)
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for record in frame.astype(object).where(pd.notna(frame), "").to_dict(orient="records"):
        rows.append("| " + " | ".join(str(record[column]) for column in columns) + " |")
    return "\n".join([header, divider, *rows])


def _apply_plot_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")


def _plot_cumulative_returns(equity_curve: pd.DataFrame, leaderboard: pd.DataFrame, output_path: Path, *, top_n: int, dpi: int) -> str:
    _apply_plot_style()
    fig, ax = plt.subplots(figsize=(14, 6))
    top = leaderboard.head(max(top_n, 1))
    for color_index, strategy_name in enumerate(top["strategy_name"].tolist()):
        curve = equity_curve[equity_curve["strategy_name"] == strategy_name]
        if curve.empty:
            continue
        ax.plot(
            curve["timestamp"],
            curve["cumulative_return"] * 100.0,
            label=strategy_name,
            linewidth=1.8,
            color=PLOT_COLORS[color_index % len(PLOT_COLORS)],
        )
    ax.set_title("Cumulative Return by Strategy")
    ax.set_ylabel("Cumulative return (%)")
    ax.set_xlabel("Timestamp")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)


def _plot_drawdowns(equity_curve: pd.DataFrame, leaderboard: pd.DataFrame, output_path: Path, *, top_n: int, dpi: int) -> str:
    _apply_plot_style()
    fig, ax = plt.subplots(figsize=(14, 6))
    top = leaderboard.head(max(top_n, 1))
    for color_index, strategy_name in enumerate(top["strategy_name"].tolist()):
        curve = equity_curve[equity_curve["strategy_name"] == strategy_name]
        if curve.empty:
            continue
        ax.plot(
            curve["timestamp"],
            curve["drawdown"] * 100.0,
            label=strategy_name,
            linewidth=1.5,
            color=PLOT_COLORS[color_index % len(PLOT_COLORS)],
        )
    ax.set_title("Realized Drawdown by Strategy")
    ax.set_ylabel("Drawdown (%)")
    ax.set_xlabel("Timestamp")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)


def _plot_trade_return_boxplot(trade_log: pd.DataFrame, leaderboard: pd.DataFrame, output_path: Path, *, top_n: int, dpi: int) -> str:
    _apply_plot_style()
    fig, ax = plt.subplots(figsize=(12, 6))
    top_names = leaderboard.head(max(top_n, 1))["strategy_name"].tolist()
    if trade_log.empty or "strategy_name" not in trade_log.columns or "net_return_bps" not in trade_log.columns:
        ax.text(0.5, 0.5, "No trades available", ha="center", va="center")
        ax.set_axis_off()
    else:
        filtered = trade_log[trade_log["strategy_name"].isin(top_names)].copy()
        if filtered.empty:
            ax.text(0.5, 0.5, "No trades available", ha="center", va="center")
            ax.set_axis_off()
            fig.tight_layout()
            fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
            plt.close(fig)
            return str(output_path)
        ordered_groups = [filtered.loc[filtered["strategy_name"] == name, "net_return_bps"].astype(float).to_numpy() for name in top_names]
        ax.boxplot(ordered_groups, labels=top_names, patch_artist=True)
        ax.set_ylabel("Net trade return (bps)")
        ax.set_title("Trade Return Distribution")
        ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return str(output_path)


def _load_manifest(path_text: str | Path | None) -> dict[str, Any] | None:
    if path_text is None:
        return None
    path = _resolve_path(path_text)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown_report(
    settings: BacktestSettings,
    strategy_metrics: pd.DataFrame,
    split_summary: pd.DataFrame,
    figure_paths: list[str],
    signal_manifest: dict[str, Any] | None,
    market_manifest: dict[str, Any] | None,
) -> str:
    assumptions = [
        f"Signals are observed at timestamp `t` and executed after `{settings.execution.entry_delay_bars}` bar(s) using `{settings.execution.execution_price_field}` prices.",
        f"Direction is fixed to `{settings.selection.direction}` for this run.",
        f"Delta-neutral abstraction uses fixed per-leg notional of `{settings.portfolio.position_notional}` USD.",
        "PnL includes explicit perp-leg, spot-leg, and funding components.",
        f"Trading fees use taker fee `{settings.costs.taker_fee_bps}` bps on all four round-trip transactions.",
        f"Slippage is modeled through adverse execution prices using `{settings.costs.slippage_bps}` bps.",
        f"Gas cost is `{settings.costs.gas_cost_usd}` USD per closed trade.",
        "Equity curve in this first version is realized-PnL based rather than full intratrade mark-to-market.",
    ]
    figure_markdown = "\n".join(f"![{Path(path).stem}](figures/{Path(path).name})" for path in figure_paths)
    manifest_lines = ""
    if signal_manifest is not None:
        manifest_lines += f"- Signal rows: `{signal_manifest.get('summary', {}).get('row_count', 'n/a')}`\n"
        manifest_lines += f"- Active signal count: `{signal_manifest.get('summary', {}).get('active_signal_count', 'n/a')}`\n"
    if market_manifest is not None:
        manifest_lines += f"- Canonical market rows: `{market_manifest.get('canonical_row_count', 'n/a')}`\n"

    top_metrics = (
        strategy_metrics[
            [
                "strategy_name",
                "trade_count",
                "cumulative_return",
                "annualized_return",
                "sharpe_ratio",
                "max_drawdown",
                "win_rate",
                "average_trade_return_bps",
                "total_net_pnl_usd",
            ]
        ].copy()
        if not strategy_metrics.empty
        else pd.DataFrame()
    )

    return f"""# Backtest Report

## Overview

- Symbol: `{settings.input.symbol}`
- Provider: `{settings.input.provider}`
- Frequency: `{settings.input.frequency}`
- Signal artifact: `{settings.input.signal_path}`
- Market dataset: `{settings.input.market_dataset_path}`
- Output root: `{settings.reporting.output_dir}`
{manifest_lines}
## Simplifying Assumptions

""" + "\n".join(f"- {line}" for line in assumptions) + f"""

## Strategy Summary

{_dataframe_to_markdown(top_metrics.round(6))}

## Split Summary

{_dataframe_to_markdown(split_summary.round(6))}

## Figures

{figure_markdown}
"""


def run_backtest_pipeline(settings: BacktestSettings) -> BacktestArtifacts:
    """Run the explicit delta-neutral prototype backtest."""
    if int(settings.portfolio.max_open_positions) != 1:
        raise ValueError("The first backtest version supports max_open_positions = 1 only.")
    if settings.execution.allow_partial_exit:
        raise ValueError("The first backtest version does not support partial exits.")
    if settings.execution.maximum_holding_hours < settings.execution.holding_window_hours:
        raise ValueError("maximum_holding_hours must be greater than or equal to holding_window_hours.")

    signals = _load_signal_table(settings)
    market = _load_market_table(settings)
    timestamp_to_market_index = {
        pd.Timestamp(timestamp): index for index, timestamp in enumerate(pd.to_datetime(market["timestamp"], utc=True))
    }
    signals = signals[signals["timestamp"].isin(timestamp_to_market_index)].copy()
    if signals.empty:
        raise ValueError("No signal timestamps overlap with the market dataset.")

    selected_market = market.loc[market["timestamp"] >= signals["timestamp"].min()].reset_index(drop=True)
    selected_index_map = {pd.Timestamp(timestamp): index for index, timestamp in enumerate(pd.to_datetime(selected_market["timestamp"], utc=True))}
    signals = signals[signals["timestamp"].isin(selected_index_map)].copy()
    signals["market_index"] = signals["timestamp"].map(selected_index_map).astype(int)
    funding_cumulative = pd.to_numeric(selected_market["funding_rate"], errors="coerce").fillna(0.0).cumsum()

    trade_logs: list[pd.DataFrame] = []
    equity_curves: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []

    for strategy_name, strategy_frame in signals.groupby("strategy_name", sort=True):
        strategy_frame = strategy_frame.sort_values("timestamp").reset_index(drop=True)
        trade_log = _simulate_strategy(strategy_frame, selected_market, selected_index_map, funding_cumulative, settings)
        if not trade_log.empty:
            trade_log["trade_id"] = np.arange(1, len(trade_log) + 1, dtype=int)
        trade_logs.append(trade_log)

        strategy_source = str(strategy_frame["source"].iloc[0])
        strategy_subtype = str(strategy_frame["source_subtype"].iloc[0])
        strategy_task = str(strategy_frame["task"].iloc[0])
        equity_curve = build_realized_equity_curve(
            selected_market["timestamp"],
            trade_log,
            initial_capital=settings.portfolio.initial_capital,
            strategy_name=strategy_name,
        )
        equity_curve["source"] = strategy_source
        equity_curve["source_subtype"] = strategy_subtype
        equity_curves.append(equity_curve)
        metric_rows.append(
            summarize_strategy_backtest(
                strategy_name=strategy_name,
                source=strategy_source,
                source_subtype=strategy_subtype,
                task=strategy_task,
                equity_curve=equity_curve,
                trade_log=trade_log,
                initial_capital=settings.portfolio.initial_capital,
            )
        )

    non_empty_trade_logs = [frame for frame in trade_logs if not frame.empty]
    if non_empty_trade_logs:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            trade_log_frame = pd.concat(non_empty_trade_logs, ignore_index=True)
    else:
        trade_log_frame = pd.DataFrame()
    equity_curve_frame = pd.concat(equity_curves, ignore_index=True) if equity_curves else pd.DataFrame()
    strategy_metrics = (
        pd.DataFrame(metric_rows).sort_values(["sharpe_ratio", "cumulative_return"], ascending=[False, False]).reset_index(drop=True)
        if metric_rows
        else pd.DataFrame()
    )
    split_summary = _split_trade_summary(trade_log_frame)
    leaderboard = (
        strategy_metrics[
            [
                "strategy_name",
                "source",
                "source_subtype",
                "task",
                "trade_count",
                "cumulative_return",
                "annualized_return",
                "sharpe_ratio",
                "max_drawdown",
                "win_rate",
                "average_trade_return_bps",
                "total_net_pnl_usd",
                "final_equity_usd",
            ]
        ].copy()
        if not strategy_metrics.empty
        else pd.DataFrame()
    )

    output_dir = _resolve_output_dir(settings)
    figures_dir = ensure_directory(output_dir / "figures")

    trade_log_path = _write_frame(trade_log_frame, output_dir / "trade_log.parquet")
    equity_curve_path = _write_frame(equity_curve_frame, output_dir / "equity_curve.parquet")
    strategy_metrics_path = _write_frame(strategy_metrics, output_dir / "strategy_metrics.parquet")
    split_summary_path = _write_frame(split_summary, output_dir / "split_summary.parquet")
    leaderboard_path = _write_frame(leaderboard, output_dir / "leaderboard.parquet")

    trade_log_csv_path = _write_frame(trade_log_frame, output_dir / "trade_log.csv") if settings.reporting.write_csv else None
    equity_curve_csv_path = _write_frame(equity_curve_frame, output_dir / "equity_curve.csv") if settings.reporting.write_csv else None
    strategy_metrics_csv_path = _write_frame(strategy_metrics, output_dir / "strategy_metrics.csv") if settings.reporting.write_csv else None
    split_summary_csv_path = _write_frame(split_summary, output_dir / "split_summary.csv") if settings.reporting.write_csv else None
    leaderboard_csv_path = _write_frame(leaderboard, output_dir / "leaderboard.csv") if settings.reporting.write_csv else None

    figure_paths: list[str] = []
    if not equity_curve_frame.empty and not leaderboard.empty:
        figure_paths.append(
            _plot_cumulative_returns(
                equity_curve_frame,
                leaderboard,
                figures_dir / f"cumulative_returns.{settings.reporting.figure_format}",
                top_n=settings.reporting.top_n_strategies_for_plots,
                dpi=settings.reporting.dpi,
            )
        )
        figure_paths.append(
            _plot_drawdowns(
                equity_curve_frame,
                leaderboard,
                figures_dir / f"drawdowns.{settings.reporting.figure_format}",
                top_n=settings.reporting.top_n_strategies_for_plots,
                dpi=settings.reporting.dpi,
            )
        )
    figure_paths.append(
        _plot_trade_return_boxplot(
            trade_log_frame,
            leaderboard,
            figures_dir / f"trade_return_boxplot.{settings.reporting.figure_format}",
            top_n=settings.reporting.top_n_strategies_for_plots,
            dpi=settings.reporting.dpi,
        )
    )

    signal_manifest = _load_manifest(settings.input.signal_manifest_path)
    market_manifest = _load_manifest(settings.input.market_manifest_path)
    report_path: str | None = None
    if settings.reporting.write_markdown_report:
        report_text = _build_markdown_report(settings, strategy_metrics, split_summary, figure_paths, signal_manifest, market_manifest)
        report_file = output_dir / "backtest_report.md"
        report_file.write_text(report_text, encoding="utf-8")
        report_path = str(report_file)

    manifest = {
        "input": settings.input.model_dump(),
        "selection": settings.selection.model_dump(),
        "portfolio": settings.portfolio.model_dump(),
        "costs": settings.costs.model_dump(),
        "execution": settings.execution.model_dump(),
        "reporting": settings.reporting.model_dump(),
        "summary": {
            "strategy_count": int(strategy_metrics["strategy_name"].nunique()) if not strategy_metrics.empty else 0,
            "trade_count": int(len(trade_log_frame)),
            "best_strategy": None if leaderboard.empty else str(leaderboard.iloc[0]["strategy_name"]),
            "best_sharpe_ratio": None if leaderboard.empty else float(leaderboard.iloc[0]["sharpe_ratio"]),
            "best_cumulative_return": None if leaderboard.empty else float(leaderboard.iloc[0]["cumulative_return"]),
        },
        "signal_manifest": signal_manifest,
        "market_manifest": market_manifest,
        "artifacts": {
            "trade_log_path": trade_log_path,
            "equity_curve_path": equity_curve_path,
            "strategy_metrics_path": strategy_metrics_path,
            "split_summary_path": split_summary_path,
            "leaderboard_path": leaderboard_path,
            "report_path": report_path,
            "figure_paths": figure_paths,
        },
        "assumptions": [
            "Single-asset, delta-neutral prototype with at most one open position per strategy.",
            "Signals at timestamp t are executed after entry_delay_bars using the configured execution price field.",
            "Equity curve is realized-PnL based rather than full intratrade mark-to-market.",
            "Funding PnL uses summed realized funding_rate rows between entry and exit execution timestamps.",
            "Trading fees use taker_fee_bps on all four round-trip leg transactions.",
            "Slippage is modeled by adverse execution prices, not by a separate extra deduction.",
        ],
    }
    manifest_path = output_dir / "backtest_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return BacktestArtifacts(
        output_dir=str(output_dir),
        trade_log_path=trade_log_path,
        trade_log_csv_path=trade_log_csv_path,
        equity_curve_path=equity_curve_path,
        equity_curve_csv_path=equity_curve_csv_path,
        strategy_metrics_path=strategy_metrics_path,
        strategy_metrics_csv_path=strategy_metrics_csv_path,
        split_summary_path=split_summary_path,
        split_summary_csv_path=split_summary_csv_path,
        leaderboard_path=leaderboard_path,
        leaderboard_csv_path=leaderboard_csv_path,
        report_path=report_path,
        figure_paths=figure_paths,
        manifest_path=str(manifest_path),
    )
