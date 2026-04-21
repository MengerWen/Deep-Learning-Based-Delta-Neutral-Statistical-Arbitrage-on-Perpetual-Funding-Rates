# FTE 4312 Final Presentation Script

Project: **Deep Learning-Based Delta-Neutral Statistical Arbitrage on Perpetual Funding Rates**

Target duration: **15 minutes**

Presentation page:

```text
http://127.0.0.1:5174/pre/index.html?ppt=1
```

Interactive dashboard, if needed:

```text
http://127.0.0.1:5174/?mode=demo_showcase
```

## Speaker Assignment And Timing

| Speaker | Time | PPT Sections | Main Responsibility |
| --- | ---: | --- | --- |
| Jie Wen | 2:00 | Hero, Executive Outline, Blockchain Scope | Opening, project framing, high-level architecture |
| Qihang Han | 6:30 | Problem, System Boundary, Off-Chain Deep Dive, Off-Chain Intelligence | Motivation, off-chain analytics, modeling, arbitrage evidence |
| Hongrui Pan | 6:30 | On-Chain Deep Dive, Boundary Handoff, Implementation Status, Blockchain Evidence, Live Vault Console, Chain Demo Flow, Caveats, Next Steps | Vault design, chain-facing implementation, live demo, closing |

## Important Presentation Rule

Only discuss the **demo showcase** results in class. Do not compare against the separate real experiment artifacts. Phrase results as "in our demo showcase" or "in this demonstration bundle" when necessary.

## Part 1: Jie Wen - Opening And Overall Framing

### Slide: Title / Hero

**Time: 0:00 - 0:45**

Hello everyone. We are presenting our FTE 4312 course project, **Deep Learning-Based Delta-Neutral Statistical Arbitrage on Perpetual Funding Rates**.

The key idea is to combine two worlds. On one side, we use off-chain quantitative research to analyze perpetual funding-rate opportunities. On the other side, we use an on-chain vault to represent user deposits, share accounting, strategy state, and NAV or PnL synchronization.

So the project is not only a trading model, and it is not only a smart contract. It is a hybrid prototype: **off-chain intelligence, on-chain state machine**.

### Slide: Executive Outline

**Time: 0:45 - 1:25**

Our presentation follows four parts.

First, we explain the project idea: why funding-rate arbitrage creates a natural DeFi strategy problem.

Second, we explain the technical design: what stays off-chain and what moves on-chain.

Third, we show the implementation: the data pipeline, model pipeline, backtest, Solidity vault, scripts, tests, and frontend bridge.

Finally, we demonstrate the system: especially the vault console, where we can operate the vault during the presentation and show state changes on screen.

### Slide: Blockchain Scope

**Time: 1:25 - 2:00**

The most important framing is this: the blockchain contribution is not that we run deep learning on-chain. That would be expensive and unrealistic.

Instead, the blockchain contribution is the vault boundary. The smart contract records pooled capital, internal shares, strategy state, NAV, PnL updates, and event history. The heavy analytics happen off-chain, and the compact result is synchronized to the vault.

I will now pass to Qihang, who will explain the problem and the off-chain strategy pipeline.

## Part 2: Qihang Han - Problem, Architecture Boundary, And Off-Chain Analytics

### Slide: Problem And Motivation

**Time: 2:00 - 3:00**

The motivation starts from perpetual futures. Unlike traditional futures, perpetual contracts do not expire. Exchanges use the funding-rate mechanism to keep the perpetual price close to the spot or index price.

When the market is strongly long, funding can become positive, meaning longs pay shorts. In a simplified delta-neutral trade, we can short the perpetual contract and hedge with a long spot position. The goal is to reduce directional BTC exposure and earn from funding or basis convergence.

But this is not automatically profitable. A high funding rate alone is not enough. We still need to consider basis risk, transaction fees, slippage, holding period, and whether the funding dislocation persists long enough.

That is why this is a good hybrid system problem. The strategy logic requires heavy off-chain research, while pooled capital and accounting benefit from transparent on-chain bookkeeping.

### Slide: System Boundary - What Stays Off-Chain / What Moves On-Chain

**Time: 3:00 - 4:05**

Our system boundary is very deliberate.

The off-chain side handles data-heavy and computation-heavy work. This includes market data processing, feature engineering, label construction, model training, signal generation, backtesting, and report generation.

The on-chain side handles deterministic state. This includes deposits, withdrawals, internal shares, strategy state, role-restricted updates, NAV synchronization, and event logs.

This separation is important because smart contracts cannot natively access exchange data or run complex machine learning models. Instead of forcing everything on-chain, we use a realistic oracle-style architecture: compute off-chain, then publish a small and auditable update on-chain.

