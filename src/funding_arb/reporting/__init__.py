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

__all__ = [
    "DataQualityReportArtifacts",
    "compute_correlation_summary",
    "compute_distribution_summary",
    "compute_missingness_summary",
    "compute_time_coverage_summary",
    "describe_data_quality_job",
    "load_market_dataset",
    "prepare_analysis_frame",
    "run_data_quality_report",
]