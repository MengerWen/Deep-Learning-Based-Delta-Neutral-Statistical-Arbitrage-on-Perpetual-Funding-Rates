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

This is the initial monorepo scaffold. The folder structure, configs, docs, starter Python package, Solidity workspace, and demo frontend skeleton are in place. Most domain-specific logic is still a placeholder and should be implemented incrementally.

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
+-- scripts/
|   +-- backtests/
|   +-- data/
|   +-- demo/
|   +-- features/
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
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[dev]
python -m pytest
```

Example scaffold commands:

```bash
python scripts/data/fetch_market_data.py --config configs/data/default.toml
python scripts/features/build_features.py --config configs/features/default.toml
python scripts/models/train_baseline.py --config configs/models/baseline.toml
python scripts/backtests/run_backtest.py --config configs/backtests/default.toml
```

### Solidity

```bash
cd contracts
forge build
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Docs

- Architecture: [docs/architecture/overview.md](docs/architecture/overview.md)
- Data pipeline: [docs/modules/data-pipeline.md](docs/modules/data-pipeline.md)
- Models and research: [docs/modules/models-and-research.md](docs/modules/models-and-research.md)
- Backtesting: [docs/modules/backtesting.md](docs/modules/backtesting.md)
- Vault contract: [docs/contracts/vault.md](docs/contracts/vault.md)
- Frontend demo: [docs/demos/frontend.md](docs/demos/frontend.md)
- Implementation plan: [docs/plans/2026-04-09-course-project-implementation-plan.md](docs/plans/2026-04-09-course-project-implementation-plan.md)

## Immediate Next Steps

1. Implement the real data-ingestion adapters for one exchange and one reference price source.
2. Build the cleaned canonical dataset schema and feature pipeline.
3. Add the first baseline strategy and a cost-aware backtest.
4. Expand the vault contract tests and connect demo artifacts into the frontend.

## Minimal No-Install Verification

If you have Python 3.11+ but have not installed project dependencies yet, the starter tests can still be run with the standard library:

```bash
python -m unittest discover -s tests/unit -p "test_*.py"
```

