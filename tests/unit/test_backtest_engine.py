from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from funding_arb.backtest.engine import (
    _plot_trade_return_boxplot,
    build_realized_equity_curve,
    calculate_trade_pnl,
    summarize_strategy_backtest,
)


def test_calculate_trade_pnl_for_short_perp_long_spot_convergence_trade() -> None:
    pnl = calculate_trade_pnl(
        direction="short_perp_long_spot",
        position_notional_usd=10_000.0,
        perp_entry_price_raw=100.0,
        perp_exit_price_raw=99.0,
        spot_entry_price_raw=100.0,
        spot_exit_price_raw=101.0,
        funding_rate_sum=0.001,
        taker_fee_bps=0.0,
        slippage_bps=0.0,
        gas_cost_usd=0.0,
        other_friction_bps=0.0,
    )

    assert pnl["perp_leg_pnl_usd"] == pytest.approx(100.0)
    assert pnl["spot_leg_pnl_usd"] == pytest.approx(100.0)
    assert pnl["funding_pnl_usd"] == pytest.approx(10.0)
    assert pnl["gross_pnl_usd"] == pytest.approx(210.0)
    assert pnl["net_pnl_usd"] == pytest.approx(210.0)
    assert pnl["gross_return_bps"] == pytest.approx(210.0)


def test_calculate_trade_pnl_applies_explicit_cost_terms() -> None:
    pnl = calculate_trade_pnl(
        direction="short_perp_long_spot",
        position_notional_usd=10_000.0,
        perp_entry_price_raw=100.0,
        perp_exit_price_raw=100.0,
        spot_entry_price_raw=100.0,
        spot_exit_price_raw=100.0,
        funding_rate_sum=0.0,
        taker_fee_bps=5.0,
        slippage_bps=0.0,
        gas_cost_usd=2.0,
        other_friction_bps=1.0,
    )

    assert pnl["trading_fees_usd"] == pytest.approx(20.0)
    assert pnl["other_friction_usd"] == pytest.approx(1.0)
    assert pnl["net_pnl_usd"] == pytest.approx(-23.0)
    assert pnl["net_return_bps"] == pytest.approx(-23.0)


def test_realized_equity_curve_and_summary_metrics() -> None:
    timestamps = pd.date_range("2024-01-01", periods=4, freq="h", tz="UTC")
    trade_log = pd.DataFrame(
        {
            "entry_timestamp": [timestamps[0], timestamps[2]],
            "exit_market_index": [1, 3],
            "net_pnl_usd": [100.0, -50.0],
            "net_return_bps": [100.0, -50.0],
            "turnover_usd": [40_000.0, 40_000.0],
            "trading_fees_usd": [0.0, 0.0],
            "gas_cost_usd": [0.0, 0.0],
            "other_friction_usd": [0.0, 0.0],
            "funding_pnl_usd": [10.0, -5.0],
            "gross_pnl_usd": [100.0, -50.0],
            "holding_hours": [1, 1],
        }
    )

    equity_curve = build_realized_equity_curve(
        pd.Series(timestamps),
        trade_log,
        initial_capital=100_000.0,
        strategy_name="toy_strategy",
    )
    summary = summarize_strategy_backtest(
        strategy_name="toy_strategy",
        source="baseline",
        source_subtype="rule_based",
        task="classification",
        equity_curve=equity_curve,
        trade_log=trade_log,
        initial_capital=100_000.0,
    )

    assert equity_curve["equity_usd"].tolist() == pytest.approx(
        [100_000.0, 100_100.0, 100_100.0, 100_050.0]
    )
    assert summary["trade_count"] == 2
    assert summary["win_rate"] == pytest.approx(0.5)
    assert summary["total_net_pnl_usd"] == pytest.approx(50.0)
    assert summary["cumulative_return"] == pytest.approx(0.0005)
    assert summary["final_equity_usd"] == pytest.approx(100_050.0)


def test_trade_return_boxplot_handles_empty_trade_log() -> None:
    leaderboard = pd.DataFrame({"strategy_name": ["ridge_regression"]})
    scratch_dir = Path("tests/.tmp/backtest")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    output_path = scratch_dir / "boxplot.png"

    written = _plot_trade_return_boxplot(
        pd.DataFrame(),
        leaderboard,
        output_path,
        top_n=1,
        dpi=72,
    )

    assert written.endswith("boxplot.png")
    assert output_path.exists()
