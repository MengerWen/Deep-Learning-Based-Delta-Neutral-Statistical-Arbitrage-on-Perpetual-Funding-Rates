# Backtesting Module

## Purpose

Evaluate whether a funding-rate arbitrage signal survives realistic frictions and position-management rules.

## Planned Features

- delta-neutral position accounting
- fee and slippage modeling
- funding accrual handling
- entry and exit rules
- PnL attribution
- performance metrics

## Minimum Metrics

- cumulative return
- annualized return
- Sharpe ratio
- maximum drawdown
- win rate
- turnover and trading cost impact

## Future Files

- `src/funding_arb/backtest/engine.py`
- `src/funding_arb/evaluation/metrics.py`
- `scripts/backtests/run_backtest.py`

## Caveats

The initial scaffold provides starter metric functions and CLI structure, but not a complete strategy simulator yet.

