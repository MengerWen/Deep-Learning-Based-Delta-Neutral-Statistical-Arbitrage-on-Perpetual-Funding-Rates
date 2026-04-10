# Backtesting Module

## Status

The first complete backtesting module is now implemented.

Primary implementation:

- `src/funding_arb/backtest/engine.py`

Primary documentation:

- `docs/backtest.md`

## What It Does

- consumes standardized signals from the signal layer
- simulates one delta-neutral position at a time per strategy
- applies explicit fee, slippage, gas, and funding logic
- writes trade logs, equity curves, metrics, plots, and a markdown report

## Current Design Choice

This first version uses a **realized-PnL equity curve** instead of full intratrade mark-to-market.

That is an intentional simplification:

- easier to audit
- easier to explain in a course project
- enough for first-pass comparison of baseline and deep-learning signals

## Outputs

Default output root:

- `data/artifacts/backtests/<provider>/<symbol>/<frequency>/<run_name>/`

## Command

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main backtest --config configs/backtests/default.yaml
```
