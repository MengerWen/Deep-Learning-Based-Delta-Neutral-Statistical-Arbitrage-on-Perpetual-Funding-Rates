"""Baseline strategy and predictive-model pipeline for the funding-rate arbitrage project."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import dump, load
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
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
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from funding_arb.config.models import BaselineSettings, RuleBaselineSpec
from funding_arb.utils.paths import ensure_directory, repo_path


@dataclass(frozen=True)
class BaselineArtifacts:
    """Paths produced by the baseline training/evaluation pipeline."""

    output_dir: str
    manifest_path: str
    metrics_path: str
    metrics_csv_path: str | None
    leaderboard_path: str
    leaderboard_csv_path: str | None
    predictions_path: str
    predictions_csv_path: str | None
    report_path: str | None
    feature_columns_path: str
    model_paths: dict[str, str]
    diagnostic_paths: dict[str, str]


def describe_baseline_job(config: BaselineSettings | dict[str, Any]) -> str:
    """Return a human-readable summary of the baseline training job."""
    settings = config if isinstance(config, BaselineSettings) else BaselineSettings.model_validate(config)
    rule_count = sum(1 for rule in settings.rules if rule.enabled)
    predictive_names: list[str] = []
    if settings.predictive.classification.enabled:
        predictive_names.append(settings.predictive.classification.name)
    if settings.predictive.regression.enabled:
        predictive_names.append(settings.predictive.regression.name)
    if settings.predictive.tree.enabled:
        predictive_names.extend(
            [
                settings.predictive.tree.classifier_name,
                settings.predictive.tree.regressor_name,
            ]
        )
    return (
        f"Baseline training ready for {settings.input.symbol} on {settings.input.provider} at "
        f"{settings.input.frequency}, using {rule_count} rule models and {len(predictive_names)} predictive models. "
        f"Artifacts will be written under {settings.output.model_dir}/{settings.input.provider}/"
        f"{settings.input.symbol.lower()}/{settings.input.frequency}/{settings.output.run_name}."
    )


def describe_baseline_evaluation_job(config: BaselineSettings | dict[str, Any]) -> str:
    """Return a human-readable summary of the baseline evaluation job."""
    settings = config if isinstance(config, BaselineSettings) else BaselineSettings.model_validate(config)
    return (
        f"Baseline evaluation ready for {settings.input.symbol} on {settings.input.provider} at "
        f"{settings.input.frequency}, loading trained artifacts from {settings.output.model_dir}/{settings.input.provider}/"
        f"{settings.input.symbol.lower()}/{settings.input.frequency}/{settings.output.run_name}."
    )


def _resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_path(*path.parts)


def _load_supervised_dataset(settings: BaselineSettings) -> pd.DataFrame:
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
    frame = frame.sort_values(timestamp_column).reset_index(drop=True)
    ready_column = settings.target.ready_column
    split_column = settings.target.split_column
    frame = frame[(frame[ready_column] == 1) & frame[split_column].isin(["train", "validation", "test"])].copy()
    if frame.empty:
        raise ValueError("No supervised-ready rows were found for baseline modeling.")
    return frame


def select_feature_columns(frame: pd.DataFrame, settings: BaselineSettings) -> list[str]:
    """Select leakage-safe numeric feature columns for predictive baselines."""
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
        raise ValueError("Feature selection removed every candidate feature column.")

    candidate_frame = frame[columns].replace([np.inf, -np.inf], np.nan)
    missing_fraction = candidate_frame.isna().mean()
    columns = [
        column
        for column in columns
        if float(missing_fraction[column]) <= float(feature_settings.max_missing_fraction)
    ]
    if feature_settings.drop_constant_features:
        non_constant: list[str] = []
        filtered_frame = candidate_frame[columns]
        for column in columns:
            unique_count = filtered_frame[column].nunique(dropna=True)
            if int(unique_count) > 1:
                non_constant.append(column)
        columns = non_constant
    if not columns:
        raise ValueError("No usable feature columns remain after missing-value and variance filtering.")
    return sorted(columns)


def _output_dir(settings: BaselineSettings) -> Path:
    return ensure_directory(
        _resolve_path(settings.output.model_dir)
        / settings.input.provider
        / settings.input.symbol.lower()
        / settings.input.frequency
        / settings.output.run_name
    )


def _write_frame(frame: pd.DataFrame, path: Path) -> str:
    if path.suffix.lower() == ".parquet":
        frame.to_parquet(path, index=False)
    elif path.suffix.lower() == ".csv":
        frame.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")
    return str(path)


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


def _mean_or_none(series: pd.Series) -> float | None:
    if series.empty:
        return None
    return _safe_float(series.mean())


def _median_or_none(series: pd.Series) -> float | None:
    if series.empty:
        return None
    return _safe_float(series.median())


def _sum_or_none(series: pd.Series) -> float | None:
    if series.empty:
        return None
    return _safe_float(series.sum())


def _feature_matrix(frame: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    return frame[feature_columns].replace([np.inf, -np.inf], np.nan)

def _build_classifier_pipeline(settings: BaselineSettings) -> Pipeline:
    classifier_settings = settings.predictive.classification
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if classifier_settings.standardize:
        steps.append(("scaler", StandardScaler()))
    steps.append(
        (
            "model",
            LogisticRegression(
                C=classifier_settings.c,
                class_weight=classifier_settings.class_weight,
                max_iter=classifier_settings.max_iter,
                random_state=classifier_settings.random_state,
            ),
        )
    )
    return Pipeline(steps)


def _build_regression_pipeline(settings: BaselineSettings) -> Pipeline:
    regression_settings = settings.predictive.regression
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if regression_settings.standardize:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", Ridge(alpha=regression_settings.alpha)))
    return Pipeline(steps)


def _build_tree_classifier(settings: BaselineSettings) -> Pipeline:
    tree_settings = settings.predictive.tree
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=tree_settings.n_estimators,
                    max_depth=tree_settings.max_depth,
                    min_samples_leaf=tree_settings.min_samples_leaf,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                    random_state=tree_settings.random_state,
                ),
            ),
        ]
    )


def _build_tree_regressor(settings: BaselineSettings) -> Pipeline:
    tree_settings = settings.predictive.tree
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=tree_settings.n_estimators,
                    max_depth=tree_settings.max_depth,
                    min_samples_leaf=tree_settings.min_samples_leaf,
                    n_jobs=-1,
                    random_state=tree_settings.random_state,
                ),
            ),
        ]
    )


def _rule_prediction_frame(
    frame: pd.DataFrame,
    settings: BaselineSettings,
    rule: RuleBaselineSpec,
) -> pd.DataFrame:
    timestamp_column = settings.target.timestamp_column
    split_column = settings.target.split_column
    classification_column = settings.target.classification_column
    regression_column = settings.target.regression_column

    if rule.kind == "funding_threshold":
        decision_score = frame[rule.funding_column].astype(float)
        signal_threshold = float(rule.funding_threshold_bps)
        signal = decision_score >= signal_threshold
    elif rule.kind == "spread_zscore_threshold":
        decision_score = frame[rule.spread_column].astype(float)
        signal_threshold = float(rule.spread_threshold)
        signal = decision_score >= signal_threshold
    elif rule.kind == "combined_threshold":
        funding_margin = frame[rule.funding_column].astype(float) - float(rule.funding_threshold_bps)
        spread_margin = frame[rule.spread_column].astype(float) - float(rule.spread_threshold)
        decision_score = funding_margin.add(spread_margin, fill_value=0.0)
        signal_threshold = 0.0
        signal = (funding_margin >= 0.0) & (spread_margin >= 0.0)
    else:
        raise ValueError(f"Unsupported rule baseline kind: {rule.kind}")

    if rule.regime_column is not None:
        signal = signal & frame[rule.regime_column].eq(rule.regime_value)

    predictions = pd.DataFrame(
        {
            "timestamp": frame[timestamp_column],
            "split": frame[split_column],
            "model_name": rule.name,
            "model_family": "rule_based",
            "task": "classification",
            "signal_direction": "short_perp_long_spot",
            "signal": signal.astype(int),
            "decision_score": decision_score.astype(float),
            "signal_threshold": float(signal_threshold),
            "signal_strength": decision_score.astype(float) - float(signal_threshold),
            "predicted_probability": np.nan,
            "predicted_return_bps": np.nan,
            "predicted_label": signal.astype(int),
            "actual_label": pd.to_numeric(frame[classification_column], errors="coerce"),
            "actual_return_bps": pd.to_numeric(frame[regression_column], errors="coerce"),
        }
    )
    return predictions


def _fit_or_load_model(
    estimator: Pipeline,
    train_frame: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    artifact_path: Path,
    train_models: bool,
) -> Pipeline:
    if train_models:
        estimator.fit(_feature_matrix(train_frame, feature_columns), train_frame[target_column])
        dump(estimator, artifact_path)
        return estimator
    if not artifact_path.exists():
        raise FileNotFoundError(f"Missing trained model artifact: {artifact_path}")
    loaded_estimator = load(artifact_path)
    if not isinstance(loaded_estimator, Pipeline):
        raise TypeError(f"Model artifact at {artifact_path} is not a scikit-learn Pipeline.")
    return loaded_estimator


def _extract_linear_coefficients(model: Pipeline, feature_columns: list[str]) -> pd.DataFrame | None:
    estimator = model.named_steps.get("model")
    if estimator is None or not hasattr(estimator, "coef_"):
        return None
    coefficients = np.asarray(estimator.coef_)
    if coefficients.ndim > 1:
        coefficients = coefficients[0]
    frame = pd.DataFrame(
        {
            "feature": feature_columns,
            "coefficient": coefficients.astype(float),
        }
    )
    frame["abs_coefficient"] = frame["coefficient"].abs()
    return frame.sort_values("abs_coefficient", ascending=False).reset_index(drop=True)


def _extract_tree_importances(model: Pipeline, feature_columns: list[str]) -> pd.DataFrame | None:
    estimator = model.named_steps.get("model")
    if estimator is None or not hasattr(estimator, "feature_importances_"):
        return None
    frame = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": np.asarray(estimator.feature_importances_, dtype=float),
        }
    )
    return frame.sort_values("importance", ascending=False).reset_index(drop=True)


def _write_diagnostics(
    diagnostics_dir: Path,
    model_name: str,
    diagnostic_frame: pd.DataFrame | None,
) -> str | None:
    if diagnostic_frame is None:
        return None
    diagnostic_path = diagnostics_dir / f"{model_name}_diagnostics.csv"
    diagnostic_frame.to_csv(diagnostic_path, index=False)
    return str(diagnostic_path)

def _predict_classifier(
    frame: pd.DataFrame,
    settings: BaselineSettings,
    model_name: str,
    model_family: str,
    model: Pipeline,
    feature_columns: list[str],
    probability_threshold: float,
) -> pd.DataFrame:
    probabilities = model.predict_proba(_feature_matrix(frame, feature_columns))[:, 1]
    predicted_label = (probabilities >= probability_threshold).astype(int)
    return pd.DataFrame(
        {
            "timestamp": frame[settings.target.timestamp_column],
            "split": frame[settings.target.split_column],
            "model_name": model_name,
            "model_family": model_family,
            "task": "classification",
            "signal_direction": "short_perp_long_spot",
            "signal": predicted_label.astype(int),
            "decision_score": probabilities.astype(float),
            "signal_threshold": float(probability_threshold),
            "signal_strength": probabilities.astype(float) - float(probability_threshold),
            "predicted_probability": probabilities.astype(float),
            "predicted_return_bps": np.nan,
            "predicted_label": predicted_label.astype(int),
            "actual_label": pd.to_numeric(frame[settings.target.classification_column], errors="coerce"),
            "actual_return_bps": pd.to_numeric(frame[settings.target.regression_column], errors="coerce"),
        }
    )


def _predict_regressor(
    frame: pd.DataFrame,
    settings: BaselineSettings,
    model_name: str,
    model_family: str,
    model: Pipeline,
    feature_columns: list[str],
    trade_threshold_bps: float,
) -> pd.DataFrame:
    predicted_return = model.predict(_feature_matrix(frame, feature_columns)).astype(float)
    signal = predicted_return >= float(trade_threshold_bps)
    return pd.DataFrame(
        {
            "timestamp": frame[settings.target.timestamp_column],
            "split": frame[settings.target.split_column],
            "model_name": model_name,
            "model_family": model_family,
            "task": "regression",
            "signal_direction": "short_perp_long_spot",
            "signal": signal.astype(int),
            "decision_score": predicted_return.astype(float),
            "signal_threshold": float(trade_threshold_bps),
            "signal_strength": predicted_return.astype(float) - float(trade_threshold_bps),
            "predicted_probability": np.nan,
            "predicted_return_bps": predicted_return.astype(float),
            "predicted_label": signal.astype(int),
            "actual_label": pd.to_numeric(frame[settings.target.classification_column], errors="coerce"),
            "actual_return_bps": pd.to_numeric(frame[settings.target.regression_column], errors="coerce"),
        }
    )


def _classification_metrics(predictions: pd.DataFrame) -> dict[str, Any]:
    usable = predictions.dropna(subset=["actual_label"]).copy()
    if usable.empty:
        return {}
    y_true = usable["actual_label"].astype(int)
    y_pred = usable["predicted_label"].astype(int)
    y_score = usable["predicted_probability"].copy()
    if y_score.isna().all():
        y_score = usable["decision_score"].astype(float)

    signaled = usable[usable["signal"] == 1]["actual_return_bps"].dropna()
    metrics = {
        "row_count": int(len(usable)),
        "actual_positive_count": int(y_true.sum()),
        "predicted_positive_count": int(y_pred.sum()),
        "actual_positive_rate": _safe_float(y_true.mean()),
        "predicted_positive_rate": _safe_float(y_pred.mean()),
        "accuracy": _safe_float(accuracy_score(y_true, y_pred)),
        "precision": _safe_float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": _safe_float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": _safe_float(f1_score(y_true, y_pred, zero_division=0)),
        "signal_count": int((usable["signal"] == 1).sum()),
        "signal_rate": _safe_float((usable["signal"] == 1).mean()),
        "avg_signal_return_bps": _mean_or_none(signaled),
        "median_signal_return_bps": _median_or_none(signaled),
        "cumulative_signal_return_bps": _sum_or_none(signaled),
        "signal_hit_rate": _safe_float((signaled > 0.0).mean()) if not signaled.empty else None,
    }
    if y_true.nunique() >= 2 and y_score.nunique(dropna=True) >= 2:
        metrics["roc_auc"] = _safe_float(roc_auc_score(y_true, y_score))
        metrics["average_precision"] = _safe_float(average_precision_score(y_true, y_score))
    else:
        metrics["roc_auc"] = None
        metrics["average_precision"] = None
    return metrics


def _regression_metrics(predictions: pd.DataFrame) -> dict[str, Any]:
    usable = predictions.dropna(subset=["actual_return_bps", "predicted_return_bps"]).copy()
    if usable.empty:
        return {}
    y_true = usable["actual_return_bps"].astype(float)
    y_pred = usable["predicted_return_bps"].astype(float)
    signaled = usable[usable["signal"] == 1]["actual_return_bps"].dropna()
    metrics = {
        "row_count": int(len(usable)),
        "mae": _safe_float(mean_absolute_error(y_true, y_pred)),
        "rmse": _safe_float(math.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": _safe_float(r2_score(y_true, y_pred)) if len(usable) > 1 else None,
        "directional_accuracy": _safe_float(((y_true >= 0.0) == (y_pred >= 0.0)).mean()),
        "predicted_positive_rate": _safe_float((y_pred >= 0.0).mean()),
        "signal_count": int((usable["signal"] == 1).sum()),
        "signal_rate": _safe_float((usable["signal"] == 1).mean()),
        "avg_signal_return_bps": _mean_or_none(signaled),
        "median_signal_return_bps": _median_or_none(signaled),
        "cumulative_signal_return_bps": _sum_or_none(signaled),
        "signal_hit_rate": _safe_float((signaled > 0.0).mean()) if not signaled.empty else None,
    }
    if y_true.std(ddof=0) > 0.0 and y_pred.std(ddof=0) > 0.0:
        metrics["pearson_corr"] = _safe_float(np.corrcoef(y_true, y_pred)[0, 1])
    else:
        metrics["pearson_corr"] = None
    return metrics


def evaluate_prediction_table(predictions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate split-aware metrics from a combined prediction table."""
    rows: list[dict[str, Any]] = []
    grouped = predictions.groupby(["model_name", "model_family", "task", "split"], sort=True)
    for (model_name, model_family, task, split), group in grouped:
        if task == "regression":
            metrics = _regression_metrics(group)
        else:
            metrics = _classification_metrics(group)
        row = {
            "model_name": model_name,
            "model_family": model_family,
            "task": task,
            "split": split,
        }
        row.update(metrics)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["task", "model_family", "model_name", "split"]).reset_index(drop=True)


