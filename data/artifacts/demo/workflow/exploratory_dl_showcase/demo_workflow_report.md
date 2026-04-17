# End-to-End Demo Workflow

- Run name: `exploratory_dl_showcase`
- Status: `completed_with_warnings`
- Failed stage: `none`

## Stage Results

| Stage | Status | Optional | Return Code | Duration | Command |
| --- | --- | --- | --- | --- | --- |
| Build exploratory DL dataset | completed | no | 0 | 10.1s | `D:\MG\anaconda3\python.exe -m src.main build-exploratory-dl-dataset --config configs/models/exploratory_dl/dataset.yaml --log-level INFO` |
| Compare exploratory deep-learning showcase bundle | completed | no | 0 | 6.7s | `D:\MG\anaconda3\python.exe -m src.main compare-dl --config configs/experiments/dl/exploratory_gross_regression.yaml --log-level INFO` |
| Compare exploratory direction-classification bundle | completed | no | 0 | 6.7s | `D:\MG\anaconda3\python.exe -m src.main compare-dl --config configs/experiments/dl/exploratory_direction_classification.yaml --log-level INFO` |
| Generate exploratory deep-learning signals | completed | no | 0 | 46.4s | `D:\MG\anaconda3\python.exe -m src.main generate-exploratory-dl-signals --config configs/signals/exploratory_dl/default.yaml --log-level INFO` |
| Run exploratory deep-learning backtest | reused_existing_artifacts | no | 120 | 635.5s | `D:\MG\anaconda3\python.exe -m src.main backtest --config configs/backtests/exploratory_dl/default.yaml --log-level INFO` |
| Generate exploratory deep-learning report | reused_existing_artifacts | no | 120 | 10.9s | `D:\MG\anaconda3\python.exe -m src.main generate-exploratory-dl-report --config configs/reports/exploratory_dl/showcase.yaml --log-level INFO` |
| Export frontend demo snapshot | reused_existing_artifacts | yes | 120 | 1.0s | `D:\MG\anaconda3\python.exe "D:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\scripts\demo\export_demo_snapshot.py" --config configs/demo/exploratory_snapshot.yaml --log-level INFO` |

## Demo Artifacts

- Artifact snapshot: `D:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\data\artifacts\demo\exploratory\demo_snapshot.json`
- Frontend snapshot: `D:\MG\! CUHKSZ\~！大三 下\FTE 4312\Github\frontend\public\demo\exploratory\demo_snapshot.json`

## Next Steps

1. If the frontend snapshot exists, start the dashboard:
   `cd frontend`
   `npm run dev`
2. If you want a live local-chain update instead of dry-run sync, deploy the vault, set `VAULT_ADDRESS` and `PRIVATE_KEY`, enable broadcast in `configs/integration/default.yaml`, then rerun the sync stage.