# Models and Research Module

## Purpose

Compare simple statistical baselines against sequence models that attempt to predict whether funding-rate dislocations remain exploitable after costs.

## Current Research Assets

- a working canonical hourly market dataset pipeline
- a configurable feature-engineering pipeline under `src/funding_arb/features/`
- a cost-aware label-generation and supervised-dataset pipeline under `src/funding_arb/labels/`
- reproducible feature and label configs under `configs/features/default.yaml` and `configs/labels/default.yaml`
- documented feature definitions in `docs/features.md`
- documented target definitions in `docs/labels.md`

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
- `src/funding_arb/labels/pipeline.py`
- `src/funding_arb/models/baselines.py`
- `src/funding_arb/models/deep_learning.py`

## Caveats

Feature and label pipelines are now implemented, but baseline training, deep-learning training loops, and experiment tracking remain future work.