### Slide: Off-Chain Deep Dive

**Time: 4:05 - 5:45**

Before the contract is touched, the off-chain pipeline does four things.

First, it builds the research context. The Python pipeline fetches and aligns market data, then creates features such as funding rate, annualized funding, basis spread, z-score, volatility, and short-horizon market indicators.

Second, it builds supervised learning targets. Instead of predicting simple price direction, the label is aligned with the actual strategy objective: whether a potential delta-neutral trade has positive expected value after costs.

Third, it trains and compares models. The demo includes rule-based baselines, simple statistical or machine learning baselines, and deep learning models such as LSTM, GRU, and Transformer-style sequence models.

Fourth, it produces evidence. The output is not just one prediction number. We generate leaderboards, strategy metrics, equity curves, drawdowns, and charts. These artifacts justify whether the strategy view is strong enough to be reflected into the vault.

### Slide: Off-Chain Intelligence

**Time: 5:45 - 7:25**

This slide shows why the vault is not arbitrary. It is supported by off-chain research evidence.

The funding-rate chart shows that the market environment changes over time. Funding can stay calm, spike, reverse, or remain elevated. This matters because strategy timing is central to funding-rate arbitrage.

The spread chart shows the relationship between the perpetual price and spot reference. The basis can widen and mean-revert, which creates potential statistical arbitrage opportunities.

The model comparison chart shows how different signal families behave in the demo. We compare rule-based logic, baseline machine learning, and deep learning. The purpose is not to claim that deep learning is always best, but to show a structured benchmark process.

The equity and drawdown charts are important because we care about post-cost strategy behavior, not just raw prediction accuracy. A signal should be evaluated through trading outcomes, risk, and drawdown.

### Transition To Hongrui

**Time: 7:25 - 8:30**

So the off-chain side creates a strategy view: what model is selected, what direction is suggested, what NAV or PnL update should be reported, and what evidence supports that update.

But the user does not interact directly with a Python notebook. The user interacts with a vault. That vault is the chain-facing part of our system.

Hongrui will now explain what the Solidity layer stores and how the off-chain result becomes on-chain state.

## Part 3: Hongrui Pan - On-Chain Vault, Live Demo, And Closing

### Slide: On-Chain Deep Dive

**Time: 8:30 - 9:30**

The Solidity layer is centered around two contracts.

The first is `MockStablecoin`, which gives us a local demo asset. It lets us demonstrate minting, approval, deposit, and withdrawal flows without depending on a live external token.

The second is `DeltaNeutralVault`, which is the main vault contract. It handles deposits, withdrawals, internal share accounting, strategy-state updates, NAV synchronization, PnL updates, pause control, operator management, and events.

The key point is that the vault is not pretending to execute trades directly on-chain. It is an accounting and state-management layer for a strategy whose intelligence comes from off-chain analytics.

### Slide: Boundary Handoff

**Time: 9:30 - 10:20**

Now the important question is: what exactly crosses from off-chain analytics into on-chain state?

We keep the payload small. The contract does not receive the full dataset, the full model, or the full backtest. It receives only the fields that matter for state:

strategy state, reported NAV, PnL delta, signal hash, metadata hash, and report hash.

The hashes are important because they anchor the on-chain update to off-chain evidence. The vault stores compact state, while the full reasoning remains in generated artifacts and reports.

This design keeps gas costs low, makes the trust boundary explicit, and gives the blockchain a meaningful role without forcing the EVM to do unsuitable computation.

### Slide: Implementation Status

**Time: 10:20 - 11:05**

In terms of implementation, all major demo layers are already built.

The off-chain analytics engine includes data, features, labels, models, signals, backtest, evaluation, reporting, demo, and integration modules.

The contract layer includes the mock stablecoin, the delta-neutral vault, update functions, events, pause logic, ownership mechanics, and operator control.

The automation layer includes local scripts for deployment and vault updates, plus Foundry tests for the core accounting and access-control behavior.

The frontend bridge packages all of this into the presentation page and dashboard.

### Slide: Blockchain Evidence

**Time: 11:05 - 11:45**

This slide answers the question: how do we know the chain side is more than a diagram?

The vault exposes concrete capabilities: deposit and withdraw, owner and operator separation, strategy-state updates, NAV and PnL synchronization, pause control, and event logging.

These capabilities map directly to contract behavior. For example, a user deposit mints shares. A NAV update changes reported assets. A strategy update records the latest strategy state and hashes. Events provide the audit trail.

Now I will use the live vault console to show these state transitions interactively.

### Slide: Live Vault Console

