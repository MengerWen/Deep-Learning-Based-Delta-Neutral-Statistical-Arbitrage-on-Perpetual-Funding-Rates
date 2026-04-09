from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pandas as pd

from funding_arb.config.models import SignalSettings
from funding_arb.signals.adapters import adapt_baseline_predictions, adapt_deep_learning_predictions
from funding_arb.signals.pipeline import run_signal_generation

REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_TMP_ROOT = REPO_ROOT / 'tests' / '.tmp'
TEST_TMP_ROOT.mkdir(parents=True, exist_ok=True)


def _make_temp_dir() -> Path:
    path = TEST_TMP_ROOT / f'signal-tests-{uuid.uuid4().hex}'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _baseline_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'timestamp': pd.date_range('2024-01-01', periods=2, freq='h', tz='UTC'),
            'split': ['train', 'validation'],
            'model_name': ['rule_a', 'logit_a'],
            'model_family': ['rule_based', 'linear'],
            'task': ['classification', 'classification'],
            'signal_direction': ['short_perp_long_spot', 'short_perp_long_spot'],
            'signal': [1, 0],
            'decision_score': [1.5, 0.42],
            'signal_threshold': [1.0, 0.5],
            'signal_strength': [0.5, -0.08],
            'predicted_probability': [None, 0.42],
            'predicted_return_bps': [None, None],
            'predicted_label': [1, 0],
            'actual_label': [1, 0],
            'actual_return_bps': [5.0, -3.0],
        }
    )


def _dl_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'timestamp': pd.date_range('2024-01-02', periods=2, freq='h', tz='UTC'),
            'split': ['validation', 'test'],
            'model_name': ['lstm', 'lstm'],
            'model_family': ['deep_learning', 'deep_learning'],
            'task': ['regression', 'regression'],
            'signal_direction': ['short_perp_long_spot', 'short_perp_long_spot'],
            'signal': [1, 0],
            'decision_score': [3.2, -1.4],
            'signal_threshold': [0.0, 0.0],
            'signal_strength': [3.2, -1.4],
            'predicted_probability': [None, None],
            'predicted_return_bps': [3.2, -1.4],
            'predicted_label': [1, 0],
            'actual_label': [1, 0],
            'actual_return_bps': [2.8, -2.1],
        }
    )


def _settings(tmp_dir: Path, source_name: str) -> SignalSettings:
    baseline_path = tmp_dir / 'baseline.parquet'
    dl_path = tmp_dir / 'dl.parquet'
    _baseline_frame().to_parquet(baseline_path, index=False)
    _dl_frame().to_parquet(dl_path, index=False)
    return SignalSettings.model_validate(
        {
            'input': {
                'baseline_predictions_path': str(baseline_path),
                'dl_predictions_path': str(dl_path),
                'provider': 'binance',
                'symbol': 'BTCUSDT',
                'venue': 'binance',
                'frequency': '1h',
            },
            'source': {
                'name': source_name,
                'baseline_mode': 'all',
                'model_names': [],
            },
            'output': {
                'output_dir': str(tmp_dir / 'signals_out'),
                'artifact_name': 'signals.parquet',
                'manifest_name': 'signals_manifest.json',
                'write_csv': True,
            },
        }
    )


def test_adapt_baseline_predictions_returns_rule_and_ml_subtypes() -> None:
    tmp_dir = _make_temp_dir()
    try:
        settings = _settings(tmp_dir, 'baseline')
        signals = adapt_baseline_predictions(settings)
        assert set(signals['source_subtype'].tolist()) == {'baseline_ml', 'rule_based'}
        assert signals.loc[signals['strategy_name'] == 'rule_a', 'suggested_direction'].iloc[0] == 'short_perp_long_spot'
        assert signals.loc[signals['strategy_name'] == 'logit_a', 'suggested_direction'].iloc[0] == 'flat'
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_adapt_baseline_predictions_can_filter_rules_only() -> None:
    tmp_dir = _make_temp_dir()
    try:
        settings = _settings(tmp_dir, 'rules')
        signals = adapt_baseline_predictions(settings)
        assert signals['strategy_name'].tolist() == ['rule_a']
        assert signals['source_subtype'].tolist() == ['rule_based']
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_adapt_deep_learning_predictions_sets_expected_return_and_deep_learning_subtype() -> None:
    tmp_dir = _make_temp_dir()
    try:
        settings = _settings(tmp_dir, 'dl')
        signals = adapt_deep_learning_predictions(settings)
        assert signals['source_subtype'].tolist() == ['deep_learning', 'deep_learning']
        assert float(signals.loc[signals['should_trade'] == 1, 'expected_return_bps'].iloc[0]) == 3.2
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_run_signal_generation_writes_artifacts_and_manifest() -> None:
    tmp_dir = _make_temp_dir()
    try:
        settings = _settings(tmp_dir, 'dl')
        artifacts = run_signal_generation(settings)
        manifest_path = tmp_dir / 'signals_out' / 'binance' / 'btcusdt' / '1h' / 'dl' / 'signals_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        assert artifacts.signals_path.endswith('signals.parquet')
        assert artifacts.signals_csv_path is not None
        assert manifest['summary']['active_signal_count'] == 1
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
