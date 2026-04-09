from __future__ import annotations

import math

from funding_arb.evaluation.metrics import (
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_total_return,
)



def test_calculate_total_return_compounds() -> None:
    result = calculate_total_return([0.10, -0.05])
    assert math.isclose(result, 0.045, rel_tol=1e-9)



def test_calculate_sharpe_ratio_returns_zero_for_flat_returns() -> None:
    result = calculate_sharpe_ratio([0.0, 0.0, 0.0], periods_per_year=252)
    assert result == 0.0



def test_calculate_max_drawdown_tracks_peak_to_trough() -> None:
    result = calculate_max_drawdown([100.0, 110.0, 90.0, 95.0])
    assert math.isclose(result, -0.1818181818, rel_tol=1e-6)