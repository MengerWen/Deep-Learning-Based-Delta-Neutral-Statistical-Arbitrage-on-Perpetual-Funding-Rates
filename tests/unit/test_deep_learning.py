from __future__ import annotations

import numpy as np
import pandas as pd
import torch

from funding_arb.config.models import DeepLearningSettings
from funding_arb.models.deep_learning import (
    LSTMSequenceModel,
    SequenceDataset,
    build_sequence_indices,
)



def _settings(allow_cross_split_context: bool = True) -> DeepLearningSettings:
    return DeepLearningSettings.model_validate(
        {
            "input": {
                "dataset_path": "data/processed/supervised/binance/btcusdt/1h/btcusdt_supervised_dataset.parquet",
                "provider": "binance",
                "symbol": "BTCUSDT",
                "venue": "binance",
                "frequency": "1h",
            },
            "target": {
                "task": "regression",
                "column": "target_future_net_return_bps_24h",
                "classification_column": "target_is_profitable_24h",
                "regression_column": "target_future_net_return_bps_24h",
                "timestamp_column": "timestamp",
                "split_column": "split",
                "ready_column": "supervised_ready",
            },
            "feature_selection": {},
            "sequence": {
                "lookback_steps": 3,
                "allow_cross_split_context": allow_cross_split_context,
            },
            "model": {
                "name": "lstm",
                "hidden_size": 8,
                "num_layers": 1,
                "dropout": 0.0,
                "bidirectional": False,
            },
            "training": {
                "batch_size": 2,
                "epochs": 1,
                "learning_rate": 0.001,
                "weight_decay": 0.0,
                "seed": 42,
                "device": "cpu",
                "num_workers": 0,
                "clip_grad_norm": 1.0,
                "early_stopping_patience": 1,
                "deterministic": True,
            },
            "output": {
                "model_dir": "data/artifacts/models/dl",
                "run_name": "unit_test",
                "write_csv": True,
                "write_markdown_report": False,
            },
        }
    )



def test_build_sequence_indices_respects_lookback_and_cross_split_context() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=6, freq="h", tz="UTC"),
            "split": ["train", "train", "train", "validation", "validation", "test"],
            "supervised_ready": [1, 1, 1, 1, 1, 1],
            "target_future_net_return_bps_24h": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "target_is_profitable_24h": [0, 0, 1, 1, 1, 1],
        }
    )

    with_cross = build_sequence_indices(frame, _settings(True))
    without_cross = build_sequence_indices(frame, _settings(False))

    assert with_cross == {"train": [2], "validation": [3, 4], "test": [5]}
    assert without_cross == {"train": [2], "validation": [], "test": []}



def test_sequence_dataset_returns_expected_historical_window() -> None:
    features = np.arange(24, dtype=np.float32).reshape(6, 4)
    targets = np.array([0, 1, 2, 3, 4, 5], dtype=np.float32)
    dataset = SequenceDataset(features=features, targets=targets, sample_indices=[2, 4], lookback_steps=3)

    sequence, target, row_index = dataset[1]

    assert sequence.shape == (3, 4)
    assert torch.equal(sequence, torch.tensor(features[2:5]))
    assert float(target.item()) == 4.0
    assert int(row_index.item()) == 4



def test_lstm_sequence_model_forward_shape_is_batch_scalar() -> None:
    model = LSTMSequenceModel(
        input_size=5,
        hidden_size=8,
        num_layers=2,
        dropout=0.1,
        bidirectional=False,
    )
    batch = torch.randn(4, 12, 5)

    output = model(batch)

    assert output.shape == (4,)
