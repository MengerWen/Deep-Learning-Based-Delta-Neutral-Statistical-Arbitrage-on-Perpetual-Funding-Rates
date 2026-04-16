# Mock Off-Chain to On-Chain Integration Report

## Selected Strategy Context

- strategy: `spread_zscore_1p5`
- split: `test`
- timestamp: `2026-04-07T00:00:00+00:00`
- should_trade: `False`
- suggested_direction: `flat`
- ranking metric `total_net_pnl_usd`: `-6474.853785395195`

## Planned Vault Update

- strategy_state: `idle` (`0`)
- reported_nav_assets: `93525146215`
- summary_pnl_assets: `-6474853785`
- summary_pnl_usd: `-6474.853785395195`

## Contract Calls

- `updateStrategyState` with calldata `0x9317baf5000000000000000000000000000000000000000000000000000000000000000038e68cbe2305323a89e8bc50205410f49ff81df28f7720606e0c805aeee36f9b3fd845dc21419dd4581260640e149c43ae279f113879b8c82e573d1e59914532`
- `updateNav` with calldata `0x6c3827ba00000000000000000000000000000000000000000000000000000015c6887a67565621192ff6806aeaf85ce3a46eced19ac8f63e3fc178ef2c9e092b815998a7`

## Execution Summary

- mode: dry-run
- rpc_url: http://127.0.0.1:8545
- vault_address: 0x0000000000000000000000000000000000000000
- operator_private_key_env: PRIVATE_KEY

## Prototype Assumptions

- This flow is a trusted operator/oracle-style prototype.
- It reuses local strategy artifacts and converts them into simplified vault updates.
- It is educational and demo-oriented, not a production oracle network.
