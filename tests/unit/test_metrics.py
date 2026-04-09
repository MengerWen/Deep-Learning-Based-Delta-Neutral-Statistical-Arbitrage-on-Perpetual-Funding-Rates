from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from funding_arb.evaluation.metrics import (
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_total_return,
)


class MetricsTests(unittest.TestCase):
    def test_calculate_total_return_compounds(self) -> None:
        result = calculate_total_return([0.10, -0.05])
        self.assertTrue(math.isclose(result, 0.045, rel_tol=1e-9))

    def test_calculate_sharpe_ratio_returns_zero_for_flat_returns(self) -> None:
        result = calculate_sharpe_ratio([0.0, 0.0, 0.0], periods_per_year=252)
        self.assertEqual(result, 0.0)

    def test_calculate_max_drawdown_tracks_peak_to_trough(self) -> None:
        result = calculate_max_drawdown([100.0, 110.0, 90.0, 95.0])
        self.assertTrue(math.isclose(result, -0.1818181818, rel_tol=1e-6))


if __name__ == "__main__":
    unittest.main()
