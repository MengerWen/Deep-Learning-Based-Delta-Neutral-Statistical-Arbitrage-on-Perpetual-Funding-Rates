# Contracts Workspace

This directory contains the Solidity side of the course-project prototype.

## Tooling

The contract workspace uses `Foundry`.

Why Foundry for this project:

- fast local compile/test loop
- Solidity-first workflow
- smaller surface area than a JS-heavy toolchain
- good fit for a compact vault prototype

## Planned Contracts

- `MockStablecoin.sol`
  Local demo asset used for deposit/withdraw flows
- `DeltaNeutralVault.sol`
  Prototype vault for:
  - deposits
  - withdrawals
  - share accounting
  - owner-controlled NAV updates
  - pause controls
  - event logging

## Quickstart

```bash
forge build
```

## Scope Caveat

This contract workspace is a prototype foundation. It is not a production DeFi protocol and should not be treated as audited or deployment-ready.

