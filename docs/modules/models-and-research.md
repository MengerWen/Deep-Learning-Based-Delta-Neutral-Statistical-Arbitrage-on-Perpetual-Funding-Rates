# Models and Research Module

## Purpose

Compare simple statistical baselines against sequence models that attempt to predict whether funding-rate dislocations remain exploitable after costs.

## Current Research Assets

- a working canonical hourly market dataset pipeline
- a configurable feature-engineering pipeline under `src/funding_arb/features/`
- reproducible feature configs under `configs/features/default.yaml`
- documented feature definitions in `docs/features.md`

## Planned Model Layers

- threshold and z-score baselines
- rolling mean-reversion signals
- simple regression or classification baselines
- LSTM sequence models
- optional Transformer-style sequence experiments if time permits

## Research Rules

- benchmark deep models against strong simple baselines
- use time-based train/validation/test splits
- document feature leakage controls
- report post-cost performance, not just raw prediction accuracy

## Current Files

- `src/funding_arb/features/pipeline.py`
- `src/funding_arb/features/builders.py`
- `src/funding_arb/features/transforms.py`
- `src/funding_arb/labels/generator.py`
- `src/funding_arb/models/baselines.py`
- `src/funding_arb/models/deep_learning.py`

## Caveats

The feature pipeline is now implemented, but label generation, baseline training, and experiment tracking are still future work.