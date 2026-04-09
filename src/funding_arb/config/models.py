"""Typed config models for the Python-side pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SettingsBase(BaseModel):
    """Base settings model with permissive extra handling for easy extension."""

    model_config = ConfigDict(extra="allow")


class DataDatasetSettings(SettingsBase):
    symbol: str
    venue: str
    reference_source: str
    frequency: str
    start: str
    end: str


class DataSourceSettings(SettingsBase):
    enabled: bool = True
    endpoint: str


class DataPathSettings(SettingsBase):
    raw_dir: str = "data/raw"
    interim_dir: str = "data/interim"


class DataSettings(SettingsBase):
    dataset: DataDatasetSettings
    sources: dict[str, DataSourceSettings]
    paths: DataPathSettings
    notes: dict[str, Any] = Field(default_factory=dict)


class FeatureSetSettings(SettingsBase):
    rolling_windows: list[int] = Field(default_factory=list)
    volatility_window: int
    zscore_window: int
    funding_mean_window: int
    basis_mean_window: int


class LabelSettings(SettingsBase):
    forward_horizon_hours: int
    min_expected_edge_bps: float
    use_post_cost_target: bool = True


class FeatureOutputSettings(SettingsBase):
    processed_dir: str = "data/processed"
    artifact_name: str = "feature_set.parquet"


class FeatureSettings(SettingsBase):
    feature_set: FeatureSetSettings
    labels: LabelSettings
    output: FeatureOutputSettings


class ModelSplitSettings(SettingsBase):
    train_end: str
    validation_end: str
    test_end: str


class ModelTrainingSettings(SettingsBase):
    split: ModelSplitSettings | None = None
    batch_size: int | None = None
    epochs: int | None = None
    learning_rate: float | None = None
    seed: int | None = None


class ModelOutputSettings(SettingsBase):
    model_dir: str = "data/artifacts/models"


class BaselineModelSettings(SettingsBase):
    name: str
    entry_threshold: float | None = None
    exit_threshold: float | None = None
    max_holding_hours: int | None = None


class BaselineTrainingSettings(SettingsBase):
    split: ModelSplitSettings


class BaselineSettings(SettingsBase):
    model: BaselineModelSettings
    training: BaselineTrainingSettings
    output: ModelOutputSettings


class DeepLearningModelSettings(SettingsBase):
    name: str
    lookback_steps: int
    hidden_size: int
    num_layers: int
    dropout: float = 0.0


class DeepLearningSettings(SettingsBase):
    model: DeepLearningModelSettings
    training: ModelTrainingSettings
    output: ModelOutputSettings


class PortfolioSettings(SettingsBase):
    initial_capital: float
    position_notional: float
    max_open_positions: int


class CostSettings(SettingsBase):
    taker_fee_bps: float
    maker_fee_bps: float
    slippage_bps: float
    gas_cost_usd: float


class ExecutionSettings(SettingsBase):
    funding_interval_hours: int
    rebalance_frequency: str
    allow_partial_exit: bool = False


class ReportingSettings(SettingsBase):
    output_dir: str = "data/artifacts/backtests"


class BacktestSettings(SettingsBase):
    portfolio: PortfolioSettings
    costs: CostSettings
    execution: ExecutionSettings
    reporting: ReportingSettings