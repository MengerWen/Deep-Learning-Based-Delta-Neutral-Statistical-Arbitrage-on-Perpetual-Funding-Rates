# Models and Research Module

## Purpose

Compare simple statistical baselines against sequence models that attempt to predict whether funding-rate dislocations remain exploitable after costs.

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

## Future Files

- `src/funding_arb/features/pipeline.py`
- `src/funding_arb/labels/generator.py`
- `src/funding_arb/models/baselines.py`
- `src/funding_arb/models/deep_learning.py`

## Caveats

This scaffold includes config files and placeholder modules only. Model training code and experiment tracking remain future work.

