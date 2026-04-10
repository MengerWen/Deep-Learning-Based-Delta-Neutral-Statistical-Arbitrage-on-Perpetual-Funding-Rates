# Frontend Demo

## Goal

Provide a lightweight dashboard for presenting the project during demos and the final course presentation.

## Implemented Views

- project summary and architecture snapshot
- key research and backtest charts
- strategy metrics and model comparison cards
- vault status and operator-sync summary
- activity log
- local mock interaction panel for:
  - deposit
  - withdraw
  - strategy activation
  - NAV/PnL update
  - share/accounting status reset

## Stack Choice

The frontend uses `Vite + vanilla TypeScript` to keep setup and maintenance light.

## Data Flow

1. Python pipelines generate research, model, backtest, and integration artifacts.
2. `scripts/demo/export_demo_snapshot.py` packages those results into:
   - `data/artifacts/demo/demo_snapshot.json`
   - `frontend/public/demo/demo_snapshot.json`
   - `frontend/public/demo/assets/*`
3. The dashboard fetches `/demo/demo_snapshot.json` locally and renders the full story without a backend.

## Startup

```powershell
& 'd:\MG\anaconda3\python.exe' scripts/demo/export_demo_snapshot.py --config configs/demo/default.yaml
cd frontend
npm install
npm run dev
```

## Caveats

- The dashboard is optimized for demo clarity, not wallet-grade production UX.
- The local vault console is an educational simulator and intentionally mirrors mock accounting assumptions.
- The frontend does not execute trades or act as a live oracle network.
