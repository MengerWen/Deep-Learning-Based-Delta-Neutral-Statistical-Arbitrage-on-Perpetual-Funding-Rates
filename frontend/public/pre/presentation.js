(function () {
  const snapshotUrl = "/demo_showcase/demo_snapshot.json";
  const exploratoryUrl = "/demo_showcase/exploratory_dl_summary.json";
  const reportSummaryUrl = "/demo_showcase/report/summary.json";

  const chartOrder = [
    "DEMO ONLY | DL test metric comparison",
    "DEMO ONLY | Strict strategy comparison",
    "DEMO ONLY | Family comparison",
    "DEMO ONLY | Strict equity curves",
    "DEMO ONLY | Strict drawdown comparison",
    "DEMO ONLY | Synthetic funding-rate regime map",
    "DEMO ONLY | Synthetic perpetual-vs-spot spread",
  ];

  const CONTRACT_TEST_COUNT = 15;
  const CONTRACT_SCRIPT_COUNT = 2;
  const VAULT_STATE_COUNT = 4;
  const OFFCHAIN_PACKAGE_COUNT = 14;
  const PYTHON_SCRIPT_COUNT = 16;

  const rubricItems = [
    {
      title: "Project idea",
      detail:
        "Frame the project as a blockchain vault problem: how to represent strategy participation, accounting, and updates transparently on-chain.",
    },
    {
      title: "Technical design",
      detail:
        "Show the hybrid architecture: off-chain analytics produce strategy outputs, while a Solidity vault stores the actionable state and accounting.",
    },
    {
      title: "Implementation",
      detail:
        "Walk through the vault contract, role model, update scripts, Foundry tests, and the frontend bridge to the demo snapshot.",
    },
    {
      title: "System demo",
      detail:
        "Use this presentation page first, then move into the interactive dashboard only when you need deeper drill-down.",
      },
  ];

  const problemCards = [
    {
      title: "Pooled strategy capital needs transparent accounting",
      detail:
        "Even if the strategy logic is off-chain, user deposits, share balances, NAV, and withdrawals benefit from deterministic on-chain bookkeeping.",
    },
    {
      title: "Smart contracts cannot natively see market data or ML outputs",
      detail:
        "This creates the oracle-style boundary in our system: signals and reports are computed off-chain, then synchronized to the vault through an explicit updater path.",
    },
    {
      title: "Role separation matters for safety and operability",
      detail:
        "The vault must distinguish owner privileges, operator privileges, and user actions, rather than treating every state change like a single admin shortcut.",
    },
    {
      title: "A blockchain course project should demonstrate more than charts",
      detail:
        "The most defensible demo is an end-to-end flow where research outputs become explicit contract updates, events, and user-facing state.",
    },
  ];

  const implementationBlueprint = [
    {
      title: "MockStablecoin asset layer",
      detail:
        "A simple mock stablecoin lets us demonstrate minting, approval, deposit, and withdrawal flows without depending on an external live token.",
      metric: (snapshot) => `${snapshot.simulation.asset_symbol} | ${snapshot.simulation.asset_decimals} decimals`,
    },
    {
      title: "DeltaNeutralVault core contract",
      detail:
        "The Solidity vault handles deposits, withdrawals, internal share accounting, strategy-state updates, NAV sync, PnL sync, pause controls, and event emission.",
      metric: () => `${VAULT_STATE_COUNT} strategy states`,
    },
    {
      title: "Foundry scripts",
      detail:
        "Local scripts deploy the mock stablecoin plus vault, then apply explicit strategy-state, NAV, and PnL updates through readable environment toggles.",
      metric: () => `${CONTRACT_SCRIPT_COUNT} local scripts`,
    },
    {
      title: "Foundry tests",
      detail:
        "The contract is validated locally for share pricing, withdrawals, pause behavior, role restrictions, NAV and PnL updates, and ownership transfer.",
      metric: () => `${CONTRACT_TEST_COUNT} test cases`,
    },
  ];

  const chainStoryPoints = [
    "The blockchain contribution is the vault accounting boundary, not on-chain execution of the whole strategy.",
    "Off-chain model outputs are packaged into explicit strategy-state, NAV, and PnL updates rather than hidden inside the frontend.",
    "Owner and operator roles are separated so the demo can talk about governance and operational trust assumptions.",
    "Foundry scripts and tests make the chain-facing workflow reproducible for local demonstration.",
  ];

  const offchainBoundaryItems = [
    {
      label: "Market data and feature pipeline",
      detail:
        "Historical market data fetching, canonicalization, feature engineering, and label construction are all implemented in Python modules and scripts.",
    },
    {
      label: "Model training and ranking",
      detail:
        "Baseline models, deep-learning comparisons, signal generation, and backtests stay off-chain because they are data-heavy and iterative.",
    },
    {
      label: "Research artifacts and reporting",
      detail:
        "Trade logs, equity curves, robustness tables, charts, and presentation assets are generated before any contract update is attempted.",
    },
    {
      label: "Update packaging for the vault",
      detail:
        "Off-chain outputs are compressed into a small update payload: strategy state, NAV/PnL numbers, and signal/metadata/report hashes.",
    },
  ];

  const onchainBoundaryItems = [
    {
      label: "User funds and shares",
      detail:
        "The vault receives deposits and withdrawals and maps them to internal non-transferable shares rather than a simple balance log.",
    },
    {
      label: "Role-restricted updates",
      detail:
        "Only the owner or operator can update strategy state, NAV, and PnL, which makes the trust boundary explicit.",
    },
    {
      label: "Persistent strategy state",
      detail:
        "The contract stores strategy state, reported NAV, cumulative PnL, timestamps, and last signal/metadata/report hashes.",
    },
    {
      label: "Safety and governance controls",
      detail:
        "Pause control, operator management, and two-step ownership transfer make the on-chain layer look like a real vault prototype rather than a static mock.",
    },
  ];

  const offchainLifecycleRows = [
    {
      title: "1. Build research context",
      detail:
        "Python modules fetch market data, align timestamps, engineer features and labels, and define the candidate strategy universe.",
    },
    {
      title: "2. Train and compare models",
      detail:
        "Model ranking, signal generation, and strategy evaluation happen off-chain because they require iteration over large datasets and repeated experiments.",
    },
    {
      title: "3. Produce evidence",
      detail:
        "Leaderboards, trade logs, equity curves, robustness tables, and charts are generated before any state is synchronized to the vault.",
    },
    {
      title: "4. Reduce to a compact payload",
      detail:
        "The off-chain side compresses a rich research result into a small update package that a contract can actually store: state, NAV/PnL, and hashes.",
    },
  ];

  const offchainArtifactRows = [
    {
      title: "Python package surface",
      detail:
        "The repository already has dedicated packages for data, features, labels, models, signals, backtest, evaluation, integration, and reporting.",
      metric: `${OFFCHAIN_PACKAGE_COUNT} package areas`,
    },
    {
      title: "Workflow scripts",
      detail:
        "Runnable scripts already cover fetching market data, building features and labels, training models, generating signals, running backtests, and exporting demos.",
      metric: `${PYTHON_SCRIPT_COUNT} scripts`,
    },
    {
      title: "Outputs handed to the chain side",
      detail:
        "The chain side does not receive the full dataset; it receives distilled state and hashes derived from these off-chain artifacts.",
      metric: "state + NAV/PnL + hashes",
    },
  ];

  const onchainFunctionRows = [
    {
      title: "User-facing functions",
      detail:
        "<code>deposit</code> and <code>withdraw</code> turn asset movements into internal shares and back into assets under reported NAV constraints.",
    },
    {
      title: "Updater-facing functions",
      detail:
        "<code>updateStrategyState</code>, <code>updateNav</code>, and <code>updatePnl</code> move off-chain strategy and valuation information into contract state.",
    },
    {
      title: "Admin safety functions",
      detail:
        "<code>setOperator</code>, <code>pause</code>, <code>unpause</code>, <code>transferOwnership</code>, and <code>acceptOwnership</code> handle governance and emergencies.",
    },
    {
      title: "Events and audit trail",
      detail:
        "Deposits, withdrawals, strategy-state updates, NAV updates, PnL updates, and operator changes are all emitted as events for traceability.",
    },
  ];

  const onchainStateRows = [
    {
      title: "Economic state",
      detail:
        "The vault persists <code>totalShares</code>, per-user <code>shareBalance</code>, and <code>reportedNavAssets</code> as the accounting backbone.",
      metric: "shares + NAV",
    },
    {
      title: "Strategy state",
      detail:
        "The contract stores <code>StrategyState</code> with enum values <code>Idle</code>, <code>Active</code>, <code>Emergency</code>, and <code>Settled</code>.",
      metric: `${VAULT_STATE_COUNT} enum states`,
    },
    {
      title: "Update traceability",
      detail:
        "The latest signal, metadata, and report hashes plus update timestamps are stored to anchor where the on-chain state came from.",
      metric: "hashes + timestamps",
    },
    {
      title: "Access and pause state",
      detail:
        "The vault keeps owner, pending owner, operator, and paused state so operational control is visible and enforceable on-chain.",
      metric: "owner/operator/pause",
    },
  ];

  const handoffFieldRows = [
    {
      title: "Strategy state",
      detail:
        "A compact enum indicating whether the strategy is idle, active, emergency, or settled.",
      code: "updateStrategyState(StrategyState, signalHash, metadataHash)",
    },
    {
      title: "Reported NAV",
      detail:
        "A scalar valuation number that mirrors the off-chain view of vault assets without pushing the full valuation model on-chain.",
      code: "updateNav(newReportedNavAssets, reportHash)",
    },
    {
      title: "PnL delta",
      detail:
        "A signed delta that adjusts reported NAV and cumulative PnL without replaying the full backtest path inside the contract.",
      code: "updatePnl(pnlDeltaAssets, reportHash)",
    },
    {
      title: "Signal / metadata / report hashes",
      detail:
        "Hashes act as lightweight anchors to richer off-chain artifacts and make the boundary explicit instead of hiding provenance in the UI.",
      code: "bytes32 signalHash / metadataHash / reportHash",
    },
  ];

  const handoffSequenceRows = [
    {
      title: "Research output selected",
      detail: "The off-chain engine picks a strategy state and valuation update worth synchronizing.",
    },
    {
      title: "Updater script configured",
      detail: "Environment variables specify whether to update strategy state, NAV, PnL, or a combination of them.",
    },
    {
      title: "Contract call broadcast",
      detail: "Foundry broadcasts only the small set of parameters the vault actually needs to persist.",
    },
    {
      title: "New on-chain state visible",
      detail: "Users and the frontend can read the updated vault state without re-running the off-chain research pipeline.",
    },
  ];

  const handoffWhyRows = [
    "This boundary keeps gas costs and contract complexity small.",
    "It makes trust assumptions visible: the updater path is explicit and role-restricted.",
    "It avoids pretending that model training or backtesting belongs on-chain.",
    "It still gives the vault a real blockchain role: funds, shares, state, and event history live on-chain.",
  ];

  const implementationExtentRows = [
    {
      title: "Off-chain analytics engine",
      status: "implemented",
      detail:
        "Python package areas already cover data, features, labels, models, signals, backtest, evaluation, reporting, demo, and integration.",
      metric: `${OFFCHAIN_PACKAGE_COUNT} package areas`,
    },
    {
      title: "Vault contract layer",
      status: "implemented",
      detail:
        "The Solidity side already includes the mock asset, vault contract, update paths, events, pause logic, and ownership mechanics.",
      metric: "2 contracts",
    },
    {
      title: "Automation and validation",
      status: "implemented",
      detail:
        "Local scripts deploy and update the vault, while Foundry tests validate the most important accounting and access-control behavior.",
      metric: `${CONTRACT_SCRIPT_COUNT} scripts + ${CONTRACT_TEST_COUNT} tests`,
    },
    {
      title: "Frontend bridge",
      status: "prototype",
      detail:
        "The dashboard and presentation page already surface prepared contract-call context, but the operator experience is still demo-oriented.",
      metric: "demo-ready",
    },
    {
      title: "Production-grade infra",
      status: "future",
      detail:
        "Oracle verification, automated relayers, multi-asset support, audited deployment, and live exchange execution are intentionally not finished.",
      metric: "out of scope",
    },
  ];

  const offchainImplementationRows = [
    {
      title: "Data + preprocessing",
      detail:
        "Implemented under <code>src/funding_arb/data</code>, <code>features</code>, and <code>labels</code> with runnable scripts for fetching data and building pipeline inputs.",
      metric: `${PYTHON_SCRIPT_COUNT} Python workflow scripts`,
    },
    {
      title: "Modeling + signal generation",
      detail:
        "Implemented under <code>models</code> and <code>signals</code>; includes baseline training, DL comparison, and standardized signal export.",
      metric: "baseline + DL + signals",
    },
    {
      title: "Backtest + evaluation",
      detail:
        "Implemented under <code>backtest</code> and <code>evaluation</code>; produces leaderboards, trade logs, equity curves, and robustness outputs.",
      metric: "cost-aware metrics",
    },
    {
      title: "Reporting + demo export",
      detail:
        "Implemented under <code>reporting</code>, <code>demo</code>, and <code>demo_showcase</code>; exports the frontend-ready JSON plus chart assets you are presenting now.",
      metric: "dashboard + pre page",
    },
  ];

  const onchainImplementationRows = [
    {
      title: "MockStablecoin.sol",
      detail:
        "Implemented mint, approve, transfer, and transferFrom so the local demo can walk through approval and vault deposit without external token dependencies.",
      metric: "asset simulation ready",
    },
    {
      title: "DeltaNeutralVault.sol",
      detail:
        "Implemented deposit, withdraw, share math, state updates, NAV/PnL sync, pause control, operator management, and two-step ownership transfer.",
      metric: `${VAULT_STATE_COUNT} strategy states`,
    },
    {
      title: "Foundry scripts",
      detail:
        "Implemented <code>DeployLocal.s.sol</code> and <code>UpdateVaultState.s.sol</code> to make the chain demo runnable from deployment to updater flow.",
      metric: `${CONTRACT_SCRIPT_COUNT} scripts`,
    },
    {
      title: "Foundry tests",
      detail:
        "Implemented tests for constructor state, deposit, withdraw, pause, operator permissions, NAV/PnL updates, and ownership transfer.",
      metric: `${CONTRACT_TEST_COUNT} tests`,
    },
  ];

  const contractCapabilityRows = [
    {
      capability: "Deposit / Withdraw",
      purpose: "Let users enter and exit the vault against internal shares.",
      evidence: "Validated via <code>Deposit/Withdraw</code> events. Uses <code>_ceilDiv</code> math to protect share price against rounding exploits.",
    },
    {
      capability: "Owner / Operator split",
      purpose: "Separate governance authority from routine update authority.",
      evidence: "Enforced by <code>onlyOwnerOrOperator</code> modifier, utilizing <code>Ownable2StepLite</code> for secure governance handoff.",
    },
    {
      capability: "Strategy-state updates",
      purpose: "Record whether the system is Idle, Active, Emergency, or Settled.",
      evidence: "Anchors off-chain intent by emitting <code>StrategyStateUpdated</code> with explicit <code>bytes32</code> signal and metadata hashes.",
    },
    {
      capability: "NAV / PnL synchronization",
      purpose: "Mirror off-chain valuation and strategy outcome into contract state.",
      evidence: "Mirrors valuation on-chain by emitting <code>NavUpdated</code>, permanently anchoring the backtest <code>reportHash</code>.",
    },
    {
      capability: "Pause + ownership transfer",
      purpose: "Provide emergency controls and cleaner admin handoff.",
      evidence: "Uses <code>whenNotPaused</code> modifier to halt user flows during emergencies, protecting the vault from extreme basis dislocations.",
    },
  ];

  const assurancePoints = [
    {
      title: "Contract tests",
      value: `${CONTRACT_TEST_COUNT}`,
      note: "Foundry tests cover share accounting, pause controls, update authorization, and ownership flow.",
    },
    {
      title: "Prepared calls",
      value: null,
      note: "The frontend demo bundle already includes a prepared contract-call summary for vault updates.",
    },
    {
      title: "Hash-anchored fields",
      value: "3",
      note: "Signal, metadata, and report hashes help explain how off-chain evidence is referenced on-chain.",
    },
    {
      title: "Role model",
      value: "owner + operator",
      note: "The demo can discuss governance trust assumptions instead of pretending everything is trustless.",
    },
  ];

  const demoFlowSteps = [
    {
      label: "1. Deploy local demo contracts",
      detail:
        "Use `DeployLocal.s.sol` to deploy `MockStablecoin` and `DeltaNeutralVault` into a local/test network environment.",
    },
    {
      label: "2. Fund and approve",
      detail:
        "Mint `mUSDC` to demo users, approve the vault, and show how assets become shares through the deposit function.",
    },
    {
      label: "3. Activate strategy state",
      detail:
        "Call `updateStrategyState` as owner/operator and explain the strategy-state enum plus signal and metadata hashes.",
    },
    {
      label: "4. Sync NAV or PnL",
      detail:
        "Run `UpdateVaultState.s.sol` with explicit toggles for `UPDATE_NAV` and `UPDATE_PNL`, together with a report hash.",
    },
    {
      label: "5. Withdraw and inspect accounting",
      detail:
        "Show how withdrawals depend on shares, reported NAV, and actual token liquidity instead of a naive balance subtraction.",
    },
  ];

  const chainContributions = [
    "A readable Solidity vault that models deposit, withdrawal, internal share accounting, and strategy state for a quant strategy prototype.",
    "A role-based bridge from off-chain signals to on-chain state using owner/operator updates plus signal, metadata, and report hashes.",
    "A lightweight local blockchain workflow built with Foundry scripts and tests rather than a purely static DeFi mockup.",
    "A frontend demo that connects research outputs and contract-facing state so the system can be presented end to end.",
  ];

  const chainLimitations = [
    "The vault relies on a trusted owner/operator path; it does not yet verify oracle data or signatures on-chain.",
    "Execution remains off-chain, so the contract mirrors strategy state and accounting rather than performing live multi-venue trading.",
    "The demo uses a single mock stablecoin and a simplified local/testnet flow rather than production-grade token, oracle, and fee infrastructure.",
    "This is a course-project prototype and not an audited DeFi system.",
  ];

  const chainFutureWork = [
    "Add signed or oracle-mediated update verification so NAV and signal updates are less trust-heavy.",
    "Introduce fee accounting, withdrawal queue logic, and richer role controls for a more realistic vault lifecycle.",
    "Extend from a single mock asset to multi-asset collateral and more realistic on-chain accounting around execution costs.",
    "Connect local update scripts to a cleaner operator dashboard for repeatable demo and governance workflows.",
  ];

  const authorDisplayNameMap = {
    Wenjie: "Jie Wen",
  };

  async function readJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.status}`);
    }
    return response.json();
  }

  function cleanPresentationText(value) {
    if (typeof value !== "string") {
      return value;
    }
    return value
      .replace(/DEMO ONLY\s*[:|]\s*/gi, "")
      .replace(/\bdemo_showcase\b/gi, "presentation")
      .replace(/\s{2,}/g, " ")
      .trim();
  }

  function toPublicAssetUrl(path) {
    if (!path) {
      return "";
    }
    return path.startsWith("/") ? path : `/${path}`;
  }

  function formatNumber(value, digits = 2) {
    if (value == null || Number.isNaN(Number(value))) {
      return "n/a";
    }
    return new Intl.NumberFormat("en-US", {
      maximumFractionDigits: digits,
    }).format(Number(value));
  }

  function formatPercent(value, digits = 2) {
    if (value == null || Number.isNaN(Number(value))) {
      return "n/a";
    }
    return `${(Number(value) * 100).toFixed(digits)}%`;
  }

  function formatUsd(value) {
    if (value == null || Number.isNaN(Number(value))) {
      return "n/a";
    }
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(Number(value));
  }

  function formatDate(value) {
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "2-digit",
    }).format(new Date(value));
  }

  function formatDateTime(value) {
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  }

  function setList(elementId, items) {
    const node = document.getElementById(elementId);
    if (!node) {
      return;
    }
    node.innerHTML = "";
    items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      node.appendChild(li);
    });
  }

  function createDetailRow(label, value) {
    return `<div class="detail-row"><span>${label}</span><span>${value}</span></div>`;
  }

  function createSummaryBadge(label, value) {
    return `<div class="summary-badge"><span>${label}</span><strong>${value}</strong></div>`;
  }

  function renderHero(snapshot, exploratory, reportSummary) {
    const teamNode = document.getElementById("team-row");
    const verdictNode = document.getElementById("hero-verdict");
    const metricsNode = document.getElementById("hero-metrics");
    const artifactNode = document.getElementById("artifact-pill");
    if (!teamNode || !verdictNode || !metricsNode || !artifactNode) {
      return;
    }

    const best = snapshot.backtest.best_strategy;
    const exploratoryBest = exploratory.exploratory_summary?.best_showcase_row;

    teamNode.innerHTML = (reportSummary.meta.authors || [])
      .map(
        (author, index) => `
          <div class="team-chip">
            <span>Member ${index + 1}</span>
            <strong>${authorDisplayNameMap[author] || author}</strong>
          </div>
        `,
      )
      .join("");

    verdictNode.textContent = cleanPresentationText(reportSummary.verdict);
    metricsNode.innerHTML = [
      createSummaryBadge("Off-chain package areas", `${OFFCHAIN_PACKAGE_COUNT}`),
      createSummaryBadge("Python scripts", `${PYTHON_SCRIPT_COUNT}`),
      createSummaryBadge("Prepared contract calls", formatNumber(snapshot.vault.call_count, 0)),
      createSummaryBadge("Contract tests", `${CONTRACT_TEST_COUNT}`),
    ].join("");
    artifactNode.textContent =
      "Presentation-ready blockchain showcase with contract workflow, research evidence, and live demo links.";
  }

  function renderRubricAndScope(snapshot, reportSummary) {
    const rubricNode = document.getElementById("rubric-grid");
    const scopeNode = document.getElementById("scope-details");
    if (rubricNode) {
      rubricNode.innerHTML = rubricItems
        .map(
          (item, index) => `
            <article class="rubric-item">
              <p class="rubric-index">Section ${index + 1}</p>
              <strong>${item.title}</strong>
              <p>${item.detail}</p>
            </article>
          `,
        )
        .join("");
    }

    if (scopeNode) {
      scopeNode.innerHTML = [
        createDetailRow("Vault asset", snapshot.simulation.asset_symbol),
        createDetailRow("Asset decimals", `${snapshot.simulation.asset_decimals}`),
        createDetailRow("Chain label", snapshot.vault.chain_name),
        createDetailRow("Role model", "owner + operator"),
        createDetailRow("Generated", formatDateTime(snapshot.meta.generated_at)),
      ].join("");
    }

    setList("story-points", chainStoryPoints);
  }

  function renderProblemCards() {
    const node = document.getElementById("problem-grid");
    if (!node) {
      return;
    }
    node.innerHTML = problemCards
      .map(
        (item) => `
          <article class="problem-card">
            <p class="section-kicker">Challenge</p>
            <strong>${item.title}</strong>
            <p>${item.detail}</p>
          </article>
        `,
      )
      .join("");
  }

  function renderBoundaries() {
    const offchainNode = document.getElementById("offchain-boundary");
    const onchainNode = document.getElementById("onchain-boundary");
    if (offchainNode) {
      offchainNode.innerHTML = offchainBoundaryItems
        .map(
          (item) => `
            <article class="responsibility-card">
              <p class="section-kicker">Off-chain</p>
              <strong>${item.label}</strong>
              <p>${item.detail}</p>
            </article>
          `,
        )
        .join("");
    }
    if (onchainNode) {
      onchainNode.innerHTML = onchainBoundaryItems
        .map(
          (item) => `
            <article class="responsibility-card">
              <p class="section-kicker">On-chain</p>
              <strong>${item.label}</strong>
              <p>${item.detail}</p>
            </article>
          `,
        )
        .join("");
    }
  }

  function createStatusBadge(status) {
    const labelMap = {
      implemented: "Implemented",
      prototype: "Prototype",
      future: "Future",
    };
    return `<span class="status-badge ${status}">${labelMap[status] || status}</span>`;
  }

  function renderImplementationStatus() {
    const extentNode = document.getElementById("implementation-extent");
    const offchainNode = document.getElementById("implementation-offchain");
    const onchainNode = document.getElementById("implementation-onchain");
    if (!extentNode || !offchainNode || !onchainNode) {
      return;
    }

    extentNode.innerHTML = `
      <p class="section-kicker">Implementation extent</p>
      <h3>Current project boundary</h3>
      <div class="implementation-list">
        ${implementationExtentRows
          .map(
            (item) => `
              <article class="status-row">
                <div class="status-topline">
                  <strong>${item.title}</strong>
                  ${createStatusBadge(item.status)}
                </div>
                <p>${item.detail}</p>
                <div class="status-metric">${item.metric}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    `;

    offchainNode.innerHTML = `
      <p class="section-kicker">Off-chain implementation</p>
      <h3>What is already built outside the chain</h3>
      <div class="implementation-list">
        ${offchainImplementationRows
          .map(
            (item) => `
              <article class="status-row">
                <strong>${item.title}</strong>
                <p>${item.detail}</p>
                <div class="status-metric">${item.metric}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    `;

    onchainNode.innerHTML = `
      <p class="section-kicker">On-chain implementation</p>
      <h3>What is already built on the Solidity side</h3>
      <div class="implementation-list">
        ${onchainImplementationRows
          .map(
            (item) => `
              <article class="status-row">
                <strong>${item.title}</strong>
                <p>${item.detail}</p>
                <div class="status-metric">${item.metric}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderDeepDivePages() {
    const offchainLifecycleNode = document.getElementById("offchain-lifecycle");
    const offchainArtifactsNode = document.getElementById("offchain-artifacts");
    const onchainFunctionsNode = document.getElementById("onchain-functions");
    const onchainStateNode = document.getElementById("onchain-state");
    const handoffFieldsNode = document.getElementById("handoff-fields");
    const handoffSequenceNode = document.getElementById("handoff-sequence");
    const handoffWhyNode = document.getElementById("handoff-why");

    if (offchainLifecycleNode) {
      offchainLifecycleNode.innerHTML = `
        <p class="section-kicker">Off-chain workflow</p>
        <h3>Lifecycle before a contract update</h3>
        <div class="lifecycle-list">
          ${offchainLifecycleRows
            .map(
              (item) => `
                <article class="lifecycle-card">
                  <strong>${item.title}</strong>
                  <p>${item.detail}</p>
                </article>
              `,
            )
            .join("")}
        </div>
      `;
    }

    if (offchainArtifactsNode) {
      offchainArtifactsNode.innerHTML = `
        <p class="section-kicker">Off-chain implementation</p>
        <h3>Implemented off-chain surfaces</h3>
        <div class="implementation-list">
          ${offchainArtifactRows
            .map(
              (item) => `
                <article class="status-row">
                  <strong>${item.title}</strong>
                  <p>${item.detail}</p>
                  <div class="status-metric">${item.metric}</div>
                </article>
              `,
            )
            .join("")}
        </div>
      `;
    }

    if (onchainFunctionsNode) {
      onchainFunctionsNode.innerHTML = `
        <p class="section-kicker">On-chain mechanics</p>
        <h3>Functions exposed by the vault</h3>
        <div class="lifecycle-list">
          ${onchainFunctionRows
            .map(
              (item) => `
                <article class="lifecycle-card">
                  <strong>${item.title}</strong>
                  <p>${item.detail}</p>
                </article>
              `,
            )
            .join("")}
        </div>
      `;
    }

    if (onchainStateNode) {
      onchainStateNode.innerHTML = `
        <p class="section-kicker">On-chain state</p>
        <h3>What is actually persisted in storage</h3>
        <div class="implementation-list">
          ${onchainStateRows
            .map(
              (item) => `
                <article class="status-row">
                  <strong>${item.title}</strong>
                  <p>${item.detail}</p>
                  <div class="status-metric">${item.metric}</div>
                </article>
              `,
            )
            .join("")}
        </div>
      `;
    }

    if (handoffFieldsNode) {
      handoffFieldsNode.innerHTML = `
        <p class="section-kicker">Payload fields</p>
        <h3>Exact things that cross the boundary</h3>
        <div class="payload-list">
          ${handoffFieldRows
            .map(
              (item) => `
                <article class="payload-card">
                  <strong>${item.title}</strong>
                  <p>${item.detail}</p>
                  <div class="status-metric"><code>${item.code}</code></div>
                </article>
              `,
            )
            .join("")}
        </div>
      `;
    }

    if (handoffSequenceNode) {
      handoffSequenceNode.innerHTML = `
        <p class="section-kicker">Boundary sequence</p>
        <h3>How the handoff works in practice</h3>
        <div class="lifecycle-list">
          ${handoffSequenceRows
            .map(
              (item) => `
                <article class="lifecycle-card">
                  <strong>${item.title}</strong>
                  <p>${item.detail}</p>
                </article>
              `,
            )
            .join("")}
        </div>
      `;
    }

    if (handoffWhyNode) {
      handoffWhyNode.innerHTML = `
        <p class="section-kicker">Why this split</p>
        <h3>Why we do not push everything on-chain</h3>
        <ul class="bullet-list">
          ${handoffWhyRows.map((item) => `<li>${item}</li>`).join("")}
        </ul>
      `;
    }
  }

  function renderResults(snapshot, exploratory, reportSummary) {
    const resultsNode = document.getElementById("results-highlight");
    const leaderboardNode = document.getElementById("leaderboard-panel");
    const robustnessNode = document.getElementById("robustness-panel");
    if (!resultsNode || !leaderboardNode || !robustnessNode) {
      return;
    }

    const best = snapshot.backtest.best_strategy;
    const robustness = reportSummary.robustness;

    resultsNode.innerHTML = `
      <p class="section-kicker">Blockchain-centered takeaway</p>
      <h3>The vault is the core system artifact</h3>
      <p class="panel-text">
        The research pipeline still matters, but the blockchain value of this project is the contract
        layer that turns off-chain output into explicit deposits, shares, state transitions, and NAV or
        PnL updates.
      </p>
      <div class="micro-grid">
        <article class="micro-card">
          <p class="metric-label">Strategy state</p>
          <strong>${snapshot.vault.strategy_state}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Reported NAV</p>
          <strong>${formatNumber(snapshot.vault.reported_nav_assets, 0)}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Prepared calls</p>
          <strong>${formatNumber(snapshot.vault.call_count, 0)}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Strict return</p>
          <strong>${formatPercent(best.cumulative_return)}</strong>
        </article>
      </div>
      <ul class="story-list">
        <li>The chain-facing demo is about accountability and update flow, not pretending the whole strategy is fully on-chain.</li>
        <li>Owner/operator updates, pause controls, and explicit share accounting are the most important blockchain mechanisms to highlight.</li>
        <li>The strategy metrics remain supporting evidence that the off-chain engine is meaningful enough to justify a vault layer.</li>
      </ul>
      <div class="subsection">
        <h3>Research support in one line</h3>
        <div class="detail-stack">
          ${createDetailRow("Best strict model", best.display_name)}
          ${createDetailRow("Strict Sharpe", formatNumber(best.sharpe_ratio, 3))}
          ${createDetailRow("Strict net PnL", formatUsd(best.total_net_pnl_usd))}
        </div>
      </div>
    `;

    leaderboardNode.innerHTML = `
      <p class="section-kicker">Contract capabilities</p>
      <h3>What the Solidity layer actually implements</h3>
      <div class="table-shell">
        <table>
          <thead>
            <tr>
              <th>Capability</th>
              <th>Purpose</th>
              <th>Evidence</th>
            </tr>
          </thead>
          <tbody>
            ${contractCapabilityRows
              .map(
                (row) => `
                  <tr>
                    <td>${row.capability}</td>
                    <td>${row.purpose}</td>
                    <td>${row.evidence}</td>
                  </tr>
                `,
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;

    robustnessNode.innerHTML = `
      <p class="section-kicker">Validation and assurance</p>
      <h3>Why the chain-facing demo is credible</h3>
      <div class="micro-grid">
        ${assurancePoints
          .map(
            (item) => `
              <article class="micro-card">
                <p class="metric-label">${item.title}</p>
                <strong>${item.value ?? formatNumber(snapshot.vault.call_count, 0)}</strong>
                <p>${item.note}</p>
              </article>
            `,
          )
          .join("")}
      </div>
      <div class="family-list">
        ${(robustness.family_comparison || [])
          .map(
            (item) => `
              <div class="family-item">
                <div>
                  <strong>${item.family_label}</strong>
                  <span>${item.strategy_label}</span>
                </div>
                <div>
                  <strong>${formatPercent(item.cumulative_return)}</strong>
                  <span>supporting research context</span>
                </div>
              </div>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderCharts(snapshot) {
    const node = document.getElementById("chart-grid");
    if (!node) {
      return;
    }

    // Keep figures uncropped and ordered for live presentation flow.
    const chartRank = new Map(chartOrder.map((title, index) => [title, index]));
    const charts = [...snapshot.charts]
      .sort((left, right) => (chartRank.get(left.title) ?? 99) - (chartRank.get(right.title) ?? 99))
      .slice(0, 4);

    node.innerHTML = charts
      .map((chart) => {
        const assetUrl = toPublicAssetUrl(chart.image);
        return `
          <article class="panel chart-card">
            <a class="chart-media" href="${assetUrl}" target="_blank" rel="noreferrer">
              <img src="${assetUrl}" alt="${chart.title}" />
            </a>
            <div class="chart-copy">
              <p class="chart-tag">${chart.section}</p>
              <h3>${cleanPresentationText(chart.title)}</h3>
              <p>${cleanPresentationText(chart.subtitle)}</p>
              <a class="chart-open" href="${assetUrl}" target="_blank" rel="noreferrer">
                Open full-size chart
              </a>
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderDemoAndVault(snapshot) {
    const timelineNode = document.getElementById("activity-timeline");
    const vaultNode = document.getElementById("vault-summary");
    const vaultCalloutNode = document.getElementById("vault-callout");
    if (!timelineNode || !vaultNode || !vaultCalloutNode) {
      return;
    }

    timelineNode.innerHTML = demoFlowSteps
      .map(
        (item) => `
          <article class="timeline-item">
            <div class="timeline-time">${item.label}</div>
            <div>
              <strong>${item.label}</strong>
              <p>${item.detail}</p>
            </div>
          </article>
        `,
      )
      .join("");

    const decimals = snapshot.simulation.asset_decimals || 6;
    const realNav = snapshot.vault.reported_nav_assets / Math.pow(10, decimals);
    vaultNode.innerHTML = [
      createDetailRow("Chain label", snapshot.vault.chain_name),
      createDetailRow("Vault Contract", "<code style='color:var(--teal)'>DeltaNeutralVault.sol</code>"),
      createDetailRow("Vault Asset", `${snapshot.simulation.asset_symbol} (Decimals: ${decimals})`),
      createDetailRow("Share model", "internal non-transferable shares"),
      createDetailRow("Strategy State", `<span class="status-pill" style="margin:0; padding:2px 8px;">${snapshot.vault.strategy_state.toUpperCase()}</span>`),
      createDetailRow("Selected strategy", snapshot.vault.selected_strategy),
      createDetailRow("Reported NAV", formatUsd(realNav)),
      createDetailRow("Summary PnL", formatUsd(snapshot.vault.summary_pnl_usd)),
      createDetailRow("Prepared calls", formatNumber(snapshot.vault.call_count, 0)),
    ].join("");

    vaultCalloutNode.textContent =
      "The key demo message is that state changes are explicit and parameterized: the update script toggles strategy-state, NAV, and PnL updates separately and can carry signal, metadata, and report hashes into the contract-facing flow.";
  }

  function renderClosingPanels(reportSummary) {
    setList("executive-summary", [
      "This presentation treats the vault and updater flow as the center of the project, with the research pipeline as the off-chain engine behind it.",
      "The strategy is not fully executed on-chain; instead, the contract provides transparent accounting, role-based updates, and user-facing state.",
      "Supporting research figures remain available, but the strongest blockchain contribution is the Solidity vault prototype and its local validation workflow.",
    ]);
    setList("limitations", chainLimitations);
    setList("contributions", chainContributions);
    setList("future-work", chainFutureWork);
  }

  function renderError(message) {
    const root = document.getElementById("presentation-root");
    const heroVerdict = document.getElementById("hero-verdict");
    if (heroVerdict) {
      heroVerdict.innerHTML = `<span class="error-card">${message}</span>`;
    }
    if (root) {
      root.innerHTML = `
        <section class="section">
          <article class="panel">
            <div class="error-card">
              <strong>Presentation data unavailable.</strong>
              <p>${message}</p>
            </div>
          </article>
        </section>
      `;
    }
  }

    Promise.all([readJson(snapshotUrl), readJson(exploratoryUrl), readJson(reportSummaryUrl)])
    .then(([snapshot, exploratory, reportSummary]) => {
      renderHero(snapshot, exploratory, reportSummary);
      renderRubricAndScope(snapshot, reportSummary);
      renderProblemCards();
      renderBoundaries();
      renderDeepDivePages();
      renderImplementationStatus();
      renderResults(snapshot, exploratory, reportSummary);
      renderCharts(snapshot);
      renderDemoAndVault(snapshot);
      renderClosingPanels(reportSummary);
    })
    .catch((error) => {
      renderError(error instanceof Error ? error.message : String(error));
    });
 function initPPTMode() {
    const startBtn = document.getElementById('start-ppt-btn');
    if (!startBtn) return;
    let slides = [];
    let currentIndex = 0;
    let controlsDiv = null;
    function splitChartsForPPT() {
      const chartGrid = document.getElementById('chart-grid');
      if (!chartGrid || chartGrid.dataset.splitDone) return;
      
      const charts = Array.from(chartGrid.children);
      if (charts.length <= 2) return; 
      const originalSection = chartGrid.closest('.section');
      chartGrid.innerHTML = '';
      chartGrid.appendChild(charts[0]);
      chartGrid.appendChild(charts[1]);
      chartGrid.dataset.splitDone = "true";
      let insertReference = originalSection;
 
      for (let i = 2; i < charts.length; i += 2) {
        const newSection = originalSection.cloneNode(true); 

        const title = newSection.querySelector('h2');
        if (title) title.innerText += " (Cont.)";
        
        const newGrid = newSection.querySelector('.chart-grid');
        newGrid.innerHTML = ''; 
        newGrid.appendChild(charts[i]);
        if (charts[i+1]) newGrid.appendChild(charts[i+1]); 
        insertReference.parentNode.insertBefore(newSection, insertReference.nextSibling);
        insertReference = newSection; 
      }
    }
    function buildSlides() {
      splitChartsForPPT(); 
      slides = [document.querySelector('.hero'), ...document.querySelectorAll('.section')];
    }
    function updateView() {
      slides.forEach((slide, index) => {
        if (index === currentIndex) {
          slide.classList.add('slide-active');
        } else {
          slide.classList.remove('slide-active');
        }
      });
      const prevBtn = document.getElementById('ppt-prev');
      const nextBtn = document.getElementById('ppt-next');
      if (prevBtn) prevBtn.disabled = currentIndex === 0;
      if (nextBtn) nextBtn.disabled = currentIndex === slides.length - 1;

      let progressBar = document.getElementById('ppt-progress-bar');
      if (!progressBar) {
        progressBar = document.createElement('div');
        progressBar.id = 'ppt-progress-bar';
        progressBar.className = 'ppt-progress';
        document.body.appendChild(progressBar);
      }
      progressBar.style.width = `${((currentIndex + 1) / slides.length) * 100}%`;
      let pageCount = document.getElementById('ppt-page-count');
      if (!pageCount) {
        pageCount = document.createElement('div');
        pageCount.id = 'ppt-page-count';
        pageCount.className = 'ppt-page-count';
        document.body.appendChild(pageCount);
      }
      pageCount.innerText = `${currentIndex + 1} / ${slides.length}`;
      window.scrollTo(0, 0); 
    }
    function enterPPTMode() {
      buildSlides();
      currentIndex = 0;
      document.body.classList.add('ppt-mode');
      
      if (!controlsDiv) {
        controlsDiv = document.createElement('div');
        controlsDiv.className = 'ppt-controls';
        controlsDiv.innerHTML = `
          <button id="ppt-prev" class="ppt-btn">◀ Prev</button>
          <button id="ppt-next" class="ppt-btn">Next ▶</button>
          <button id="ppt-exit" class="ppt-btn exit-btn">Exit PPT</button>
        `;
        document.body.appendChild(controlsDiv);
        document.getElementById('ppt-prev').addEventListener('click', () => {
          if (currentIndex > 0) { currentIndex--; updateView(); }
        });
        document.getElementById('ppt-next').addEventListener('click', () => {
          if (currentIndex < slides.length - 1) { currentIndex++; updateView(); }
        });
        document.getElementById('ppt-exit').addEventListener('click', exitPPTMode);
      }
      
      controlsDiv.style.display = 'flex';
      updateView();
    }
    function exitPPTMode() {
      document.body.classList.remove('ppt-mode');
      slides.forEach(slide => slide.classList.remove('slide-active'));
      if (controlsDiv) controlsDiv.style.display = 'none';
      const progressBar = document.getElementById('ppt-progress-bar');
      if (progressBar) progressBar.remove();
      const pageCount = document.getElementById('ppt-page-count');
      if (pageCount) pageCount.remove();
    }
    startBtn.addEventListener('click', (e) => {
      e.preventDefault();
      enterPPTMode();
    });
    window.addEventListener('keydown', (e) => {
      if (!document.body.classList.contains('ppt-mode')) return;
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        if (currentIndex < slides.length - 1) { currentIndex++; updateView(); }
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        if (currentIndex > 0) { currentIndex--; updateView(); }
      } else if (e.key === 'Escape') {
        exitPPTMode();
      }
    });
  }
  setTimeout(initPPTMode, 800);
 function initImageLightbox() {
  document.addEventListener('click', (e) => {
    if (e.target.closest('.chart-media') || e.target.closest('.chart-open')) {
      e.preventDefault();
      const href = e.target.closest('a').href;

      const overlay = document.createElement('div');
      overlay.style.cssText = 'position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 100000; display: grid; place-items: center; cursor: zoom-out;';
      
      const img = document.createElement('img');
      img.src = href;
      img.style.cssText = 'max-width: 90vw; max-height: 90vh; border-radius: 12px; box-shadow: 0 20px 50px rgba(0,0,0,0.5);';
      
      overlay.appendChild(img);
      document.body.appendChild(overlay);

      overlay.addEventListener('click', () => overlay.remove());
    }
  });
 }
 setTimeout(initImageLightbox, 800);
})();
