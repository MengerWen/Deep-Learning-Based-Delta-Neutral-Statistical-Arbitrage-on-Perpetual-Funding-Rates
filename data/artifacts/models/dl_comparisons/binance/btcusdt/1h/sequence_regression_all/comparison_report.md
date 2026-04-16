# Deep-Learning Comparison Report

- Experiment: `sequence_regression_all`
- Description: Compare all Phase 1 sequence-model families on the shared 24-hour post-cost net-return regression target.
- Compared runs: `4`
- Validation ranking metric: `pearson_corr`
- Test ranking metric: `pearson_corr`
- Strategy ranking metric: `top_quantile_avg_return_bps` on `test`

## Runs

- `lstm` -> `lstm` using `configs/models/lstm.yaml` (reused_artifacts=True)
- `gru` -> `gru` using `configs/models/gru.yaml` (reused_artifacts=True)
- `tcn` -> `tcn` using `configs/models/tcn.yaml` (reused_artifacts=True)
- `transformer_encoder` -> `transformer_encoder` using `configs/models/transformer.yaml` (reused_artifacts=True)

## Main Finding

Current default best model under the configured test ranking metric (`pearson_corr`) is `transformer_encoder` with score `0.6460854810538473`.

## Validation Leaderboard

|   rank | run_label           | model_name          | model_group   | task       | target_column                    |   lookback_steps |   best_epoch | selected_loss   | checkpoint_selection_metric      | checkpoint_selection_effective_metric   |   selected_threshold | ranking_metric   |   ranking_metric_value |   validation_pearson_corr |   validation_rmse |   validation_avg_signal_return_bps |   validation_cumulative_signal_return_bps |   validation_signal_hit_rate |   validation_signal_count |   validation_top_quantile_avg_return_bps |
|-------:|:--------------------|:--------------------|:--------------|:-----------|:---------------------------------|-----------------:|-------------:|:----------------|:---------------------------------|:----------------------------------------|---------------------:|:-----------------|-----------------------:|--------------------------:|------------------:|-----------------------------------:|------------------------------------------:|-----------------------------:|--------------------------:|-----------------------------------------:|
|      1 | transformer_encoder | transformer_encoder | attention     | regression | target_future_net_return_bps_24h |               48 |            3 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.680773 |                  0.680773 |           1.94139 |                                nan |                                       nan |                          nan |                         0 |                                 -28.6457 |
|      2 | lstm                | lstm                | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.669739 |                  0.669739 |           1.96638 |                                nan |                                       nan |                          nan |                         0 |                                 -28.6512 |
|      3 | gru                 | gru                 | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.657014 |                  0.657014 |           2.00227 |                                nan |                                       nan |                          nan |                         0 |                                 -28.5401 |
|      4 | tcn                 | tcn                 | convolutional | regression | target_future_net_return_bps_24h |               48 |            4 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.495386 |                  0.495386 |           2.39443 |                                nan |                                       nan |                          nan |                         0 |                                 -29.2969 |

## Test Leaderboard

|   rank | run_label           | model_name          | model_group   | task       | target_column                    |   lookback_steps |   best_epoch | selected_loss   | checkpoint_selection_metric      | checkpoint_selection_effective_metric   |   selected_threshold | ranking_metric   |   ranking_metric_value |   test_pearson_corr |   test_rmse |   test_avg_signal_return_bps |   test_cumulative_signal_return_bps |   test_signal_hit_rate |   test_signal_count |   test_top_quantile_avg_return_bps |
|-------:|:--------------------|:--------------------|:--------------|:-----------|:---------------------------------|-----------------:|-------------:|:----------------|:---------------------------------|:----------------------------------------|---------------------:|:-----------------|-----------------------:|--------------------:|------------:|-----------------------------:|------------------------------------:|-----------------------:|--------------------:|-----------------------------------:|
|      1 | transformer_encoder | transformer_encoder | attention     | regression | target_future_net_return_bps_24h |               48 |            3 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.646085 |            0.646085 |     1.20869 |                          nan |                                 nan |                    nan |                   0 |                           -31.5936 |
|      2 | lstm                | lstm                | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.638585 |            0.638585 |     1.23896 |                          nan |                                 nan |                    nan |                   0 |                           -31.6377 |
|      3 | gru                 | gru                 | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.570399 |            0.570399 |     1.36035 |                          nan |                                 nan |                    nan |                   0 |                           -31.7184 |
|      4 | tcn                 | tcn                 | convolutional | regression | target_future_net_return_bps_24h |               48 |            4 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | pearson_corr     |               0.474455 |            0.474455 |     1.77152 |                          nan |                                 nan |                    nan |                   0 |                           -32.1444 |

## Strategy-Oriented Leaderboard

|   rank | run_label           | model_name          | model_group   | task       | target_column                    |   lookback_steps |   best_epoch | selected_loss   | checkpoint_selection_metric      | checkpoint_selection_effective_metric   |   selected_threshold | ranking_metric              |   ranking_metric_value |   test_avg_signal_return_bps |   test_cumulative_signal_return_bps |   test_signal_hit_rate |   test_signal_count |   test_top_quantile_avg_return_bps |   test_top_quantile_cumulative_return_bps |
|-------:|:--------------------|:--------------------|:--------------|:-----------|:---------------------------------|-----------------:|-------------:|:----------------|:---------------------------------|:----------------------------------------|---------------------:|:----------------------------|-----------------------:|-----------------------------:|------------------------------------:|-----------------------:|--------------------:|-----------------------------------:|------------------------------------------:|
|      1 | transformer_encoder | transformer_encoder | attention     | regression | target_future_net_return_bps_24h |               48 |            3 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | top_quantile_avg_return_bps |               -31.5936 |                          nan |                                 nan |                    nan |                   0 |                           -31.5936 |                                  -27897.2 |
|      2 | lstm                | lstm                | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | top_quantile_avg_return_bps |               -31.6377 |                          nan |                                 nan |                    nan |                   0 |                           -31.6377 |                                  -27936.1 |
|      3 | gru                 | gru                 | recurrent     | regression | target_future_net_return_bps_24h |               48 |            5 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | top_quantile_avg_return_bps |               -31.7184 |                          nan |                                 nan |                    nan |                   0 |                           -31.7184 |                                  -28007.4 |
|      4 | tcn                 | tcn                 | convolutional | regression | target_future_net_return_bps_24h |               48 |            4 | huber           | validation_avg_signal_return_bps | validation_loss                         |                    0 | top_quantile_avg_return_bps |               -32.1444 |                          nan |                                 nan |                    nan |                   0 |                           -32.1444 |                                  -28383.5 |

## Notes

- This Phase 2 comparison layer reuses the stable Phase 1 per-model artifact contract rather than inventing a new tracking system.
- Runs are compared only after validating that provider, symbol, frequency, task, and target column match.
- Artifact reuse is allowed so repeated comparison refreshes stay lightweight when model outputs already exist.

## Figures

- `validation_metric_comparison.png`
- `test_metric_comparison.png`
- `strategy_metric_comparison.png`