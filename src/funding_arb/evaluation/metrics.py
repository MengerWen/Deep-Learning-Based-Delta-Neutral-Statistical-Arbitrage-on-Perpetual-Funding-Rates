"""Small, reusable performance metrics for the initial scaffold."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd



def _to_series(values: Iterable[float]) -> pd.Series:
    series = pd.Series(list(values), dtype="float64")
    if series.empty:
        raise ValueError("Metric input cannot be empty.")
    return series



def calculate_total_return(returns: Iterable[float]) -> float:
    """Calculate compounded total return from periodic simple returns."""
    series = _to_series(returns)
    return float((1.0 + series).prod() - 1.0)



def calculate_sharpe_ratio(
    returns: Iterable[float],
    periods_per_year: int = 365 * 24,
    risk_free_rate: float = 0.0,
) -> float:
    """Calculate a simple annualized Sharpe ratio."""
    series = _to_series(returns)
    excess = series - (risk_free_rate / periods_per_year)
    volatility = float(excess.std(ddof=0))
    if math.isclose(volatility, 0.0):
        return 0.0
    annualization = math.sqrt(periods_per_year)
    return float((excess.mean() / volatility) * annualization)



def calculate_max_drawdown(equity_curve: Iterable[float]) -> float:
    """Calculate maximum drawdown from a sequence of equity values."""
    series = _to_series(equity_curve)
    running_max = series.cummax()
    drawdown = (series / running_max) - 1.0
    return float(np.min(drawdown))