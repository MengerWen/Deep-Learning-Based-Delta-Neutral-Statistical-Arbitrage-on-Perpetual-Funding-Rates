# Config Conventions

This repository keeps configuration centralized under `configs/`.

- `configs/data/`: source selection, symbols, date range, sampling frequency
- `configs/features/`: rolling windows, normalization, z-score settings, label horizons
- `configs/models/`: baseline model configs and deep-learning experiment parameters
- `configs/backtests/`: fees, slippage, execution assumptions, portfolio rules
- `configs/demo/`: frontend/demo artifact settings

The initial scaffold uses JSON-compatible config files with `.yaml` filenames so the repo can be smoke-tested without extra parser dependencies. Assumptions that materially affect outputs should live in config before they are hardcoded into scripts or notebooks.
