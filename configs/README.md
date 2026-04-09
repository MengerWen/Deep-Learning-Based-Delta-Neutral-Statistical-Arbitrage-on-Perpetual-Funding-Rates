# Config Conventions

This repository keeps configuration centralized under `configs/` using YAML files.

- `configs/data/`: source selection, symbols, date range, sampling frequency
- `configs/features/`: rolling windows, normalization, z-score settings, label horizons
- `configs/models/`: baseline model configs and deep-learning experiment parameters
- `configs/backtests/`: fees, slippage, execution assumptions, portfolio rules
- `configs/demo/`: frontend/demo artifact settings
- `configs/reports/`: exploratory reporting, figure generation, and markdown data-quality summaries

Use the existing Python environment at `d:\MG\anaconda3\python.exe`, which already includes `PyYAML`, when running scripts that load these configs. Assumptions that materially affect outputs should live in config before they are hardcoded into scripts or notebooks.