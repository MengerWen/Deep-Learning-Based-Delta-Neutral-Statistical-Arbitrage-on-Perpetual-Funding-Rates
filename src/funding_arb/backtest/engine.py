"""Scaffold helpers for backtest execution."""

from __future__ import annotations

from typing import Any


def describe_backtest_job(config: dict[str, Any]) -> str:
    """Return a summary of the configured backtest scaffold."""
    portfolio = config.get("portfolio", {})
    costs = config.get("costs", {})
    initial_capital = portfolio.get("initial_capital", "unknown")
    fee_bps = costs.get("taker_fee_bps", "unknown")
    slippage_bps = costs.get("slippage_bps", "unknown")

    return (
        f"Backtest scaffold ready with initial capital {initial_capital}, "
        f"taker fee {fee_bps} bps, and slippage {slippage_bps} bps. "
        "Implement order accounting and funding accrual logic next."
    )