**Time: 11:45 - 13:30**

This is a local presentation simulator of the vault workflow. It follows the same conceptual flow as our Solidity vault and update scripts, but it is stable for classroom demonstration because it does not depend on a wallet or live RPC connection.

First, I click **Deploy local vault**. This represents deploying `MockStablecoin` and `DeltaNeutralVault`. We can see the vault address appears, a transaction hash is generated, and the event stream records `DeployLocal`.

**Click: Deploy local vault**

Next, I click **Deposit 10,000 mUSDC**. This represents the user approving the vault and depositing mock stablecoin. The user wallet decreases, vault cash increases, reported NAV increases, and user shares are minted.

**Click: Deposit 10,000 mUSDC**

Now I click **Sync strategy state**. This represents the operator pushing the selected strategy state into the vault. In this demo, the vault moves from idle to active, and the selected strategy becomes visible in contract-facing state.

**Click: Sync strategy state**

Next, I click **Sync NAV / PnL**. This represents synchronizing the off-chain strategy outcome into the vault. Reported NAV and cumulative PnL update, and a report hash is anchored in the event stream.

**Click: Sync NAV / PnL**

Finally, I click **Withdraw 2,500 mUSDC**. This shows that withdrawals are not just a simple balance subtraction. The vault burns shares, decreases reported NAV, decreases vault cash, and increases the user wallet balance.

**Click: Withdraw 2,500 mUSDC**

The point of this demo is accountability. We can see the user-facing state, vault accounting, transaction-style hashes, and event-style logs all changing step by step.

### Slide: Chain Demo Flow / Vault Demo Story

**Time: 13:30 - 14:15**

This slide summarizes the same flow in system terms.

The local demo starts with contract deployment, then user funding and approval, then deposit, then strategy-state update, then NAV or PnL synchronization, and finally withdrawal.

The vault stores the parts that should be transparent to users: total shares, user shares, reported NAV, strategy state, update timestamps, and hash references to off-chain artifacts.

So the frontend is not just showing a static report. It connects the research output to a contract-facing state machine.

### Slide: Caveats

**Time: 14:15 - 14:40**

There are clear limitations.

This is a course-project prototype, not an audited DeFi protocol. The vault uses a trusted owner or operator path. It does not yet verify decentralized oracle signatures on-chain. Execution remains off-chain, and the contract mirrors strategy state and accounting rather than performing live multi-venue trading.

These limitations are intentional. The goal is to demonstrate a credible hybrid architecture, not to overclaim production readiness.

### Slide: Next Steps / Closing

**Time: 14:40 - 15:00**

To conclude, our project contributes four things.

First, an end-to-end off-chain research pipeline for funding-rate arbitrage. Second, a cost-aware strategy evaluation workflow. Third, a Solidity vault that represents pooled capital, shares, strategy state, NAV, and PnL. Fourth, a frontend demo that connects the research system to the vault interface.

Future work would include signed or oracle-mediated updates, richer vault lifecycle controls, multi-asset support, and a cleaner operator dashboard.

Thank you. We are happy to take questions.

## Backup Short Version If Time Is Running Out

If the team is behind schedule by more than one minute, shorten as follows:

- Jie Wen: keep the opening, skip detailed outline bullets.
- Qihang Han: shorten model explanation to one sentence: "We compare rule-based, baseline ML, and deep-learning signals using post-cost backtesting."
- Hongrui Pan: keep the live vault console, but skip the final withdrawal click if necessary.

## Suggested Q&A Answers

### Why not run the model on-chain?

Because model training and backtesting are data-heavy and iterative. Running them on-chain would be expensive and unrealistic. The smart contract should store compact, auditable state: deposits, shares, NAV, PnL, strategy state, and hashes.

### What makes this a blockchain project rather than only a quant project?

The blockchain layer is the vault accounting boundary. Users deposit into a contract, receive internal shares, and observe strategy-state and NAV updates through role-restricted functions and events.

### Is the live vault console a real mainnet transaction?

No. It is a local presentation simulator for stability during class. It mirrors the implemented Solidity vault workflow: deploy, deposit, update strategy, update NAV, withdraw, and event logging. The actual contracts and Foundry tests are in the `contracts/` workspace.

### What is delta-neutral in this project?

It means the strategy tries to reduce directional BTC exposure by pairing opposite legs, such as short perpetual and long spot. The target is not to bet on BTC price direction, but to capture funding-rate carry or basis convergence after costs.

### What is the most important limitation?

The vault currently trusts an owner or operator to synchronize off-chain results. A more production-ready system would need signed updates, oracle verification, stronger operational controls, and security review.
