"""Reporting utilities for research artifacts and data-quality summaries."""

from funding_arb.reporting.data_quality import (
    DataQualityReportArtifacts,
    compute_correlation_summary,
    compute_distribution_summary,
    compute_missingness_summary,
    compute_time_coverage_summary,
    describe_data_quality_job,
    load_market_dataset,
    prepare_analysis_frame,
    run_data_quality_report,
)
from funding_arb.reporting.robustness import (
    RobustnessReportArtifacts,
    describe_robustness_job,
    run_robustness_report,
)

__all__ = [
    "DataQualityReportArtifacts",
    "RobustnessReportArtifacts",
    "compute_correlation_summary",
    "compute_distribution_summary",
    "compute_missingness_summary",
    "compute_time_coverage_summary",
    "describe_data_quality_job",
    "describe_robustness_job",
    "load_market_dataset",
    "prepare_analysis_frame",
    "run_data_quality_report",
    "run_robustness_report",
]
