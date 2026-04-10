# Mock Off-Chain to On-Chain Integration

This document explains the prototype bridge between the Python research stack and the Solidity vault.

The goal is not to build a production oracle network.
The goal is to show, clearly and locally, how an off-chain strategy system could produce a simplified vault update that is then submitted by a trusted operator account.

## What This Module Does

The integration layer:

- reads generated strategy artifacts from the Python side
- selects one strategy snapshot to represent the current off-chain state
- converts that snapshot into a mock vault update payload
- optionally calls the vault contract with `updateStrategyState` and `updateNav` or `updatePnl`
- writes JSON and markdown artifacts so the flow is easy to inspect in demos and slides

The default mode is `dry-run`.

In dry-run mode, the module does not broadcast any transaction.
It only generates the exact payload and calldata that would be sent on-chain.

## What This Module Does Not Do

This module does not:

- provide a decentralized oracle network
- verify strategy results trustlessly
- implement message relaying, signatures, committees, or consensus
- run as a persistent backend service
- claim production security

This is a course-project operator/oracle-style demo flow.

## Current Inputs

The default config uses:

- standardized signals:
  - `data/artifacts/signals/binance/btcusdt/1h/baseline/signals.parquet`
- backtest leaderboard:
  - `data/artifacts/backtests/binance/btcusdt/1h/baseline_signals_default/leaderboard.parquet`

By default the module:

1. ranks strategies using `total_net_pnl_usd`
2. selects the top-ranked strategy unless `strategy_name` is specified
3. chooses the latest signal row from the preferred split order
4. converts the signal state into a vault `StrategyState`
5. converts leaderboard PnL into mock stablecoin asset units
6. computes hashes for signal, metadata, and report payloads

## Interface Assumptions

### Off-chain assumptions

- the signal layer already writes normalized `signals.parquet`
- the backtest layer already writes a summary leaderboard
- `total_net_pnl_usd` is treated as the simplest demo proxy for off-chain strategy performance

### On-chain assumptions

- the vault is already deployed
- the caller is the vault `owner` or `operator`
- the vault uses the prototype interface defined in [contracts.md](d:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\docs\contracts.md)
- the mock stablecoin is treated as approximately `1 token = 1 USD`

### Economic assumptions

- `base_nav_assets` is a demo starting NAV configured in YAML
- `reported_nav_assets = base_nav_assets + summary_pnl_assets`
- this is a simplified accounting mirror, not a complete live accounting engine

## Files

The main implementation is:

- [pipeline.py](d:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\src\funding_arb\integration\pipeline.py)
- [default.yaml](d:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\configs\integration\default.yaml)
- [sync_vault.py](d:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\scripts\integration\sync_vault.py)

## CLI Usage

Unified CLI:

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main sync-vault --config configs/integration/default.yaml
```

Wrapper script:

```powershell
& 'd:\MG\anaconda3\python.exe' scripts/integration/sync_vault.py --config configs/integration/default.yaml
```

## Demo Walkthrough

### 1. Generate the upstream artifacts

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main generate-signals --source baseline --config configs/signals/default.yaml
& 'd:\MG\anaconda3\python.exe' -m src.main backtest --config configs/backtests/default.yaml
```

### 2. Deploy the vault locally

```powershell
cd contracts
forge script script/DeployLocal.s.sol:DeployLocal --rpc-url http://127.0.0.1:8545 --broadcast
```

Update your environment so `VAULT_ADDRESS` points to the deployed vault and `PRIVATE_KEY` points to the owner/operator key.

### 3. Run the integration in dry-run mode first

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main sync-vault --config configs/integration/default.yaml
```

This writes:

- `selected_strategy_summary.json`
- `vault_update_plan.json`
- `contract_call_summary.json`
- `integration_report.md`

under:

- `data/artifacts/integration/binance/btcusdt/1h/mock_operator_default/`

### 4. Switch to broadcast mode

Edit [default.yaml](d:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\configs\integration\default.yaml):

- set `contract.broadcast: true`
- keep only one of:
  - `update_nav: true`
  - `update_pnl: true`

Then rerun:

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main sync-vault --config configs/integration/default.yaml
```

### 5. Inspect the result

The integration artifact directory will now include the planned payload plus the execution summary.

In a local demo, this gives you a simple narrative:

1. research and backtesting produced a current strategy view
2. the operator module converted that view into a compact on-chain update
3. the vault recorded the state change on-chain

## Educational Value

This module is intentionally simple because it helps explain the hybrid architecture clearly:

- ML and backtesting stay off-chain
- vault accounting stays on-chain
- a trusted operator bridges the two

That is exactly the point this course project is trying to demonstrate.
