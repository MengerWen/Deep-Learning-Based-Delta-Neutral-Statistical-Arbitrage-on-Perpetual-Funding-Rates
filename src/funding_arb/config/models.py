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


class BaselineInputSettings(SettingsBase):
    dataset_path: str = "data/processed/supervised/binance/btcusdt/1h/btcusdt_supervised_dataset.parquet"
    manifest_path: str | None = "data/processed/supervised/binance/btcusdt/1h/btcusdt_supervised_manifest.json"
    provider: str = "binance"
    symbol: str = "BTCUSDT"
    venue: str = "binance"
    frequency: str = "1h"


class BaselineTargetSettings(SettingsBase):
    timestamp_column: str = "timestamp"
    split_column: str = "split"
    ready_column: str = "supervised_ready"
    classification_column: str = "target_is_profitable_24h"
    regression_column: str = "target_future_net_return_bps_24h"


class BaselineFeatureSelectionSettings(SettingsBase):
    include_columns: list[str] = Field(default_factory=list)
    exclude_columns: list[str] = Field(
        default_factory=lambda: [
            "timestamp",
            "symbol",
            "venue",
            "frequency",
            "split",
            "feature_ready",
            "supervised_ready",
        ]
    )
    exclude_prefixes: list[str] = Field(default_factory=lambda: ["target_"])
    max_missing_fraction: float = 0.25
    drop_constant_features: bool = True


class RuleBaselineSpec(SettingsBase):
    name: str
    kind: str
    enabled: bool = True
    funding_column: str = "funding_rate_bps"
    funding_threshold_bps: float = 0.0
    spread_column: str = "spread_zscore_72h"
    spread_threshold: float = 0.0
    regime_column: str | None = None
    regime_value: float | int | None = 1


class ClassificationBaselineSettings(SettingsBase):
    enabled: bool = True
    name: str = "logistic_regression"
    estimator: str = "logistic_regression"
    probability_threshold: float = 0.5
    standardize: bool = True
    max_iter: int = 1500
    c: float = 1.0
    class_weight: str | None = "balanced"
    random_state: int = 42


class RegressionBaselineSettings(SettingsBase):
    enabled: bool = True
    name: str = "ridge_regression"
    estimator: str = "ridge"
    standardize: bool = True
    alpha: float = 1.0
    trade_threshold_bps: float = 0.0
    random_state: int = 42


class TreeBaselineSettings(SettingsBase):
    enabled: bool = False
    classifier_name: str = "random_forest_classifier"
    regressor_name: str = "random_forest_regressor"
    n_estimators: int = 200
    max_depth: int | None = 6
    min_samples_leaf: int = 50
    classification_probability_threshold: float = 0.5
    regression_trade_threshold_bps: float = 0.0
    random_state: int = 42


class BaselinePredictiveSettings(SettingsBase):
    classification: ClassificationBaselineSettings = Field(default_factory=ClassificationBaselineSettings)
    regression: RegressionBaselineSettings = Field(default_factory=RegressionBaselineSettings)
    tree: TreeBaselineSettings = Field(default_factory=TreeBaselineSettings)


class BaselineOutputSettings(SettingsBase):
    model_dir: str = "data/artifacts/models/baselines"
    run_name: str = "default"
    write_csv: bool = True
    write_markdown_report: bool = True


class BaselineSettings(SettingsBase):
    input: BaselineInputSettings = Field(default_factory=BaselineInputSettings)
    target: BaselineTargetSettings = Field(default_factory=BaselineTargetSettings)
    feature_selection: BaselineFeatureSelectionSettings = Field(default_factory=BaselineFeatureSelectionSettings)
    rules: list[RuleBaselineSpec] = Field(default_factory=list)
    predictive: BaselinePredictiveSettings = Field(default_factory=BaselinePredictiveSettings)
    output: BaselineOutputSettings = Field(default_factory=BaselineOutputSettings)
    notes: dict[str, Any] = Field(default_factory=dict)


class ModelTrainingSettings(SettingsBase):
    split: ModelSplitSettings | None = None
    batch_size: int | None = None
    epochs: int | None = None
    learning_rate: float | None = None
    seed: int | None = None


class ModelOutputSettings(SettingsBase):
    model_dir: str = "data/artifacts/models"


class DeepLearningTargetSettings(SettingsBase):
    task: str = "regression"
    column: str = "target_future_net_return_bps_24h"
    classification_column: str = "target_is_profitable_24h"
    regression_column: str = "target_future_net_return_bps_24h"
    timestamp_column: str = "timestamp"
    split_column: str = "split"
    ready_column: str = "supervised_ready"
    probability_threshold: float = 0.5
    trade_threshold_bps: float = 0.0


class SequenceSettings(SettingsBase):
    lookback_steps: int = 48
    allow_cross_split_context: bool = True


class DeepLearningModelSettings(SettingsBase):
    name: str = "lstm"
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.1
    bidirectional: bool = False


class DeepLearningTrainingSettings(SettingsBase):
    batch_size: int = 256
    epochs: int = 5
    learning_rate: float = 0.001
    weight_decay: float = 0.00001
    seed: int = 42
    device: str = "auto"
    num_workers: int = 0
    clip_grad_norm: float | None = 1.0
    early_stopping_patience: int = 3
    deterministic: bool = True
    use_balanced_classification_loss: bool = True


