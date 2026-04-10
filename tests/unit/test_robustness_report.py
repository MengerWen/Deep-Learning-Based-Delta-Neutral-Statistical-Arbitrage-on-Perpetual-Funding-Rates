from __future__ import annotations

import pandas as pd

from funding_arb.reporting.robustness import _ablation_columns, _best_rows


def test_ablation_columns_resolve_feature_groups_and_aliases() -> None:
    group_catalog = {
        "funding": ["funding_rate_bps", "funding_zscore_24h"],
        "basis": ["spread_bps"],
        "interaction_state": ["funding_x_spread_bps"],
    }

    columns = _ablation_columns(
        group_catalog,
        feature_groups=["funding", "interaction"],
        extra_columns=["manual_feature"],
    )

    assert columns == [
        "funding_rate_bps",
        "funding_x_spread_bps",
        "funding_zscore_24h",
        "manual_feature",
    ]


def test_best_rows_selects_highest_ranked_strategy_per_group() -> None:
    frame = pd.DataFrame(
        {
            "family_name": ["rule_based", "rule_based", "baseline_ml", "baseline_ml"],
            "scenario_name": ["base", "base", "base", "base"],
            "strategy_name": ["a_rule", "b_rule", "ridge", "logistic"],
            "trade_count": [10, 12, 0, 7],
            "cumulative_return": [0.01, 0.03, 0.02, -0.01],
        }
    )

    best = _best_rows(frame, "cumulative_return", ["family_name", "scenario_name"])

    assert set(best["family_name"]) == {"rule_based", "baseline_ml"}
    assert (
        best.loc[best["family_name"] == "rule_based", "strategy_name"].iloc[0]
        == "b_rule"
    )
    assert (
        best.loc[best["family_name"] == "baseline_ml", "strategy_name"].iloc[0]
        == "logistic"
    )
