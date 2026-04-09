"""Typed config models for the Python-side pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SettingsBase(BaseModel):
    """Base settings model with permissive extra handling for easy extension."""

    model_config = ConfigDict(extra="allow")


class DataProviderSettings(SettingsBase):
    provider: str = "binance"
    timeout_seconds: int = 30
    limit_per_request: int = 1000


class DataDatasetSettings(SettingsBase):
    symbol: str
    venue: str
    reference_source: str
    frequency: str
    start: str
    end: str
    perpetual_symbol: str | None = None
    spot_symbol: str | None = None


class DataSourceSettings(SettingsBase):
    enabled: bool = True
    endpoint: str


class DataCleaningSettings(SettingsBase):
    timezone: str = "UTC"
    drop_duplicates: bool = True
    sort_ascending: bool = True
    max_forward_fill_hours: int = 6
    fill_price_method: str = "ffill"
    fill_volume_value: float = 0.0
    fill_funding_value: float = 0.0
    fill_open_interest_method: str = "ffill"
    validate_frequency: bool = True


class DataOutputSettings(SettingsBase):
    format: str = "parquet"
    write_csv: bool = True
    raw_subdir: str = "data/raw"
    interim_subdir: str = "data/interim"
    processed_subdir: str = "data/processed"


class DataSettings(SettingsBase):
    source: DataProviderSettings = Field(default_factory=DataProviderSettings)
    dataset: DataDatasetSettings
    sources: dict[str, DataSourceSettings]
    cleaning: DataCleaningSettings = Field(default_factory=DataCleaningSettings)
    output: DataOutputSettings = Field(default_factory=DataOutputSettings)
    notes: dict[str, Any] = Field(default_factory=dict)


class FeatureInputSettings(SettingsBase):
    dataset_path: str = "data/processed/binance/btcusdt/1h/hourly_market_data.parquet"
    manifest_path: str | None = "data/processed/binance/btcusdt/1h/manifest.json"
    provider: str = "binance"
    symbol: str = "BTCUSDT"
    venue: str = "binance"
    frequency: str = "1h"


class FeatureSetSettings(SettingsBase):
    rolling_windows: list[int] = Field(default_factory=list)
    volatility_window: int
    zscore_window: int
    funding_mean_window: int
    basis_mean_window: int
    shock_window: int = 24
    liquidity_window: int = 24
    regime_window: int = 168
    funding_interval_hours: int = 8
    annualization_factor_hours: int = 24 * 365


class FeatureLabelSettings(SettingsBase):
    forward_horizon_hours: int
    min_expected_edge_bps: float
    use_post_cost_target: bool = True


class FeatureOutputSettings(SettingsBase):
    processed_dir: str = "data/processed/features"
    artifact_name: str = "feature_set.parquet"
    manifest_name: str = "feature_manifest.json"
    write_csv: bool = True


class FeatureSettings(SettingsBase):
    input: FeatureInputSettings = Field(default_factory=FeatureInputSettings)
    feature_set: FeatureSetSettings
    labels: FeatureLabelSettings
    output: FeatureOutputSettings


class ModelSplitSettings(SettingsBase):
    train_end: str
    validation_end: str
    test_end: str


class LabelInputSettings(SettingsBase):
    feature_table_path: str = "data/processed/features/binance/btcusdt/1h/btcusdt_feature_set.parquet"
    feature_manifest_path: str | None = "data/processed/features/binance/btcusdt/1h/btcusdt_feature_manifest.json"
    market_dataset_path: str = "data/processed/binance/btcusdt/1h/hourly_market_data.parquet"
    market_manifest_path: str | None = "data/processed/binance/btcusdt/1h/manifest.json"
    provider: str = "binance"
    symbol: str = "BTCUSDT"
    venue: str = "binance"
    frequency: str = "1h"


class LabelTargetSettings(SettingsBase):
    direction: str = "short_perp_long_spot"
    holding_windows_hours: list[int] = Field(default_factory=lambda: [8])
    primary_horizon_hours: int = 8
    execution_delay_bars: int = 1
    execution_price_field: str = "open"
    min_expected_edge_bps: float = 5.0
    positive_return_threshold_bps: float = 0.0
    use_post_cost_target: bool = True


class LabelCostSettings(SettingsBase):
    taker_fee_bps: float = 5.0
    maker_fee_bps: float = 2.0
    slippage_bps: float = 3.0
    gas_cost_usd: float = 2.0
    position_notional_usd: float = 10000.0
    other_friction_bps: float = 0.0
    borrow_cost_bps_per_hour: float = 0.0


class LabelOutputSettings(SettingsBase):
    output_dir: str = "data/processed/supervised"
    artifact_name: str = "supervised_dataset.parquet"
    label_table_name: str = "label_table.parquet"
    manifest_name: str = "supervised_manifest.json"
    write_csv: bool = True
    save_split_files: bool = True


class LabelPipelineSettings(SettingsBase):
    input: LabelInputSettings = Field(default_factory=LabelInputSettings)
    target: LabelTargetSettings = Field(default_factory=LabelTargetSettings)
    costs: LabelCostSettings = Field(default_factory=LabelCostSettings)
    split: ModelSplitSettings
    output: LabelOutputSettings = Field(default_factory=LabelOutputSettings)
    notes: dict[str, Any] = Field(default_factory=dict)


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


class DataQualityReportInputSettings(SettingsBase):
    dataset_path: str = "data/processed/binance/btcusdt/1h/hourly_market_data.parquet"
    manifest_path: str | None = "data/processed/binance/btcusdt/1h/manifest.json"
    provider: str = "binance"
    symbol: str = "BTCUSDT"
    venue: str = "binance"
    frequency: str = "1h"


class DataQualityPlotSettings(SettingsBase):
    figure_format: str = "png"
    dpi: int = 180
    rolling_volatility_window_hours: int = 24
    funding_smoothing_window_hours: int = 24 * 7
    spread_smoothing_window_hours: int = 24
    annualization_factor_hours: int = 24 * 365


class DataQualityReportOutputSettings(SettingsBase):
    output_dir: str = "reports/data_quality"
    write_csv: bool = True
    write_markdown: bool = True
    write_json_summary: bool = True


class DataQualityReportSettings(SettingsBase):
    input: DataQualityReportInputSettings = Field(default_factory=DataQualityReportInputSettings)
    plots: DataQualityPlotSettings = Field(default_factory=DataQualityPlotSettings)
    output: DataQualityReportOutputSettings = Field(default_factory=DataQualityReportOutputSettings)
    notes: dict[str, Any] = Field(default_factory=dict)