def _build_leaderboard(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics.copy()
    leaderboard = metrics[metrics["split"].isin(["validation", "test"])].copy()
    sort_keys = ["task", "split", "avg_signal_return_bps", "f1", "pearson_corr"]
    available_keys = [key for key in sort_keys if key in leaderboard.columns]
    if available_keys:
        leaderboard = leaderboard.sort_values(available_keys, ascending=False, na_position="last")
    return leaderboard.reset_index(drop=True)

def _table_to_markdown(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "(no rows)"
    try:
        return frame.to_markdown(index=False)
    except Exception:
        return frame.to_string(index=False)


def _write_markdown_report(
    settings: BaselineSettings,
    feature_columns: list[str],
    metrics: pd.DataFrame,
    leaderboard: pd.DataFrame,
    output_dir: Path,
) -> str | None:
    if not settings.output.write_markdown_report:
        return None
    report_path = output_dir / "baseline_report.md"
    task_columns = ["model_name", "split", "signal_count", "signal_rate", "avg_signal_return_bps"]
    classification_columns = task_columns + ["accuracy", "precision", "recall", "f1", "roc_auc"]
    regression_columns = task_columns + ["mae", "rmse", "r2", "pearson_corr"]
    classification_table = metrics[metrics["task"] == "classification"].copy()
    regression_table = metrics[metrics["task"] == "regression"].copy()
    lines = [
        "# Baseline Models Report",
        "",
        f"- Dataset: `{settings.input.dataset_path}`",
        f"- Classification target: `{settings.target.classification_column}`",
        f"- Regression target: `{settings.target.regression_column}`",
        f"- Feature count: `{len(feature_columns)}`",
        f"- Output directory: `{output_dir}`",
        "",
        "## Validation/Test Leaderboard",
        "",
        _table_to_markdown(leaderboard),
        "",
        "## Classification and Rule Baselines",
        "",
        _table_to_markdown(classification_table[[column for column in classification_columns if column in classification_table.columns]]),
        "",
        "## Regression Baselines",
        "",
        _table_to_markdown(regression_table[[column for column in regression_columns if column in regression_table.columns]]),
        "",
        "## Notes",
        "",
        "- Signals are aligned to the post-cost supervised dataset created by the label pipeline.",
        "- Rule-based baselines benchmark interpretable heuristics against simple ML predictors.",
        "- Current post-cost profitable labels are intentionally sparse; signal-return metrics are therefore reported alongside classification metrics.",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)


def run_baseline_pipeline(settings: BaselineSettings, train_models: bool = True) -> BaselineArtifacts:
    """Train or evaluate baseline strategies and predictive models."""
    frame = _load_supervised_dataset(settings)
    feature_columns = select_feature_columns(frame, settings)
    output_dir = _output_dir(settings)
    models_dir = ensure_directory(output_dir / "models")
    diagnostics_dir = ensure_directory(output_dir / "diagnostics")

    feature_columns_path = output_dir / "feature_columns.json"
    feature_columns_path.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")

    prediction_frames: list[pd.DataFrame] = []
    model_paths: dict[str, str] = {}
    diagnostic_paths: dict[str, str] = {}

    for rule in settings.rules:
        if not rule.enabled:
            continue
        prediction_frames.append(_rule_prediction_frame(frame, settings, rule))

    split_column = settings.target.split_column
    train_split = frame[frame[split_column] == "train"].copy()

    if settings.predictive.classification.enabled:
        target_column = settings.target.classification_column
        classifier_train = train_split.dropna(subset=[target_column]).copy()
        if classifier_train[target_column].nunique(dropna=True) >= 2:
            classifier_path = models_dir / f"{settings.predictive.classification.name}.joblib"
            classifier = _fit_or_load_model(
                _build_classifier_pipeline(settings),
                classifier_train,
                feature_columns,
                target_column,
                classifier_path,
                train_models,
            )
            model_paths[settings.predictive.classification.name] = str(classifier_path)
            coefficients = _extract_linear_coefficients(classifier, feature_columns)
            diagnostic_path = _write_diagnostics(
                diagnostics_dir,
                settings.predictive.classification.name,
                coefficients,
            )
            if diagnostic_path is not None:
                diagnostic_paths[settings.predictive.classification.name] = diagnostic_path
            classifier_frame = frame.dropna(subset=[target_column]).copy()
            prediction_frames.append(
                _predict_classifier(
                    classifier_frame,
                    settings,
                    settings.predictive.classification.name,
                    "linear",
                    classifier,
                    feature_columns,
                    settings.predictive.classification.probability_threshold,
                )
            )

    if settings.predictive.regression.enabled:
        target_column = settings.target.regression_column
        regressor_train = train_split.dropna(subset=[target_column]).copy()
        if not regressor_train.empty:
            regressor_path = models_dir / f"{settings.predictive.regression.name}.joblib"
            regressor = _fit_or_load_model(
                _build_regression_pipeline(settings),
                regressor_train,
                feature_columns,
                target_column,
                regressor_path,
                train_models,
            )
            model_paths[settings.predictive.regression.name] = str(regressor_path)
            coefficients = _extract_linear_coefficients(regressor, feature_columns)
            diagnostic_path = _write_diagnostics(
                diagnostics_dir,
                settings.predictive.regression.name,
                coefficients,
            )
            if diagnostic_path is not None:
                diagnostic_paths[settings.predictive.regression.name] = diagnostic_path
            regressor_frame = frame.dropna(subset=[target_column]).copy()
            prediction_frames.append(
                _predict_regressor(
                    regressor_frame,
                    settings,
                    settings.predictive.regression.name,
                    "linear",
                    regressor,
                    feature_columns,
                    settings.predictive.regression.trade_threshold_bps,
                )
            )

    if settings.predictive.tree.enabled:
        class_target = settings.target.classification_column
        tree_classifier_train = train_split.dropna(subset=[class_target]).copy()
        if tree_classifier_train[class_target].nunique(dropna=True) >= 2:
            tree_classifier_path = models_dir / f"{settings.predictive.tree.classifier_name}.joblib"
            tree_classifier = _fit_or_load_model(
                _build_tree_classifier(settings),
                tree_classifier_train,
                feature_columns,
                class_target,
                tree_classifier_path,
                train_models,
            )
            model_paths[settings.predictive.tree.classifier_name] = str(tree_classifier_path)
            diagnostic_path = _write_diagnostics(
                diagnostics_dir,
                settings.predictive.tree.classifier_name,
                _extract_tree_importances(tree_classifier, feature_columns),
            )
            if diagnostic_path is not None:
                diagnostic_paths[settings.predictive.tree.classifier_name] = diagnostic_path
            classifier_frame = frame.dropna(subset=[class_target]).copy()
            prediction_frames.append(
                _predict_classifier(
                    classifier_frame,
                    settings,
                    settings.predictive.tree.classifier_name,
                    "tree",
                    tree_classifier,
                    feature_columns,
                    settings.predictive.tree.classification_probability_threshold,
                )
            )

        reg_target = settings.target.regression_column
        tree_regressor_train = train_split.dropna(subset=[reg_target]).copy()
        if not tree_regressor_train.empty:
            tree_regressor_path = models_dir / f"{settings.predictive.tree.regressor_name}.joblib"
            tree_regressor = _fit_or_load_model(
                _build_tree_regressor(settings),
                tree_regressor_train,
                feature_columns,
                reg_target,
                tree_regressor_path,
                train_models,
            )
            model_paths[settings.predictive.tree.regressor_name] = str(tree_regressor_path)
            diagnostic_path = _write_diagnostics(
                diagnostics_dir,
                settings.predictive.tree.regressor_name,
                _extract_tree_importances(tree_regressor, feature_columns),
            )
            if diagnostic_path is not None:
                diagnostic_paths[settings.predictive.tree.regressor_name] = diagnostic_path
            regressor_frame = frame.dropna(subset=[reg_target]).copy()
            prediction_frames.append(
                _predict_regressor(
                    regressor_frame,
                    settings,
                    settings.predictive.tree.regressor_name,
                    "tree",
                    tree_regressor,
                    feature_columns,
                    settings.predictive.tree.regression_trade_threshold_bps,
                )
            )

    if not prediction_frames:
        raise ValueError("No baseline models were enabled or trainable under the current config.")

    predictions = pd.concat(prediction_frames, ignore_index=True)
    predictions = predictions.sort_values(["model_name", "timestamp"]).reset_index(drop=True)
    metrics = evaluate_prediction_table(predictions)
    leaderboard = _build_leaderboard(metrics)

    predictions_path = output_dir / "baseline_predictions.parquet"
    metrics_path = output_dir / "baseline_metrics.parquet"
    leaderboard_path = output_dir / "baseline_leaderboard.parquet"

    predictions_primary_path = _write_frame(predictions, predictions_path)
    metrics_primary_path = _write_frame(metrics, metrics_path)
    leaderboard_primary_path = _write_frame(leaderboard, leaderboard_path)

    predictions_csv_path: str | None = None
    metrics_csv_path: str | None = None
    leaderboard_csv_path: str | None = None
    if settings.output.write_csv:
        predictions_csv_path = _write_frame(predictions, predictions_path.with_suffix(".csv"))
        metrics_csv_path = _write_frame(metrics, metrics_path.with_suffix(".csv"))
        leaderboard_csv_path = _write_frame(leaderboard, leaderboard_path.with_suffix(".csv"))

    report_path = _write_markdown_report(settings, feature_columns, metrics, leaderboard, output_dir)

    split_counts = {
        split_name: int((frame[split_column] == split_name).sum()) for split_name in ["train", "validation", "test"]
    }
    manifest = {
        "input": settings.input.model_dump(),
        "target": settings.target.model_dump(),
        "feature_selection": settings.feature_selection.model_dump(),
        "rules": [rule.model_dump() for rule in settings.rules if rule.enabled],
        "predictive": settings.predictive.model_dump(),
        "train_models": train_models,
        "row_count": int(len(frame)),
        "split_counts": split_counts,
        "feature_count": len(feature_columns),
        "feature_columns_path": str(feature_columns_path),
        "predictions_path": predictions_primary_path,
        "predictions_csv_path": predictions_csv_path,
        "metrics_path": metrics_primary_path,
        "metrics_csv_path": metrics_csv_path,
        "leaderboard_path": leaderboard_primary_path,
        "leaderboard_csv_path": leaderboard_csv_path,
        "report_path": report_path,
        "model_paths": model_paths,
        "diagnostic_paths": diagnostic_paths,
    }
    manifest_path = output_dir / "baseline_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return BaselineArtifacts(
        output_dir=str(output_dir),
        manifest_path=str(manifest_path),
        metrics_path=metrics_primary_path,
        metrics_csv_path=metrics_csv_path,
        leaderboard_path=leaderboard_primary_path,
        leaderboard_csv_path=leaderboard_csv_path,
        predictions_path=predictions_primary_path,
        predictions_csv_path=predictions_csv_path,
        report_path=report_path,
        feature_columns_path=str(feature_columns_path),
        model_paths=model_paths,
        diagnostic_paths=diagnostic_paths,
    )
