# End-to-End Demo Workflow

- Run name: `full_demo_default`
- Status: `completed_with_warnings`
- Failed stage: `none`

## Stage Results

| Stage | Status | Optional | Return Code | Duration | Command |
| --- | --- | --- | --- | --- | --- |
| Fetch and normalize market data | reused_existing_artifacts | no | 1 | 29.3s | `D:\MG\anaconda3\python.exe -m src.main fetch-data --config configs/data/default.yaml --log-level INFO` |
| Generate data-quality report | completed | no | 0 | 12.6s | `D:\MG\anaconda3\python.exe -m src.main report-data-quality --config configs/reports/data_quality.yaml --log-level INFO` |
| Build feature table | completed | no | 0 | 11.7s | `D:\MG\anaconda3\python.exe -m src.main build-features --config configs/features/default.yaml --log-level INFO` |
| Build supervised dataset | completed | no | 0 | 14.0s | `D:\MG\anaconda3\python.exe -m src.main build-labels --config configs/labels/default.yaml --log-level INFO` |
| Train baseline models | completed | no | 0 | 312.9s | `D:\MG\anaconda3\python.exe -m src.main train-baseline --config configs/models/baseline.yaml --log-level INFO` |
| Train deep-learning model | reused_existing_artifacts | yes | 3221226505 | 28.0s | `D:\MG\anaconda3\python.exe -m src.main train-dl --config configs/models/lstm.yaml --log-level INFO` |
| Compare deep-learning model zoo | completed | yes | 0 | 7.0s | `D:\MG\anaconda3\python.exe -m src.main compare-dl --config configs/experiments/dl/regression_all.yaml --log-level INFO` |
| Generate baseline signals | completed | no | 0 | 55.2s | `D:\MG\anaconda3\python.exe -m src.main generate-signals --config configs/signals/default.yaml --log-level INFO --source baseline` |
| Generate deep-learning signals | completed | yes | 0 | 11.6s | `D:\MG\anaconda3\python.exe -m src.main generate-signals --config configs/signals/default.yaml --log-level INFO --source dl` |
| Run backtest | completed | no | 0 | 29.5s | `D:\MG\anaconda3\python.exe -m src.main backtest --config configs/backtests/default.yaml --log-level INFO` |
| Prepare or submit vault update | completed | no | 0 | 7.8s | `D:\MG\anaconda3\python.exe -m src.main sync-vault --config configs/integration/default.yaml --log-level INFO` |
| Export frontend demo snapshot | completed | no | 0 | 1.1s | `D:\MG\anaconda3\python.exe "D:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\scripts\demo\export_demo_snapshot.py" --config configs/demo/default.yaml --log-level INFO` |

## Demo Artifacts

- Artifact snapshot: `D:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\data\artifacts\demo\demo_snapshot.json`
- Frontend snapshot: `D:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\frontend\public\demo\demo_snapshot.json`

## Next Steps

1. If the frontend snapshot exists, start the dashboard:
   `cd frontend`
   `npm run dev`
2. If you want a live local-chain update instead of dry-run sync, deploy the vault, set `VAULT_ADDRESS` and `PRIVATE_KEY`, enable broadcast in `configs/integration/default.yaml`, then rerun the sync stage.