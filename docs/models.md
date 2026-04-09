# Deep Learning Models

## Purpose

This module is the first sequence-modeling layer for the project. It is designed to answer a practical question:

Can a small time-series model learn better post-cost opportunity signals from the engineered hourly feature set than simple rule-based and linear baselines?

The implementation deliberately starts with one model family only: `LSTM`. This keeps the pipeline correct, understandable, and easy to debug before adding more expressive sequence models.

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

Implemented model:

- `LSTMSequenceModel`
- encoder: stacked LSTM with `batch_first=True`
- representation: final hidden state from the last LSTM layer
- head: dropout + linear projection to one scalar output

Default hyperparameters:

- hidden size: `64`
- layers: `2`
- dropout: `0.1`
- bidirectional: `false`

The model builder is dispatch-based, so a Transformer encoder can be added later without changing sequence construction, artifact format, or CLI usage.

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
  Best checkpoint selected by validation loss.
- `training_history.csv`
  Per-epoch train/validation loss and task-specific metrics.
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
  Reproducibility summary.

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

## Caveats

- The current post-cost labels are intentionally hard, so model quality should be judged with both predictive metrics and realized signal-return diagnostics.
- This first version uses only engineered tabular features arranged into sequences; it does not yet include raw order-book or multi-asset sequence inputs.
- Transformer support is not implemented yet.
