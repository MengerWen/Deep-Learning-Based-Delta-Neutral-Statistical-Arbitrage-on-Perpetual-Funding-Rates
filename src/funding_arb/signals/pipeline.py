"""Unified signal-generation pipeline for baseline and deep-learning strategy sources."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from funding_arb.config.models import SignalSettings
from funding_arb.signals.adapters import adapt_baseline_predictions, adapt_deep_learning_predictions
from funding_arb.utils.paths import ensure_directory, repo_path


@dataclass(frozen=True)
class SignalArtifacts:
    """Paths produced by the unified signal-generation pipeline."""

    signals_path: str
    signals_csv_path: str | None
    manifest_path: str
    output_dir: str



def describe_signal_job(config: SignalSettings | dict[str, Any]) -> str:
    """Return a human-readable summary of the signal-generation job."""
    settings = config if isinstance(config, SignalSettings) else SignalSettings.model_validate(config)
    return (
        f"Signal generation ready for source={settings.source.name} on {settings.input.symbol} "
        f"({settings.input.provider}, {settings.input.frequency}), writing normalized signals under "
        f"{settings.output.output_dir}/{settings.input.provider}/{settings.input.symbol.lower()}/"
        f"{settings.input.frequency}/{settings.source.name.lower()}."
    )



def _resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return repo_path(*path.parts)



def _output_dir(settings: SignalSettings) -> Path:
    source_dir = settings.source.name.lower().replace(" ", "_")
    return ensure_directory(
        _resolve_path(settings.output.output_dir)
        / settings.input.provider
        / settings.input.symbol.lower()
        / settings.input.frequency
        / source_dir
    )



def _write_frame(frame: pd.DataFrame, path: Path) -> str:
    if path.suffix.lower() == ".parquet":
        frame.to_parquet(path, index=False)
    elif path.suffix.lower() == ".csv":
        frame.to_csv(path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")
    return str(path)



def _signal_summary(frame: pd.DataFrame) -> dict[str, Any]:
    strategy_columns = [
        "strategy_name",
        "source_subtype",
        "model_family",
        "task",
        "signal_threshold",
        "threshold_objective",
        "prediction_mode",
        "calibration_method",
        "feature_importance_method",
    ]
    strategy_summary = (
        frame[strategy_columns]
        .drop_duplicates()
        .sort_values(["strategy_name", "source_subtype"])
        .reset_index(drop=True)
        .to_dict(orient="records")
    )
    return {
        "row_count": int(len(frame)),
        "active_signal_count": int(frame["should_trade"].sum()),
        "active_signal_rate": float(frame["should_trade"].mean()) if not frame.empty else 0.0,
        "strategies": sorted(frame["strategy_name"].dropna().astype(str).unique().tolist()),
        "source_subtypes": sorted(frame["source_subtype"].dropna().astype(str).unique().tolist()),
        "prediction_modes": sorted(frame["prediction_mode"].dropna().astype(str).unique().tolist()),
        "calibration_methods": sorted(frame["calibration_method"].dropna().astype(str).unique().tolist()),
        "feature_importance_methods": sorted(frame["feature_importance_method"].dropna().astype(str).unique().tolist()),
        "threshold_objectives": sorted(frame["threshold_objective"].dropna().astype(str).unique().tolist()),
        "splits": frame["split"].value_counts().to_dict(),
        "directions": frame["suggested_direction"].value_counts().to_dict(),
        "strategy_summary": strategy_summary,
    }



def run_signal_generation(settings: SignalSettings) -> SignalArtifacts:
    """Normalize one strategy/model source into the shared signal artifact format."""
    source_name = settings.source.name.lower()
    if source_name in {"baseline", "rules", "rule-based", "rule_based", "baseline-ml", "baseline_ml", "ml"}:
        signals = adapt_baseline_predictions(settings)
    elif source_name == "dl":
        signals = adapt_deep_learning_predictions(settings)
    else:
        raise ValueError(
            f"Unsupported signal source '{settings.source.name}'. Use one of: baseline, rules, baseline-ml, dl."
        )

    output_dir = _output_dir(settings)
    signals_path = output_dir / settings.output.artifact_name
    if signals_path.suffix.lower() not in {".parquet", ".csv"}:
        raise ValueError("Signal artifact_name must end with .parquet or .csv")
    signals_primary_path = _write_frame(signals, signals_path)

    signals_csv_path: str | None = None
    if settings.output.write_csv and signals_path.suffix.lower() != ".csv":
        signals_csv_path = _write_frame(signals, signals_path.with_suffix(".csv"))

    manifest = {
        "input": settings.input.model_dump(),
        "source": settings.source.model_dump(),
        "output": settings.output.model_dump(),
        "summary": _signal_summary(signals),
        "signals_path": signals_primary_path,
        "signals_csv_path": signals_csv_path,
    }
    manifest_path = output_dir / settings.output.manifest_name
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return SignalArtifacts(
        signals_path=signals_primary_path,
        signals_csv_path=signals_csv_path,
        manifest_path=str(manifest_path),
        output_dir=str(output_dir),
    )
