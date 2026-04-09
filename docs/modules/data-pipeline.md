# Data Pipeline Module

## Purpose

Create a reproducible dataset for one funding-rate arbitrage research workflow, starting with a single symbol and single venue.

## Planned Responsibilities

- fetch perpetual funding-rate history
- fetch perpetual price history
- fetch spot or index/reference price history
- align timestamps and sampling intervals
- standardize schema and units
- preserve raw files before transformation
- write cleaned outputs for downstream feature and label generation

## Initial Assumptions

- start with `BTCUSDT`
- begin with one exchange and one reference source
- use hourly frequency for the first end-to-end prototype
- use `2021-01-01` to `2026-04-07` UTC as the default main historical window for the first full Binance `BTCUSDT` dataset

## Future Files

- `src/funding_arb/data/clients.py`
- `src/funding_arb/data/pipeline.py`
- `src/funding_arb/data/schemas.py`
- `scripts/data/fetch_market_data.py`

## Caveats

The current scaffold contains only starter utilities and CLI placeholders. Real exchange adapters and schema normalization still need to be implemented.

