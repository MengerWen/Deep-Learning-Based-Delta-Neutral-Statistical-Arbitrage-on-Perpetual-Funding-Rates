# Vault Contract Prototype

Full implementation-facing specification:

- see [`docs/contracts.md`](../contracts.md)

## Scope

The contract layer is a prototype accounting vault, not a production trading protocol.

## Core Requirements

- mock stablecoin deposits and withdrawals
- share accounting
- owner-controlled NAV/PnL updates
- pause and access control
- clear event emission for demo visibility

## Why Foundry

Foundry is a good fit here because:

- the contract scope is small and Solidity-focused
- local compile/test loops are fast
- the project does not need a large JS-first contract toolchain

## Current Scaffold

- `contracts/src/MockStablecoin.sol`
- `contracts/src/DeltaNeutralVault.sol`
- `contracts/foundry.toml`

## Caveats

The current contract is a prototype starter. It does not claim production security or complete economic realism.
