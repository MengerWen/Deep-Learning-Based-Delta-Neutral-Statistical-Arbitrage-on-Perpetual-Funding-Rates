# Unified Signals

## Purpose

This module standardizes strategy and model outputs into one clean signal interface for downstream backtesting and demo components.

Instead of making the backtest engine understand several artifact formats, we normalize everything into the same signal table.

Current supported upstream sources:

- rule-based signals from the baseline prediction artifact
- baseline ML signals from the baseline prediction artifact
- deep-learning signals from the deep-learning prediction artifact

## Common Signal Representation

Every normalized signal row contains these columns:

- `timestamp`
- `asset`
- `venue`
- `frequency`
- `source`
- `source_subtype`
- `strategy_name`
- `model_family`
- `task`
- `signal_score`
- `predicted_class`
- `expected_return_bps`
- `signal_threshold`
- `threshold_objective`
- `prediction_mode`
- `calibration_method`
- `feature_importance_method`
- `selected_hyperparameters_json`
- `suggested_direction`
- `confidence`
- `should_trade`
- `split`
- `metadata_json`

Interpretation:

- `signal_score`
  Generic ranking score. It is currently based on upstream `signal_strength`, which measures distance from the decision threshold.
- `predicted_class`
  Usually `0/1` when a classifier or threshold rule is used.
- `expected_return_bps`
  Predicted future net return when a regression-style model is used.
- `signal_threshold`
  The threshold actually applied upstream when converting scores into tradeable signals.
- `threshold_objective`
  The validation objective used to choose that threshold when threshold search is enabled.
- `prediction_mode`
  Whether the source used static scoring or a more chronological expanding/rolling prediction path.
- `calibration_method`
  Probability calibration choice for classifier baselines when applicable.
- `feature_importance_method`
  The preferred feature-importance diagnostic attached to that model family.
- `selected_hyperparameters_json`
  Serialized chosen hyperparameters from the upstream baseline training artifact.
- `suggested_direction`
  `short_perp_long_spot` when the source says trade, otherwise `flat`.
- `confidence`
  Predicted probability when available. It is left null for regression sources.
- `metadata_json`
  Serialized raw context such as decision score, threshold, actual label/return if present, and source path.

## Source Adapters

### Baseline adapter

Input artifact:

- `baseline_predictions.parquet`

Supported source names:

- `baseline`
  Includes both rule-based and ML baseline rows.
- `rules`
  Only keeps `model_family == rule_based`.
- `baseline-ml`
  Only keeps predictive baseline rows.

This design lets one upstream baseline artifact serve several downstream views without duplicating training logic.

### Deep-learning adapter

Input artifact:

- `dl_predictions.parquet`

Supported source name:

- `dl`

The adapter maps LSTM outputs into the same signal schema. In regression mode, `expected_return_bps` is populated; in classification mode, `confidence` is populated.

## Output Layout

Default output directory pattern:

`data/artifacts/signals/<provider>/<symbol>/<frequency>/<source>/`

Example:

- `data/artifacts/signals/binance/btcusdt/1h/baseline/signals.parquet`
- `data/artifacts/signals/binance/btcusdt/1h/dl/signals.parquet`

Each run writes:

- normalized signal table in parquet
- optional CSV copy
- `signals_manifest.json`

The manifest includes summary stats such as row count, active signal count, strategies present, source subtype breakdown, and strategy-level metadata previews for thresholds, calibration, and prediction mode.

## CLI

Generate normalized signals from baseline outputs:

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main generate-signals --source baseline
```

Generate only rule-based signals:

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main generate-signals --source rules
```

Generate normalized signals from deep-learning outputs:

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main generate-signals --source dl
```

Wrapper script:

```powershell
& 'd:\MG\anaconda3\python.exe' scripts\signals\generate_signals.py --source baseline
```

## Why This Layer Matters

The signal layer separates prediction logic from trading logic.

That gives us three advantages:

1. The backtest engine can consume one schema regardless of whether a signal came from a threshold rule, logistic regression, ridge regression, or LSTM.
2. The frontend/demo layer can show signals consistently without knowing training details.
3. New model families can be added later by writing only one adapter, instead of changing every downstream module.

## Recommended Ownership

- schemas and adapters:
  `src/funding_arb/signals/schemas.py`
  `src/funding_arb/signals/adapters.py`
- pipeline and artifacts:
  `src/funding_arb/signals/pipeline.py`
- config and CLI:
  `configs/signals/default.yaml`
  `src/funding_arb/config/models.py`
  `src/funding_arb/config/loader.py`
  `src/funding_arb/cli.py`
- docs:
  `docs/signals.md`

## Caveats

- The current signal interface is single-asset and single-direction oriented around `short_perp_long_spot` vs `flat`.
- Confidence is naturally better defined for classification models than for regression models.
- The normalized signal layer now keeps the most important baseline-training decisions as first-class columns so backtesting and robustness reporting can stay finance-aware without reparsing JSON blobs.
- The full raw prediction context still remains available inside `metadata_json` for diagnostics.
