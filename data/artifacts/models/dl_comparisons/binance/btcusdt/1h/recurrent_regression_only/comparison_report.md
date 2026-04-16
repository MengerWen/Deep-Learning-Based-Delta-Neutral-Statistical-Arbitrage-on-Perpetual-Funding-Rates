# Deep-Learning Comparison Report

- Experiment: `recurrent_regression_only`
- Description: Compare only the recurrent families on the shared 24-hour post-cost regression target.
- Compared runs: `2`
- Validation ranking metric: `pearson_corr`
- Test ranking metric: `pearson_corr`
- Strategy ranking metric: `top_quantile_avg_return_bps` on `test`

## Runs

- `lstm` -> `lstm` using `configs/models/lstm.yaml` (reused_artifacts=True)
- `gru` -> `gru` using `configs/models/gru.yaml` (reused_artifacts=True)

## Main Finding

Current default best model under the configured test ranking metric (`pearson_corr`) is `lstm` with score `0.6385845204255011`.

## Validation Leaderboard

|   rank | run_label   | model_name   | model_group   | task       | target_column                    |   lookback_steps |   best_epoch | selected_loss   | checkpoint_selection_metric      | checkpoint_selection_effective_metric   |   selected_threshold | ranking_metric   |   ranking_metric_value |   validation_pearson_corr |   validation_rmse | validation_avg_signal_return_bps   | validation_cumulative_signal_return_bps   | validation_signal_hit_rate   |   validation_signal_count |   validation_top_quantile_avg_return_bps |
|-------:|:------------|:-------------|:--------------|:-----------|:---------------------------------|-----------------:|-------------:|:----------------|:---------------------------------|:----------------------------------------|---------------------:|:-----------------|-----------------------:|--------------------------:|------------------:|:-----------------------------------|:------------------------------------------|:-----------------------------|--------------------------:|-----------------------------------------:|
|      1 | lstm        | lstm         | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.669739 |                  0.669739 |           1.96638 |                                    |                                           |                              |                         0 |                                 -28.6512 |
|      2 | gru         | gru          | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.657014 |                  0.657014 |           2.00227 |                                    |                                           |                              |                         0 |                                 -28.5401 |

## Test Leaderboard

|   rank | run_label   | model_name   | model_group   | task       | target_column                    |   lookback_steps |   best_epoch | selected_loss   | checkpoint_selection_metric      | checkpoint_selection_effective_metric   |   selected_threshold | ranking_metric   |   ranking_metric_value |   test_pearson_corr |   test_rmse | test_avg_signal_return_bps   | test_cumulative_signal_return_bps   | test_signal_hit_rate   |   test_signal_count |   test_top_quantile_avg_return_bps |
|-------:|:------------|:-------------|:--------------|:-----------|:---------------------------------|-----------------:|-------------:|:----------------|:---------------------------------|:----------------------------------------|---------------------:|:-----------------|-----------------------:|--------------------:|------------:|:-----------------------------|:------------------------------------|:-----------------------|--------------------:|-----------------------------------:|
|      1 | lstm        | lstm         | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.638585 |            0.638585 |     1.23896 |                              |                                     |                        |                   0 |                           -31.6377 |
|      2 | gru         | gru          | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.570399 |            0.570399 |     1.36035 |                              |                                     |                        |                   0 |                           -31.7184 |

## Strategy-Oriented Leaderboard

|   rank | run_label   | model_name   | model_group   | task       | target_column                    |   lookback_steps |   best_epoch | selected_loss   | checkpoint_selection_metric      | checkpoint_selection_effective_metric   |   selected_threshold | ranking_metric              |   ranking_metric_value | test_avg_signal_return_bps   | test_cumulative_signal_return_bps   | test_signal_hit_rate   |   test_signal_count |   test_top_quantile_avg_return_bps |   test_top_quantile_cumulative_return_bps |
|-------:|:------------|:-------------|:--------------|:-----------|:---------------------------------|-----------------:|-------------:|:----------------|:---------------------------------|:----------------------------------------|---------------------:|:----------------------------|-----------------------:|:-----------------------------|:------------------------------------|:-----------------------|--------------------:|-----------------------------------:|------------------------------------------:|
|      1 | lstm        | lstm         | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | top_quantile_avg_return_bps |               -31.6377 |                              |                                     |                        |                   0 |                           -31.6377 |                                  -27936.1 |
|      2 | gru         | gru          | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | top_quantile_avg_return_bps |               -31.7184 |                              |                                     |                        |                   0 |                           -31.7184 |                                  -28007.4 |

## Notes

- This Phase 2 comparison layer reuses the stable Phase 1 per-model artifact contract rather than inventing a new tracking system.
- Runs are compared only after validating that provider, symbol, frequency, task, and target column match.
- Artifact reuse is allowed so repeated comparison refreshes stay lightweight when model outputs already exist.

## Figures

- `validation_metric_comparison.png`
- `test_metric_comparison.png`
- `strategy_metric_comparison.png`