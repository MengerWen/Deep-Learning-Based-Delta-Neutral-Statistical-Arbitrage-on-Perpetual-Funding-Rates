"""Sequence-model deep-learning pipeline for the funding-rate arbitrage project."""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset

from funding_arb.config.models import DeepLearningSettings
from funding_arb.models.baselines import evaluate_prediction_table
from funding_arb.utils.paths import ensure_directory, repo_path


@dataclass(frozen=True)
class NormalizationStats:
    """Feature normalization parameters fitted on the training split only."""

    medians: dict[str, float]
    means: dict[str, float]
    stds: dict[str, float]


@dataclass(frozen=True)
class DeepLearningArtifacts:
    """Paths produced by the deep-learning training pipeline."""

    output_dir: str
    checkpoint_path: str
    history_path: str
    predictions_path: str
    predictions_csv_path: str | None
    metrics_path: str
    metrics_csv_path: str | None
    leaderboard_path: str
    leaderboard_csv_path: str | None
    report_path: str | None
    manifest_path: str
    feature_columns_path: str
    normalization_path: str


class SequenceDataset(Dataset[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]):
    """Lazy sliding-window dataset that slices only historical context for each target row."""

    def __init__(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        sample_indices: list[int],
        lookback_steps: int,
    ) -> None:
        self.features = features
        self.targets = targets
        self.sample_indices = sample_indices
        self.lookback_steps = lookback_steps

    def __len__(self) -> int:
        return len(self.sample_indices)

    def __getitem__(self, item: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        target_index = self.sample_indices[item]
        start_index = target_index - self.lookback_steps + 1
        sequence = torch.from_numpy(self.features[start_index : target_index + 1]).float()
        target = torch.tensor(self.targets[target_index], dtype=torch.float32)
        row_index = torch.tensor(target_index, dtype=torch.long)
        return sequence, target, row_index


class LSTMSequenceModel(nn.Module):
    """Simple LSTM encoder with a single scalar prediction head."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int,
        dropout: float,
        bidirectional: bool,
    ) -> None:
        super().__init__()
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.bidirectional = bidirectional
        self.encoder = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=lstm_dropout,
            bidirectional=bidirectional,
            batch_first=True,
        )
        output_size = hidden_size * (2 if bidirectional else 1)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(output_size, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        _, (hidden_state, _) = self.encoder(inputs)
        if self.bidirectional:
            encoded = torch.cat([hidden_state[-2], hidden_state[-1]], dim=1)
        else:
            encoded = hidden_state[-1]
        logits = self.head(self.dropout(encoded)).squeeze(-1)
        return logits


def describe_deep_learning_job(config: DeepLearningSettings | dict[str, Any]) -> str:
    """Return a human-readable summary of the deep-learning training job."""
    settings = config if isinstance(config, DeepLearningSettings) else DeepLearningSettings.model_validate(config)
    return (
        f"Deep-learning training ready for {settings.input.symbol} on {settings.input.provider} at "
        f"{settings.input.frequency}, task={settings.target.task}, target={settings.target.column}, "
        f"lookback={settings.sequence.lookback_steps}, epochs={settings.training.epochs}, "
        f"batch_size={settings.training.batch_size}. Artifacts will be written under "
        f"{settings.output.model_dir}/{settings.input.provider}/{settings.input.symbol.lower()}/"
        f"{settings.input.frequency}/{settings.output.run_name}."
    )


def _resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_path(*path.parts)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(converted) or math.isinf(converted):
        return None
    return converted


def _table_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "(no rows)"
    try:
        return frame.to_markdown(index=False)
    except Exception:
        return frame.to_string(index=False)


def _load_supervised_dataset(settings: DeepLearningSettings) -> pd.DataFrame:
    dataset_path = _resolve_path(settings.input.dataset_path)
    suffix = dataset_path.suffix.lower()
    if suffix == ".parquet":
        frame = pd.read_parquet(dataset_path)
    elif suffix == ".csv":
        frame = pd.read_csv(dataset_path)
    else:
        raise ValueError(f"Unsupported supervised dataset format: {dataset_path.suffix}")
    timestamp_column = settings.target.timestamp_column
    frame[timestamp_column] = pd.to_datetime(frame[timestamp_column], utc=True)
    return frame.sort_values(timestamp_column).reset_index(drop=True)


def select_feature_columns(frame: pd.DataFrame, settings: DeepLearningSettings) -> list[str]:
    """Select leakage-safe numeric features for sequence modeling."""
    feature_settings = settings.feature_selection
    if feature_settings.include_columns:
        columns = [column for column in feature_settings.include_columns if column in frame.columns]
    else:
        columns = frame.select_dtypes(include=["number", "bool"]).columns.tolist()
    excluded_columns = set(feature_settings.exclude_columns)
    columns = [
        column
        for column in columns
        if column not in excluded_columns
        and not any(column.startswith(prefix) for prefix in feature_settings.exclude_prefixes)
    ]
    if not columns:
        raise ValueError("Feature selection removed every candidate feature column for deep learning.")

    split_column = settings.target.split_column
    train_frame = frame[frame[split_column] == "train"].copy()
    candidate_frame = train_frame[columns].replace([np.inf, -np.inf], np.nan)
    missing_fraction = candidate_frame.isna().mean()
    columns = [
        column
        for column in columns
        if float(missing_fraction[column]) <= float(feature_settings.max_missing_fraction)
    ]
    if feature_settings.drop_constant_features:
        filtered_frame = candidate_frame[columns]
        columns = [column for column in columns if int(filtered_frame[column].nunique(dropna=True)) > 1]
    if not columns:
        raise ValueError("No usable feature columns remain for deep learning after filtering.")
    return sorted(columns)


def fit_normalization_stats(
    frame: pd.DataFrame,
    feature_columns: list[str],
    split_column: str,
) -> NormalizationStats:
    """Fit medians/means/stds on the training split only."""
    train_frame = frame.loc[frame[split_column] == "train", feature_columns].replace([np.inf, -np.inf], np.nan)
    medians = train_frame.median(skipna=True).fillna(0.0)
    filled_train = train_frame.fillna(medians)
    means = filled_train.mean().fillna(0.0)
    stds = filled_train.std(ddof=0).replace(0.0, 1.0).fillna(1.0)
    return NormalizationStats(
        medians={column: float(value) for column, value in medians.items()},
        means={column: float(value) for column, value in means.items()},
        stds={column: float(value) for column, value in stds.items()},
    )



def transform_features(
    frame: pd.DataFrame,
    feature_columns: list[str],
    stats: NormalizationStats,
) -> np.ndarray:
    """Impute and z-score features using training-only statistics."""
    feature_frame = frame[feature_columns].replace([np.inf, -np.inf], np.nan).copy()
    medians = pd.Series(stats.medians)
    means = pd.Series(stats.means)
    stds = pd.Series(stats.stds)
    feature_frame = feature_frame.fillna(medians)
    normalized = (feature_frame - means) / stds
    return normalized.astype("float32").to_numpy()



def build_sequence_indices(frame: pd.DataFrame, settings: DeepLearningSettings) -> dict[str, list[int]]:
    """Build split-specific target indices using only historical lookback windows."""
    lookback_steps = settings.sequence.lookback_steps
    split_column = settings.target.split_column
    ready_column = settings.target.ready_column
    target_column = settings.target.column
    allow_cross_split_context = settings.sequence.allow_cross_split_context

    target_values = pd.to_numeric(frame[target_column], errors="coerce")
    split_values = frame[split_column].astype(str)
    ready_values = frame[ready_column].fillna(0).astype(int)
    sample_indices: dict[str, list[int]] = {"train": [], "validation": [], "test": []}

    for row_index in range(lookback_steps - 1, len(frame)):
        split_name = split_values.iloc[row_index]
        if split_name not in sample_indices:
            continue
        if ready_values.iloc[row_index] != 1:
            continue
        if pd.isna(target_values.iloc[row_index]):
            continue
        start_index = row_index - lookback_steps + 1
        if not allow_cross_split_context:
            context_splits = split_values.iloc[start_index : row_index + 1]
            if not context_splits.eq(split_name).all():
                continue
        sample_indices[split_name].append(row_index)
    return sample_indices



def _build_dataloaders(
    features: np.ndarray,
    targets: np.ndarray,
    sample_indices: dict[str, list[int]],
    lookback_steps: int,
    batch_size: int,
    num_workers: int,
    pin_memory: bool,
) -> tuple[dict[str, SequenceDataset], dict[str, DataLoader]]:
    datasets = {
        split_name: SequenceDataset(features, targets, indices, lookback_steps)
        for split_name, indices in sample_indices.items()
    }
    loaders = {
        "train": DataLoader(
            datasets["train"],
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=pin_memory,
            drop_last=False,
        ),
        "validation": DataLoader(
            datasets["validation"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
            drop_last=False,
        ),
        "test": DataLoader(
            datasets["test"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
            drop_last=False,
        ),
    }
    return datasets, loaders



def _set_random_seed(seed: int, deterministic: bool) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False



def _select_device(device_name: str) -> torch.device:
    if device_name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_name)



def build_sequence_model(input_size: int, settings: DeepLearningSettings) -> nn.Module:
    """Dispatch to the configured sequence model implementation."""
    model_name = settings.model.name.lower()
    if model_name == "lstm":
        return LSTMSequenceModel(
            input_size=input_size,
            hidden_size=settings.model.hidden_size,
            num_layers=settings.model.num_layers,
            dropout=settings.model.dropout,
            bidirectional=settings.model.bidirectional,
        )
    raise ValueError(
        f"Unsupported deep-learning model '{settings.model.name}'. "
        "Only 'lstm' is implemented in the first prototype."
    )



def _loss_function(
    settings: DeepLearningSettings,
    device: torch.device,
    train_targets: np.ndarray,
) -> nn.Module:
    if settings.target.task == "classification":
        if settings.training.use_balanced_classification_loss:
            positives = float((train_targets > 0.5).sum())
            negatives = float((train_targets <= 0.5).sum())
            if positives > 0.0 and negatives > 0.0:
                pos_weight = torch.tensor([negatives / positives], dtype=torch.float32, device=device)
                return nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        return nn.BCEWithLogitsLoss()
    if settings.target.task == "regression":
        return nn.MSELoss()
    raise ValueError(f"Unsupported deep-learning task '{settings.target.task}'.")



def _prediction_payload(task: str, outputs: np.ndarray, threshold: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if task == "classification":
        probabilities = 1.0 / (1.0 + np.exp(-outputs))
        predicted_label = (probabilities >= threshold).astype(int)
        signal_strength = probabilities - threshold
        return probabilities.astype(float), predicted_label.astype(int), signal_strength.astype(float)
    predicted_return = outputs.astype(float)
    predicted_label = (predicted_return >= threshold).astype(int)
    signal_strength = predicted_return - threshold
    return predicted_return, predicted_label.astype(int), signal_strength.astype(float)


def _epoch_metrics(
    task: str,
    outputs: np.ndarray,
    targets: np.ndarray,
    threshold: float,
) -> dict[str, float | None]:
    if task == "classification":
        probabilities = 1.0 / (1.0 + np.exp(-outputs))
        predicted = (probabilities >= threshold).astype(int)
        actual = targets.astype(int)
        metrics: dict[str, float | None] = {
            "accuracy": _safe_float(accuracy_score(actual, predicted)),
            "precision": _safe_float(precision_score(actual, predicted, zero_division=0)),
            "recall": _safe_float(recall_score(actual, predicted, zero_division=0)),
            "f1": _safe_float(f1_score(actual, predicted, zero_division=0)),
        }
        if np.unique(actual).size >= 2 and np.unique(probabilities).size >= 2:
            metrics["roc_auc"] = _safe_float(roc_auc_score(actual, probabilities))
            metrics["average_precision"] = _safe_float(average_precision_score(actual, probabilities))
        else:
            metrics["roc_auc"] = None
            metrics["average_precision"] = None
        return metrics

    mae = mean_absolute_error(targets, outputs)
    rmse = math.sqrt(mean_squared_error(targets, outputs))
    metrics = {
        "mae": _safe_float(mae),
        "rmse": _safe_float(rmse),
        "directional_accuracy": _safe_float(((targets >= 0.0) == (outputs >= 0.0)).mean()),
    }
    metrics["r2"] = _safe_float(r2_score(targets, outputs)) if len(targets) > 1 else None
    if np.std(targets) > 0.0 and np.std(outputs) > 0.0:
        metrics["pearson_corr"] = _safe_float(np.corrcoef(targets, outputs)[0, 1])
    else:
        metrics["pearson_corr"] = None
    return metrics



def _run_loader(
    model: nn.Module,
    loader: DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
    task: str,
    optimizer: Adam | None,
    clip_grad_norm: float | None,
) -> dict[str, Any]:
    is_training = optimizer is not None
    model.train(mode=is_training)
    total_loss = 0.0
    sample_count = 0
    all_outputs: list[np.ndarray] = []
    all_targets: list[np.ndarray] = []
    all_row_indices: list[np.ndarray] = []

    context = torch.enable_grad() if is_training else torch.no_grad()
    with context:
        for sequences, targets, row_indices in loader:
            sequences = sequences.to(device)
            targets = targets.to(device)
            outputs = model(sequences)
            loss = loss_fn(outputs, targets)

            if is_training:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                if clip_grad_norm is not None and clip_grad_norm > 0.0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), clip_grad_norm)
                optimizer.step()

            batch_size = int(targets.shape[0])
            total_loss += float(loss.detach().item()) * batch_size
            sample_count += batch_size
            all_outputs.append(outputs.detach().cpu().numpy())
            all_targets.append(targets.detach().cpu().numpy())
            all_row_indices.append(row_indices.detach().cpu().numpy())

    if sample_count == 0:
        return {
            "loss": None,
            "outputs": np.array([], dtype=float),
            "targets": np.array([], dtype=float),
            "row_indices": np.array([], dtype=int),
        }

    return {
        "loss": total_loss / sample_count,
        "outputs": np.concatenate(all_outputs).astype(float),
        "targets": np.concatenate(all_targets).astype(float),
        "row_indices": np.concatenate(all_row_indices).astype(int),
    }



def _prediction_frame(
    frame: pd.DataFrame,
    row_indices: np.ndarray,
    outputs: np.ndarray,
    settings: DeepLearningSettings,
) -> pd.DataFrame:
    subset = frame.iloc[row_indices].copy().reset_index(drop=True)
    task = settings.target.task
    threshold = (
        settings.target.probability_threshold
        if task == "classification"
        else settings.target.trade_threshold_bps
    )
    decision_score, predicted_label, signal_strength = _prediction_payload(task, outputs, threshold)

    if task == "classification":
        predicted_probability = decision_score.astype(float)
        predicted_return_bps = np.full(len(subset), np.nan)
    else:
        predicted_probability = np.full(len(subset), np.nan)
        predicted_return_bps = decision_score.astype(float)

    return pd.DataFrame(
        {
            "timestamp": subset[settings.target.timestamp_column],
            "split": subset[settings.target.split_column],
            "model_name": settings.model.name,
            "model_family": "deep_learning",
            "task": task,
            "signal_direction": "short_perp_long_spot",
            "signal": predicted_label.astype(int),
            "decision_score": decision_score.astype(float),
            "signal_threshold": float(threshold),
            "signal_strength": signal_strength.astype(float),
            "predicted_probability": predicted_probability,
            "predicted_return_bps": predicted_return_bps,
            "predicted_label": predicted_label.astype(int),
            "actual_label": pd.to_numeric(subset[settings.target.classification_column], errors="coerce"),
            "actual_return_bps": pd.to_numeric(subset[settings.target.regression_column], errors="coerce"),
        }
    )



def _leaderboard(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics.copy()
    leaderboard = metrics[metrics["split"].isin(["validation", "test"])].copy()
    sort_keys = ["task", "split", "pearson_corr", "f1", "avg_signal_return_bps"]
    sort_keys = [key for key in sort_keys if key in leaderboard.columns]
    if sort_keys:
        leaderboard = leaderboard.sort_values(sort_keys, ascending=False, na_position="last")
    return leaderboard.reset_index(drop=True)



def _write_frame(frame: pd.DataFrame, path: Path) -> str:
    if path.suffix.lower() == ".parquet":
        frame.to_parquet(path, index=False)
    elif path.suffix.lower() == ".csv":
        frame.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")
    return str(path)



def _output_dir(settings: DeepLearningSettings) -> Path:
    return ensure_directory(
        _resolve_path(settings.output.model_dir)
        / settings.input.provider
        / settings.input.symbol.lower()
        / settings.input.frequency
        / settings.output.run_name
    )



def _write_report(
    settings: DeepLearningSettings,
    output_dir: Path,
    feature_columns: list[str],
    history: pd.DataFrame,
    metrics: pd.DataFrame,
    leaderboard: pd.DataFrame,
    best_epoch: int,
    device: str,
    sample_counts: dict[str, int],
) -> str | None:
    if not settings.output.write_markdown_report:
        return None
    report_path = output_dir / "training_report.md"
    lines = [
        "# Deep Learning Experiment Report",
        "",
        f"- Model: `{settings.model.name}`",
        f"- Task: `{settings.target.task}`",
        f"- Target column: `{settings.target.column}`",
        f"- Lookback steps: `{settings.sequence.lookback_steps}`",
        f"- Feature count: `{len(feature_columns)}`",
        f"- Device: `{device}`",
        f"- Best epoch: `{best_epoch}`",
        f"- Sample counts: `{sample_counts}`",
        "",
        "## Validation/Test Metrics",
        "",
        _table_to_markdown(leaderboard),
        "",
        "## Full Metrics",
        "",
        _table_to_markdown(metrics),
        "",
        "## Training History",
        "",
        _table_to_markdown(history),
        "",
        "## Notes",
        "",
        "- Sequences use only the target row and preceding feature rows; future context is never included.",
        "- Validation and test rows can reuse earlier historical context when `allow_cross_split_context=true`.",
        "- The current pipeline supports LSTM only, but the model builder is intentionally dispatch-based for future Transformer work.",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def run_deep_learning_pipeline(settings: DeepLearningSettings) -> DeepLearningArtifacts:
    """Train the first sequence-model deep-learning experiment and save reproducible artifacts."""
    _set_random_seed(settings.training.seed, settings.training.deterministic)
    frame = _load_supervised_dataset(settings)
    feature_columns = select_feature_columns(frame, settings)
    normalization = fit_normalization_stats(frame, feature_columns, settings.target.split_column)
    features = transform_features(frame, feature_columns, normalization)
    targets = pd.to_numeric(frame[settings.target.column], errors="coerce").astype(float).to_numpy()
    sample_indices = build_sequence_indices(frame, settings)

    if not sample_indices["train"]:
        raise ValueError("No train sequences were generated for the configured deep-learning task.")
    if not sample_indices["validation"]:
        raise ValueError("No validation sequences were generated for the configured deep-learning task.")

    device = _select_device(settings.training.device)
    pin_memory = device.type == "cuda"
    _, loaders = _build_dataloaders(
        features=features,
        targets=targets,
        sample_indices=sample_indices,
        lookback_steps=settings.sequence.lookback_steps,
        batch_size=settings.training.batch_size,
        num_workers=settings.training.num_workers,
        pin_memory=pin_memory,
    )

    model = build_sequence_model(len(feature_columns), settings).to(device)
    train_target_values = targets[np.array(sample_indices["train"], dtype=int)]
    loss_fn = _loss_function(settings, device, train_target_values)
    optimizer = Adam(
        model.parameters(),
        lr=settings.training.learning_rate,
        weight_decay=settings.training.weight_decay,
    )

    output_dir = _output_dir(settings)
    checkpoint_path = output_dir / "best_model.pt"
    feature_columns_path = output_dir / "feature_columns.json"
    normalization_path = output_dir / "feature_normalization.json"
    feature_columns_path.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")
    normalization_path.write_text(
        json.dumps(
            {
                "medians": normalization.medians,
                "means": normalization.means,
                "stds": normalization.stds,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    best_validation_loss = math.inf
    best_epoch = 0
    stale_epochs = 0
    history_rows: list[dict[str, Any]] = []
    threshold = (
        settings.target.probability_threshold
        if settings.target.task == "classification"
        else settings.target.trade_threshold_bps
    )

    for epoch in range(1, settings.training.epochs + 1):
        train_result = _run_loader(
            model=model,
            loader=loaders["train"],
            loss_fn=loss_fn,
            device=device,
            task=settings.target.task,
            optimizer=optimizer,
            clip_grad_norm=settings.training.clip_grad_norm,
        )
        validation_result = _run_loader(
            model=model,
            loader=loaders["validation"],
            loss_fn=loss_fn,
            device=device,
            task=settings.target.task,
            optimizer=None,
            clip_grad_norm=None,
        )

        row = {
            "epoch": epoch,
            "train_loss": _safe_float(train_result["loss"]),
            "validation_loss": _safe_float(validation_result["loss"]),
        }
        row.update({f"train_{key}": value for key, value in _epoch_metrics(settings.target.task, train_result["outputs"], train_result["targets"], threshold).items()})
        row.update({f"validation_{key}": value for key, value in _epoch_metrics(settings.target.task, validation_result["outputs"], validation_result["targets"], threshold).items()})
        history_rows.append(row)

        validation_loss = float(validation_result["loss"])
        if validation_loss < best_validation_loss:
            best_validation_loss = validation_loss
            best_epoch = epoch
            stale_epochs = 0
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "config": settings.model_dump(),
                    "feature_columns": feature_columns,
                    "normalization": {
                        "medians": normalization.medians,
                        "means": normalization.means,
                        "stds": normalization.stds,
                    },
                    "best_validation_loss": best_validation_loss,
                },
                checkpoint_path,
            )
        else:
            stale_epochs += 1
            if stale_epochs >= settings.training.early_stopping_patience:
                break

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])

    predictions_by_split: list[pd.DataFrame] = []
    for split_name in ["train", "validation", "test"]:
        if len(loaders[split_name].dataset) == 0:
            continue
        result = _run_loader(
            model=model,
            loader=loaders[split_name],
            loss_fn=loss_fn,
            device=device,
            task=settings.target.task,
            optimizer=None,
            clip_grad_norm=None,
        )
        predictions_by_split.append(_prediction_frame(frame, result["row_indices"], result["outputs"], settings))

    predictions = pd.concat(predictions_by_split, ignore_index=True).sort_values(["split", "timestamp"]).reset_index(drop=True)
    metrics = evaluate_prediction_table(predictions)
    leaderboard = _leaderboard(metrics)
    history = pd.DataFrame(history_rows)

    history_path = output_dir / "training_history.csv"
    history.to_csv(history_path, index=False)
    predictions_path = output_dir / "dl_predictions.parquet"
    metrics_path = output_dir / "dl_metrics.parquet"
    predictions_primary_path = _write_frame(predictions, predictions_path)
    metrics_primary_path = _write_frame(metrics, metrics_path)

    predictions_csv_path: str | None = None
    metrics_csv_path: str | None = None
    leaderboard_csv_path: str | None = None
    if settings.output.write_csv:
        predictions_csv_path = _write_frame(predictions, predictions_path.with_suffix(".csv"))
        metrics_csv_path = _write_frame(metrics, metrics_path.with_suffix(".csv"))
        leaderboard_csv_path = _write_frame(leaderboard, output_dir / "dl_leaderboard.csv")

    leaderboard_path = _write_frame(leaderboard, output_dir / "dl_leaderboard.parquet")
    report_path = _write_report(
        settings=settings,
        output_dir=output_dir,
        feature_columns=feature_columns,
        history=history,
        metrics=metrics,
        leaderboard=leaderboard,
        best_epoch=best_epoch,
        device=str(device),
        sample_counts={split_name: len(indices) for split_name, indices in sample_indices.items()},
    )

    manifest = {
        "input": settings.input.model_dump(),
        "target": settings.target.model_dump(),
        "feature_selection": settings.feature_selection.model_dump(),
        "sequence": settings.sequence.model_dump(),
        "model": settings.model.model_dump(),
        "training": settings.training.model_dump(),
        "row_count": int(len(frame)),
        "feature_count": len(feature_columns),
        "sample_counts": {split_name: len(indices) for split_name, indices in sample_indices.items()},
        "best_epoch": int(best_epoch),
        "best_validation_loss": _safe_float(best_validation_loss),
        "device": str(device),
        "checkpoint_path": str(checkpoint_path),
        "history_path": str(history_path),
        "predictions_path": predictions_primary_path,
        "predictions_csv_path": predictions_csv_path,
        "metrics_path": metrics_primary_path,
        "metrics_csv_path": metrics_csv_path,
        "leaderboard_path": leaderboard_path,
        "leaderboard_csv_path": leaderboard_csv_path,
        "feature_columns_path": str(feature_columns_path),
        "normalization_path": str(normalization_path),
        "report_path": report_path,
    }
    manifest_path = output_dir / "dl_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return DeepLearningArtifacts(
        output_dir=str(output_dir),
        checkpoint_path=str(checkpoint_path),
        history_path=str(history_path),
        predictions_path=predictions_primary_path,
        predictions_csv_path=predictions_csv_path,
        metrics_path=metrics_primary_path,
        metrics_csv_path=metrics_csv_path,
        leaderboard_path=leaderboard_path,
        leaderboard_csv_path=leaderboard_csv_path,
        report_path=report_path,
        manifest_path=str(manifest_path),
        feature_columns_path=str(feature_columns_path),
        normalization_path=str(normalization_path),
    )
