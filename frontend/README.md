# Frontend Demo

This directory contains the presentation-friendly dashboard for the course-project prototype.

The frontend is intentionally lightweight:

- `Vite + TypeScript`
- no backend required
- reads one exported local snapshot plus copied chart assets

## What the dashboard shows

- project overview and architecture story
- key data-quality and backtest charts
- baseline and deep-learning model-zoo comparison cards
- strategy metrics table with test-primary, mark-to-market backtest fields
- vault status and mock operator update summary
- local deposit / withdraw / strategy update / NAV update simulation
- example activity log

## Recommended startup flow

1. Run the end-to-end demo workflow once:

```powershell
& 'd:\MG\anaconda3\python.exe' -m src.main run-demo --config configs/demo/workflow.yaml
```

2. If you only need to refresh the snapshot without rerunning the whole pipeline, export the local demo snapshot:

```powershell
& 'd:\MG\anaconda3\python.exe' scripts/demo/export_demo_snapshot.py --config configs/demo/default.yaml
```

3. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

4. Open the local Vite URL, usually:

```text
http://127.0.0.1:5173
```

## Re-export after new results

If you rerun upstream pipeline stages and want the dashboard to reflect new artifacts, rerun:

```powershell
& 'd:\MG\anaconda3\python.exe' scripts/demo/export_demo_snapshot.py --config configs/demo/default.yaml
```

## Caveats

- The demo console is local and simulated; it is not a wallet-connected production dApp.
- The operator/oracle flow is a prototype bridge from local artifacts to mock vault updates.
- Backtest cards use mark-to-market drawdown/Sharpe by default, while realized-only metrics remain in the exported artifacts for auditability.
- Broadcasted on-chain updates still depend on your local/testnet vault deployment and environment variables.
