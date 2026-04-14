# Deep Learning Models

## Purpose

This module is the first sequence-modeling layer for the project. It is designed to answer a practical question:

Can a small time-series model learn better post-cost opportunity signals from the engineered hourly feature set than simple rule-based and linear baselines?

The implementation deliberately stays small, but it is no longer locked to one exact architecture. The current default is still `LSTM`, and a lightweight `GRU` option is now available through the same builder/CLI path.

## Default Task Setup

The default config uses regression rather than classification:

- task: `regression`
- target column: `target_future_net_return_bps_24h`
- reference classification column: `target_is_profitable_24h`
- lookback window: `48` hourly steps

Why regression first:

- the 24-hour net-return target is less sparse than the positive classification labels
- it gives a ranked expected-return output that is easy to feed into later backtests
- it still stays aligned with tradable post-cost opportunity quality

The same pipeline also supports classification by changing `target.task` and `target.column` in `configs/models/lstm.yaml`.

## Architecture

Implemented sequence models:

- `LSTMSequenceModel`
- `GRUSequenceModel`
- encoder: stacked LSTM with `batch_first=True`
- representation: final hidden state from the last LSTM layer
- head: dropout + linear projection to one scalar output

Default hyperparameters:

- hidden size: `64`
- layers: `2`
- dropout: `0.1`
- bidirectional: `false`

The model builder is dispatch-based, so new sequence encoders can be added later without changing sequence construction, artifact format, or CLI usage.

## Training and Selection Logic

The first prototype selected checkpoints only by validation loss. The upgraded version is more research-oriented.

It now supports configurable checkpoint selection metrics such as:

- `validation_loss`
- `validation_f1`
- `validation_roc_auc`
- `validation_pearson_corr`
- `validation_avg_signal_return_bps`
- `validation_signal_hit_rate`
- `validation_cumulative_signal_return_bps`

For the default regression experiment, the config now uses a trading-aware selection metric so the saved checkpoint is chosen with signal usefulness in mind rather than loss alone.

If a trading-oriented validation metric is undefined because a given epoch produces zero traded signals, the pipeline falls back to `validation_loss` for checkpoint comparison. That fallback is recorded in the training history and manifest so the selection behavior stays auditable.

Thresholds are also no longer fixed-only. The module can search thresholds on the validation split:

- probability thresholds for classification
- predicted-return thresholds for regression

The default threshold objective is `avg_signal_return_bps`.

## Input Shape

The model consumes a 3D tensor with shape:

`[batch_size, lookback_steps, feature_count]`

Under the current default config:

- `lookback_steps = 48`
- `feature_count` is determined from the supervised dataset after leakage-safe feature selection

Each target row uses:

- the feature row at time `t`
- the preceding `lookback_steps - 1` rows
- no future rows

That means the sequence ending at time `t` predicts the label already aligned by the supervised dataset pipeline, so there is no future leakage from sequence construction.

## Time-Series Safety

The deep-learning data path is intentionally conservative:

- rows are sorted strictly by timestamp before sequence construction
- only rows with `supervised_ready == 1` are eligible as targets
- feature normalization is fit on the training split only
- missing and infinite values are handled before tensor conversion
- validation and test sequences use earlier historical rows only
- no future labels or future features are exposed to the model

By default, `allow_cross_split_context = true`. This means a validation or test target may use preceding historical rows from earlier splits as context. This is intentional and realistic: when we score a later time, we do know the earlier market history.

## Outputs

Default output directory:

`data/artifacts/models/dl/binance/btcusdt/1h/lstm_regression_24h_default/`

Key artifacts:

- `best_model.pt`
  Best checkpoint selected by the configured validation metric.
- `training_history.csv`
  Per-epoch train/validation loss, selected threshold, selection score, and strategy-oriented metrics.
- `dl_predictions.parquet`
  Row-level predictions and trading signals.
- `dl_metrics.parquet`
  Split-level evaluation summary.
- `dl_leaderboard.parquet`
  Validation/test leaderboard view.
- `feature_columns.json`
  Exact input feature list.
- `feature_normalization.json`
  Training-only normalization statistics.
- `training_report.md`
  Lightweight experiment report.
- `dl_manifest.json`
  Reproducibility summary including selected loss, threshold, configured checkpoint metric, effective checkpoint metric, prediction mode, preprocessing, and tuning settings.

Additional diagnostics may also be written under `diagnostics/`, including:

- threshold-search tables
- tuning results when enabled
- classification calibration tables
- feature-group ablation summaries

## Prediction Output Contract

The prediction table follows the same general format as the baseline pipeline so later backtests can consume both:

- `timestamp`
- `split`
- `model_name`
- `model_family`
- `task`
- `signal`
- `decision_score`
- `signal_threshold`
- `signal_strength`
- `predicted_probability`
- `predicted_return_bps`
- `actual_label`
- `actual_return_bps`

Additional metadata columns now include:

- `selected_hyperparameters_json`
- `selected_threshold_objective`
- `calibration_method`
- `feature_importance_method`
- `prediction_mode`

For regression:

- `decision_score` and `predicted_return_bps` are the same
- `signal = 1` when predicted return exceeds `trade_threshold_bps`

For classification:

- `decision_score` is the predicted probability
- `signal = 1` when probability exceeds `probability_threshold`

## CLI

Unified CLI:

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main train-dl --config configs/models/lstm.yaml
```

Wrapper script:

```powershell
& 'd:\MG\anaconda3\python.exe' scripts\models\train_dl.py --config configs/models/lstm.yaml
```

## How It Differs From Baselines

Baseline models treat each timestamp mostly as an independent row after feature engineering.
The LSTM instead learns from ordered windows of feature history.

In practice, that means the LSTM can model:

- short-term temporal persistence in funding and basis behavior
- multi-hour build-up and unwind patterns
- interactions that depend on sequence order rather than only the current row snapshot

At the same time, the current implementation remains lightweight:

- one model family
- one target at a time
- no distributed training
- no experiment server
- no complex scheduler stack

That keeps the module maintainable and appropriate for a course-project prototype.

## Walk-Forward and Robustness Hooks

The upgraded module also adds two realism/robustness hooks:

- optional tuning-ready time-series validation structure
- optional expanding / rolling prediction mode with periodic retraining

The default run still uses `prediction.mode = static` to keep the main experiment easy to reproduce, but the code is now prepared for more chronological scoring when needed.

Preprocessing can also be made more robust through:

- winsorization before scaling
- `standard` or `robust` scaling
- training-only fitted preprocessing statistics

## Interpretability

This is still not a SHAP-heavy deep-learning research stack, but the module now includes a practical interpretability path:

- feature-group ablation on validation/test predictions

Groups are taken from the feature manifest when available, and otherwise inferred heuristically from feature names.

## Caveats

- The current post-cost labels are intentionally hard, so model quality should be judged with both predictive metrics and realized signal-return diagnostics.
- This first version uses only engineered tabular features arranged into sequences; it does not yet include raw order-book or multi-asset sequence inputs.
- Tuning support is intentionally lightweight and disabled by default because full deep time-series hyperparameter search can become expensive quickly.
- Walk-forward mode is available, but the exported checkpoint still refers to the base train/validation model rather than every refit chunk.
- Transformer support is still not implemented.
