# Deep Learning-Based Delta-Neutral Statistical Arbitrage on Perpetual Funding Rates

This repository is a course-project prototype for a hybrid DeFi + quantitative research system. The goal is to build a clean end-to-end demonstration of:

- market-data ingestion and cleaning for perpetual futures, spot/index, and funding-rate data
- feature engineering and label generation for arbitrage signals
- baseline statistical models and deep learning models
- backtesting with fees, slippage, and evaluation metrics
- a Solidity vault prototype for deposits, withdrawals, shares, NAV/PnL updates, access control, and event logging
- a lightweight demo frontend for presenting research results and vault state

The repository is intentionally scoped as a prototype. We want clear architecture, reproducible experiments, and a believable demo, without over-building production infrastructure.

## Repository Status

The repository now has a working Binance historical data pipeline, a configurable feature-engineering pipeline, a cost-aware label-generation pipeline, a presentation-friendly data-quality reporting command, a baseline strategy/model benchmarking pipeline, a first LSTM-based deep-learning training pipeline, a unified signal layer, a first explicit delta-neutral backtesting engine, and a reusable robustness-analysis workflow. Richer contract/frontend integration and deeper model iteration are the main remaining build areas.

## Architecture Overview

The project is organized into three main layers:

1. `src/funding_arb/`
   Core Python package for ingestion, cleaning, features, labels, models, backtesting, and evaluation.
2. `contracts/`
   Foundry-based Solidity workspace for the vault prototype and supporting mocks.
3. `frontend/`
   Lightweight Vite + TypeScript dashboard scaffold for displaying backtest outputs and mock vault information.

The expected data flow is:

`market data -> cleaned dataset -> engineered features -> labels/signals -> model outputs -> backtest results -> demo artifacts -> frontend/contract presentation`

## Why These Stack Choices

### Python for the research pipeline

Python is the most practical fit for:

- data ingestion and cleaning
- quant research
- feature engineering
- baseline ML
- deep learning experiments
- backtesting and evaluation

### Foundry for Solidity

This repo uses `Foundry` instead of `Hardhat` because it keeps the contract workspace small and Solidity-first. For a course-project prototype with one main vault contract and a few supporting scripts/tests, Foundry is a better fit than a larger JS-centered toolchain.

### Vite + vanilla TypeScript for the demo

The demo frontend uses a lightweight `Vite + TypeScript` scaffold rather than a full SPA framework. This keeps the dashboard simple, fast to iterate on, and easy for the team to understand.

## Repository Structure