class DeepLearningOutputSettings(SettingsBase):
    model_dir: str = "data/artifacts/models/dl"
    run_name: str = "default"
    write_csv: bool = True
    write_markdown_report: bool = True


class DeepLearningSettings(SettingsBase):
    input: BaselineInputSettings = Field(default_factory=BaselineInputSettings)
    target: DeepLearningTargetSettings = Field(default_factory=DeepLearningTargetSettings)
    feature_selection: BaselineFeatureSelectionSettings = Field(default_factory=BaselineFeatureSelectionSettings)
    sequence: SequenceSettings = Field(default_factory=SequenceSettings)
    model: DeepLearningModelSettings = Field(default_factory=DeepLearningModelSettings)
    training: DeepLearningTrainingSettings = Field(default_factory=DeepLearningTrainingSettings)
    output: DeepLearningOutputSettings = Field(default_factory=DeepLearningOutputSettings)
    notes: dict[str, Any] = Field(default_factory=dict)


class SignalInputSettings(SettingsBase):
    baseline_predictions_path: str = "data/artifacts/models/baselines/binance/btcusdt/1h/btcusdt_24h_default/baseline_predictions.parquet"
    baseline_manifest_path: str | None = "data/artifacts/models/baselines/binance/btcusdt/1h/btcusdt_24h_default/baseline_manifest.json"
    dl_predictions_path: str = "data/artifacts/models/dl/binance/btcusdt/1h/lstm_regression_24h_default/dl_predictions.parquet"
    dl_manifest_path: str | None = "data/artifacts/models/dl/binance/btcusdt/1h/lstm_regression_24h_default/dl_manifest.json"
    provider: str = "binance"
    symbol: str = "BTCUSDT"
    venue: str = "binance"
    frequency: str = "1h"


class SignalSourceSettings(SettingsBase):
    name: str = "baseline"
    baseline_mode: str = "all"
    model_names: list[str] = Field(default_factory=list)


class SignalOutputSettings(SettingsBase):
    output_dir: str = "data/artifacts/signals"
    artifact_name: str = "signals.parquet"
    manifest_name: str = "signals_manifest.json"
    write_csv: bool = True


class SignalSettings(SettingsBase):
    input: SignalInputSettings = Field(default_factory=SignalInputSettings)
    source: SignalSourceSettings = Field(default_factory=SignalSourceSettings)
    output: SignalOutputSettings = Field(default_factory=SignalOutputSettings)
    notes: dict[str, Any] = Field(default_factory=dict)


class BacktestInputSettings(SettingsBase):
    signal_path: str = "data/artifacts/signals/binance/btcusdt/1h/baseline/signals.parquet"
    signal_manifest_path: str | None = "data/artifacts/signals/binance/btcusdt/1h/baseline/signals_manifest.json"
    market_dataset_path: str = "data/processed/binance/btcusdt/1h/hourly_market_data.parquet"
    market_manifest_path: str | None = "data/processed/binance/btcusdt/1h/manifest.json"
    provider: str = "binance"
    symbol: str = "BTCUSDT"
    venue: str = "binance"
    frequency: str = "1h"


class BacktestSelectionSettings(SettingsBase):
    strategy_names: list[str] = Field(default_factory=list)
    split_filter: list[str] = Field(default_factory=lambda: ["train", "validation", "test"])
    direction: str = "short_perp_long_spot"
    require_should_trade: bool = True
    min_signal_score: float | None = None
    min_confidence: float | None = None
    min_expected_return_bps: float | None = None


class PortfolioSettings(SettingsBase):
    initial_capital: float
    position_notional: float
    max_open_positions: int = 1


class CostSettings(SettingsBase):
    taker_fee_bps: float
    maker_fee_bps: float
    slippage_bps: float
    gas_cost_usd: float
    other_friction_bps: float = 0.0


class ExecutionSettings(SettingsBase):
    entry_delay_bars: int = 1
    execution_price_field: str = "open"
    holding_window_hours: int = 24
    maximum_holding_hours: int = 48
    funding_interval_hours: int = 8
    rebalance_frequency: str = "1h"
    exit_on_signal_off: bool = True
    stop_loss_bps: float | None = None
    take_profit_bps: float | None = None
    allow_partial_exit: bool = False


class ReportingSettings(SettingsBase):
    output_dir: str = "data/artifacts/backtests"
    run_name: str = "baseline_signals_default"
    write_csv: bool = True
    write_markdown_report: bool = True
    figure_format: str = "png"
    dpi: int = 180
    top_n_strategies_for_plots: int = 5


class BacktestSettings(SettingsBase):
    input: BacktestInputSettings = Field(default_factory=BacktestInputSettings)
    selection: BacktestSelectionSettings = Field(default_factory=BacktestSelectionSettings)
    portfolio: PortfolioSettings
    costs: CostSettings
    execution: ExecutionSettings
    reporting: ReportingSettings = Field(default_factory=ReportingSettings)
    notes: dict[str, Any] = Field(default_factory=dict)


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
