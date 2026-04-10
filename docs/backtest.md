# Backtesting Engine

## Purpose

This module implements the first explicit backtesting engine for the project.

It is designed for one narrow research problem:

> Given standardized hourly trading signals for a perpetual-funding arbitrage strategy, does a simple delta-neutral execution rule produce usable post-cost performance after fees, slippage, and holding-period constraints?

This is intentionally **not** a generic multi-asset portfolio framework.

## Scope

The first version supports:

- one asset at a time
- one open position at a time per strategy
- standardized signals from the signal layer
- fixed-notional delta-neutral positions
- explicit trade logs and performance summaries
- presentation-friendly plots and markdown output

It compares strategies independently. If one signal artifact contains multiple strategies, each strategy is backtested as its own standalone equity curve.

## Inputs

Main inputs:

- standardized signal artifact
  - default: `data/artifacts/signals/binance/btcusdt/1h/baseline/signals.parquet`
- canonical hourly market dataset
  - default: `data/processed/binance/btcusdt/1h/hourly_market_data.parquet`

Required signal fields:

- `timestamp`
- `strategy_name`
- `source`
- `source_subtype`
- `signal_score`
- `predicted_class`
- `expected_return_bps`
- `suggested_direction`
- `confidence`
- `should_trade`
- `split`

Required market fields:

- `timestamp`
- `perp_open`, `perp_close`
- `spot_open`, `spot_close`
- `funding_rate`

## Position Model

The default direction is:

- `short_perp_long_spot`

The backtester uses a fixed notional per leg:

- `position_notional_usd`

For a `10,000 USD` notional:

- short perpetual leg notionally sells `10,000 USD` of perp
- hedge leg notionally buys `10,000 USD` of spot

This makes trade-level PnL easy to interpret in both USD and bps of per-leg notional.

## Entry Logic

Default entry logic:

1. observe signal at timestamp `t`
2. require `should_trade = 1`
3. require `suggested_direction` to match config direction
4. optionally require minimum `signal_score`
5. optionally require minimum `confidence`
6. optionally require minimum `expected_return_bps`
7. enter after `entry_delay_bars`

With the default config:

- signals are evaluated on hourly data
- execution uses next-bar `open`
- so signal at `t` enters at `t + 1` open

This matches the same no-leakage convention used in the label pipeline.

## Exit Logic

The first version supports four exit types:

- `signal_off`
  - exit when the signal no longer satisfies entry conditions
- `holding_window`
  - soft time-based exit
- `maximum_holding`
  - hard time cap
- optional stop conditions
  - `stop_loss_bps`
  - `take_profit_bps`

Current stop logic is evaluated on hourly bar information and exits on the next execution bar. It is therefore conservative and explicit, but not intrabar-precise.

## PnL Logic

Trade PnL has three economic components:

1. perpetual leg PnL
2. hedge leg PnL
3. funding PnL

For `short_perp_long_spot`:

```text
gross_pnl
= short-perp leg pnl
+ long-spot leg pnl
+ funding pnl
```

Net PnL then subtracts:

- taker fees on all four round-trip transactions
- gas cost per trade
- optional flat friction term

Slippage is modeled by adverse execution prices rather than by a second explicit deduction.

## Performance Outputs

The backtester writes:

- `trade_log.parquet` / `trade_log.csv`
- `equity_curve.parquet` / `equity_curve.csv`
- `strategy_metrics.parquet` / `strategy_metrics.csv`
- `split_summary.parquet` / `split_summary.csv`
- `leaderboard.parquet` / `leaderboard.csv`
- `backtest_report.md`
- `backtest_manifest.json`
- figures under `figures/`

Key reported metrics:

- cumulative return
- annualized return
- Sharpe ratio
- max drawdown
- win rate
- average trade return
- trade count
- turnover
- total fees / gas / funding contribution

## Plots

The first version exports:

- cumulative return by strategy
- realized drawdown by strategy
- trade-return distribution boxplot

These are intended to be reusable in the final report or course presentation.

## Important Simplifying Assumptions

These assumptions are deliberate and should be stated clearly in any presentation:

- single-asset prototype only
- one open position at a time per strategy
- no partial exits
- no full intratrade mark-to-market equity curve yet
- no borrow-cost model for `long_perp_short_spot`
- no order book or latency simulation
- no liquidation or margin model
- no exchange-specific funding edge cases beyond the cleaned historical dataset

The current equity curve is **realized-PnL based**. This makes the first version easier to audit, but it understates intratrade drawdown relative to a true mark-to-market engine.

## Main Files

- backtest engine:
  - `src/funding_arb/backtest/engine.py`
- CLI wrapper:
  - `scripts/backtests/run_backtest.py`
- config:
  - `configs/backtests/default.yaml`

## Command

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main backtest --config configs/backtests/default.yaml
```

## Recommended Next Step

After this first version, the most valuable improvement is:

- mark-to-market equity and drawdown during open positions

That would make the engine more realistic without changing the signal, trade-log, or reporting interfaces.