```text
.
+-- AGENTS.md
+-- Proposal.md
+-- README.md
+-- pyproject.toml
+-- .env.example
+-- configs/
|   +-- backtests/
|   +-- data/
|   +-- demo/
|   +-- features/
|   +-- labels/
|   +-- reports/
|   +-- signals/
|   `-- models/
+-- data/
|   +-- raw/
|   +-- interim/
|   +-- processed/
|   `-- artifacts/
+-- docs/
|   +-- architecture/
|   +-- contracts/
|   +-- demos/
|   +-- modules/
|   `-- plans/
+-- notebooks/
+-- reports/
+-- scripts/
|   +-- backtests/
|   +-- data/
|   +-- demo/
|   +-- features/
|   +-- labels/
|   +-- reports/
|   +-- signals/
|   `-- models/
+-- src/
|   `-- funding_arb/
+-- tests/
|   +-- fixtures/
|   +-- integration/
|   `-- unit/
+-- contracts/
`-- frontend/
```

## Quickstart

### Python

```bash
& 'd:\MG\anaconda3\python.exe' -m pip install -e .[dev]
& 'd:\MG\anaconda3\python.exe' -m pytest
```

Example scaffold commands:

```bash
& 'd:\MG\anaconda3\python.exe' scripts/data/fetch_market_data.py --config configs/data/default.yaml
& 'd:\MG\anaconda3\python.exe' scripts/features/build_features.py --config configs/features/default.yaml
& 'd:\MG\anaconda3\python.exe' scripts/labels/build_labels.py --config configs/labels/default.yaml
& 'd:\MG\anaconda3\python.exe' scripts/models/train_baseline.py --config configs/models/baseline.yaml
& 'd:\MG\anaconda3\python.exe' scripts/models/evaluate_baseline.py --config configs/models/baseline.yaml
& 'd:\MG\anaconda3\python.exe' scripts/models/train_dl.py --config configs/models/lstm.yaml
& 'd:\MG\anaconda3\python.exe' scripts/backtests/run_backtest.py --config configs/backtests/default.yaml
& 'd:\MG\anaconda3\python.exe' scripts/reports/report_data_quality.py --config configs/reports/data_quality.yaml
& 'd:\MG\anaconda3\python.exe' scripts/reports/robustness_report.py --config configs/reports/robustness.yaml
& 'd:\MG\anaconda3\python.exe' scripts/demo/export_demo_snapshot.py --config configs/demo/default.yaml
```
Unified CLI commands:

```bash
& 'd:\MG\anaconda3\python.exe' -m src.main fetch-data
& 'd:\MG\anaconda3\python.exe' -m src.main report-data-quality
& 'd:\MG\anaconda3\python.exe' -m src.main build-features
& 'd:\MG\anaconda3\python.exe' -m src.main build-labels
& 'd:\MG\anaconda3\python.exe' -m src.main train-baseline
& 'd:\MG\anaconda3\python.exe' -m src.main evaluate-baseline
& 'd:\MG\anaconda3\python.exe' -m src.main train-dl
& 'd:\MG\anaconda3\python.exe' -m src.main generate-signals --source baseline
& 'd:\MG\anaconda3\python.exe' -m src.main generate-signals --source dl
& 'd:\MG\anaconda3\python.exe' -m src.main backtest
& 'd:\MG\anaconda3\python.exe' -m src.main robustness-report
& 'd:\MG\anaconda3\python.exe' -m src.main sync-vault
```

Override config or logging when needed:

```bash
& 'd:\MG\anaconda3\python.exe' -m src.main fetch-data --config configs/data/default.yaml --log-level DEBUG
```

Legacy `scripts/` entrypoints remain available as thin wrappers around the same command layer.
The `fetch-data` command now runs the first complete historical data pipeline and writes raw, cleaned, and canonical hourly outputs under `data/raw/`, `data/interim/`, and `data/processed/`.
The `report-data-quality` command consumes that canonical dataset and writes presentation-ready tables, figures, and a markdown summary under `reports/data_quality/`.
The `build-features` command now writes an interpretable feature table and manifest under `data/processed/features/`.
The `build-labels` command now writes post-cost regression targets, classification targets, and split-ready supervised datasets under `data/processed/supervised/`.
The `train-baseline` command now fits rule-based and simple ML baselines, writes reusable prediction/signal artifacts under `data/artifacts/models/baselines/`, and saves evaluation summaries for validation/test benchmarking.
The `evaluate-baseline` command reloads saved baseline artifacts and regenerates prediction/evaluation outputs without refitting.
The `train-dl` command now trains the first LSTM sequence model on the supervised dataset, saves the best checkpoint, writes prediction artifacts, and exports a lightweight experiment summary under `data/artifacts/models/dl/`.
The `generate-signals` command now normalizes rule-based, baseline ML, and deep-learning outputs into one shared signal schema under `data/artifacts/signals/`, ready for backtesting and demo consumption.
The `backtest` command now consumes standardized signals plus the canonical market dataset, writes trade logs, realized equity curves, summary metrics, report figures, and a markdown backtest report under `data/artifacts/backtests/`.
The `robustness-report` command now reuses the signal and backtest layers to stress-test results under alternative cost assumptions, holding windows, rule thresholds, and feature ablations, then writes presentation-ready tables and figures under `reports/robustness/`.
The `sync-vault` command now demonstrates a mock operator/oracle-style bridge from off-chain strategy artifacts to the on-chain vault by generating a vault update payload and, when enabled, broadcasting `updateStrategyState` plus `updateNav` or `updatePnl`.

### Solidity

```bash
cd contracts
forge build
forge test -vv
```

Local deployment example:

```bash
cd contracts
forge script script/DeployLocal.s.sol:DeployLocal --rpc-url http://127.0.0.1:8545 --broadcast
```

### Frontend

```bash
& 'd:\MG\anaconda3\python.exe' scripts/demo/export_demo_snapshot.py --config configs/demo/default.yaml
cd frontend
npm install
npm run dev
```

The frontend reads `frontend/public/demo/demo_snapshot.json`, which is generated from the latest local research, backtest, and vault-integration artifacts by `scripts/demo/export_demo_snapshot.py`.

## Docs

- Technical design: [docs/architecture.md](docs/architecture.md)
- Architecture: [docs/architecture/overview.md](docs/architecture/overview.md)
- Data pipeline: [docs/modules/data-pipeline.md](docs/modules/data-pipeline.md)
- Data schema: [docs/data_schema.md](docs/data_schema.md)
- Data-quality reporting: [docs/modules/data-quality-reporting.md](docs/modules/data-quality-reporting.md)
- Feature specification: [docs/features.md](docs/features.md)
- Label specification: [docs/labels.md](docs/labels.md)
- Baseline models: [docs/baselines.md](docs/baselines.md)
- Deep learning models: [docs/models.md](docs/models.md)
- Unified signals: [docs/signals.md](docs/signals.md)
- Backtest engine: [docs/backtest.md](docs/backtest.md)
- Robustness workflow: [docs/robustness.md](docs/robustness.md)
- Solidity vault specification: [docs/contracts.md](docs/contracts.md)
- Mock off-chain to on-chain integration: [docs/integration.md](docs/integration.md)
- Models and research: [docs/modules/models-and-research.md](docs/modules/models-and-research.md)
- Backtesting: [docs/modules/backtesting.md](docs/modules/backtesting.md)
- Vault module note: [docs/contracts/vault.md](docs/contracts/vault.md)
- Frontend demo: [docs/demos/frontend.md](docs/demos/frontend.md)
- Implementation plan: [docs/plans/2026-04-09-course-project-implementation-plan.md](docs/plans/2026-04-09-course-project-implementation-plan.md)
## Immediate Next Steps

1. Add mark-to-market intratrade equity and drawdown to the backtesting engine.
2. Expand the data layer with index-price ingestion and optional open-interest validation.
3. Connect robustness and backtest report artifacts into the frontend demo.
4. Add a second sequence architecture, such as a Transformer encoder, only after the LSTM benchmark is stable.

## Minimal No-Install Verification

All Python commands for this repository should use the designated Anaconda interpreter: `d:\MG\anaconda3\python.exe`.

```bash
& 'd:\MG\anaconda3\python.exe' -m pytest tests/unit -q
```

