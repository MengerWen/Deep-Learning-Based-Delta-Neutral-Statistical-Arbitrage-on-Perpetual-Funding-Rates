"""Small, reusable performance metrics for the initial scaffold."""

from __future__ import annotations

import math
from typing import Iterable


def _to_list(values: Iterable[float]) -> list[float]:
    numbers = [float(value) for value in values]
    if not numbers:
        raise ValueError("Metric input cannot be empty.")
    return numbers


def calculate_total_return(returns: Iterable[float]) -> float:
    """Calculate compounded total return from periodic simple returns."""
    compounded = 1.0
    for value in _to_list(returns):
        compounded *= 1.0 + value
    return compounded - 1.0


def calculate_sharpe_ratio(
    returns: Iterable[float],
    periods_per_year: int = 365 * 24,
    risk_free_rate: float = 0.0,
) -> float:
    """Calculate a simple annualized Sharpe ratio."""
    values = _to_list(returns)
    adjustment = risk_free_rate / periods_per_year
    excess = [value - adjustment for value in values]
    mean = sum(excess) / len(excess)
    variance = sum((value - mean) ** 2 for value in excess) / len(excess)
    std = math.sqrt(variance)
    if math.isclose(std, 0.0):
        return 0.0
    return float((mean / std) * math.sqrt(periods_per_year))


def calculate_max_drawdown(equity_curve: Iterable[float]) -> float:
    """Calculate maximum drawdown from a sequence of equity values."""
    values = _to_list(equity_curve)
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = (value / peak) - 1.0
        max_drawdown = min(max_drawdown, drawdown)
    return max_drawdown
