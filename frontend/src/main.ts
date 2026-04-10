import "./style.css";

interface DemoMeta {
  title: string;
  subtitle: string;
  generated_at: string;
  symbol: string;
  venue: string;
  frequency: string;
  date_range: {
    start: string;
    end_exclusive: string;
  };
  chain_name: string;
}

interface DemoChart {
  title: string;
  subtitle: string;
  section: string;
  image: string;
  source_path: string;
}

interface StrategyRow {
  strategy_name: string;
  source: string;
  source_subtype: string;
  task: string;
  trade_count: number;
  cumulative_return: number;
  annualized_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  average_trade_return_bps: number;
  total_net_pnl_usd: number;
  final_equity_usd: number;
}

interface ActivityItem {
  timestamp: string;
  kind: string;
  title: string;
  detail: string;
}

interface DemoSnapshot {
  meta: DemoMeta;
  overview: {
    goal: string;
    story_points: string[];
    layers: Array<{ label: string; detail: string }>;
  };
  research: {
    canonical_rows: number;
    perpetual_rows: number;
    funding_events: number;
    coverage_ratio: number;
    funding_mean_bps: number;
    funding_std_bps: number;
    spread_mean_bps: number;
    annualized_volatility: number;
  };
  models: {
    baseline_best: Record<string, unknown>;
    deep_learning_best: Record<string, unknown>;
  };
  backtest: {
    summary: Record<string, unknown>;
    best_strategy: StrategyRow;
    top_strategies: StrategyRow[];
    assumptions: string[];
  };
  charts: DemoChart[];
  vault: {
    chain_name: string;
    vault_address: string;
    stablecoin_address: string;
    selected_strategy: string;
    strategy_state: string;
    suggested_direction: string;
    reported_nav_assets: number;
    summary_pnl_assets: number;
    summary_pnl_usd: number;
    call_count: number;
    execution_summary: Record<string, unknown>;
  };
  activity_log: ActivityItem[];
  simulation: {
    asset_symbol: string;
    asset_decimals: number;
    wallet_cash_assets: number;
    base_vault_cash_assets: number;
    base_reported_nav_assets: number;
    base_total_shares: number;
    user_shares: number;
    strategy_state: string;
    operator_plan: {
      selected_strategy: string;
      strategy_state: string;
      suggested_direction: string;
      reported_nav_assets: number;
      summary_pnl_assets: number;
      summary_pnl_usd: number;
      should_trade: boolean;
      demo_activation_state: string;
      demo_activation_direction: string;
    };
  };
}

interface SimulationState {
  walletCashAssets: number;
  vaultCashAssets: number;
  reportedNavAssets: number;
  totalShares: number;
  userShares: number;
  strategyState: string;
  suggestedDirection: string;
  selectedStrategy: string;
  amountInputAssets: number;
  activityLog: ActivityItem[];
}

const appNode = document.querySelector<HTMLDivElement>("#app");

if (!appNode) {
  throw new Error("App root not found.");
}

const app = appNode;

const DEFAULT_DEPOSIT_ASSETS = 2_500 * 10 ** 6;
const DEFAULT_WITHDRAW_ASSETS = 1_000 * 10 ** 6;

let snapshotState: DemoSnapshot | null = null;
let simulationState: SimulationState | null = null;

function formatDate(dateText: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(dateText));
}

function formatDateTime(dateText: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateText));
}

function formatUsd(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
  }).format(value);
}

function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${(value * 100).toFixed(2)}%`;
}

function formatBps(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return "n/a";
  }
  return `${value.toFixed(2)} bps`;
}

function formatAssets(
  assets: number,
  assetSymbol: string,
  decimals: number,
  digits = 2,
): string {
  return `${formatNumber(assets / 10 ** decimals, digits)} ${assetSymbol}`;
}

function formatAddress(address: string): string {
  if (!address || address.length < 12) {
    return address || "n/a";
  }
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function createInitialSimulationState(snapshot: DemoSnapshot): SimulationState {
  return {
    walletCashAssets: snapshot.simulation.wallet_cash_assets,
    vaultCashAssets: snapshot.simulation.base_vault_cash_assets,
    reportedNavAssets: snapshot.simulation.base_reported_nav_assets,
    totalShares: snapshot.simulation.base_total_shares,
    userShares: snapshot.simulation.user_shares,
    strategyState: snapshot.simulation.strategy_state,
    suggestedDirection: "flat",
    selectedStrategy: snapshot.vault.selected_strategy,
    amountInputAssets: DEFAULT_DEPOSIT_ASSETS,
    activityLog: [...snapshot.activity_log].reverse(),
  };
}

function convertToShares(state: SimulationState, assets: number): number {
  if (state.totalShares === 0 || state.reportedNavAssets === 0) {
    return assets;
  }
  return Math.floor((assets * state.totalShares) / state.reportedNavAssets);
}

function previewWithdrawShares(state: SimulationState, assets: number): number {
  if (state.totalShares === 0 || state.reportedNavAssets === 0) {
    return assets;
  }
  return Math.ceil((assets * state.totalShares) / state.reportedNavAssets);
}

function pushActivity(state: SimulationState, item: ActivityItem): SimulationState {
  return {
    ...state,
    activityLog: [item, ...state.activityLog].slice(0, 12),
  };
}

function renderLoading(): void {
  app.innerHTML = `
    <main class="loading-shell">
      <div class="loading-panel">
        <p class="eyebrow">Preparing Demo</p>
        <h1>Loading the funding-rate arbitrage dashboard...</h1>
        <p>Reading the local demo snapshot and chart assets.</p>
      </div>
    </main>
  `;
}

function renderError(errorMessage: string): void {
  app.innerHTML = `
    <main class="loading-shell">
      <div class="loading-panel error-panel">
        <p class="eyebrow">Snapshot Missing</p>
        <h1>The frontend could not load <code>/demo/demo_snapshot.json</code>.</h1>
        <p>${errorMessage}</p>
        <pre class="command-block">& 'd:\\MG\\anaconda3\\python.exe' scripts/demo/export_demo_snapshot.py --config configs/demo/default.yaml</pre>
        <pre class="command-block">cd frontend
npm install
npm run dev</pre>
      </div>
    </main>
  `;
}

function metricCard(label: string, value: string, note: string): string {
  return `
    <article class="metric-card">
      <p class="metric-label">${label}</p>
      <h3>${value}</h3>
      <p class="metric-note">${note}</p>
    </article>
  `;
}

function renderDashboard(snapshot: DemoSnapshot, state: SimulationState): void {
  const baselineBest = snapshot.models.baseline_best;
  const dlBest = snapshot.models.deep_learning_best;
  const assetSymbol = snapshot.simulation.asset_symbol;
  const assetDecimals = snapshot.simulation.asset_decimals;
  const visibleEvents = state.activityLog.slice(0, 8);
  const amountInputValue = (state.amountInputAssets / 10 ** assetDecimals).toFixed(2);

  app.innerHTML = `
    <div class="page-shell">
      <div class="page-noise"></div>
      <header class="masthead" id="top">
        <div class="masthead-copy">
          <p class="eyebrow">Signal To Settlement</p>
          <h1>${snapshot.meta.title}</h1>
          <p class="lede">${snapshot.meta.subtitle}</p>
          <div class="hero-meta">
            <span>${snapshot.meta.symbol} on ${snapshot.meta.venue}</span>
            <span>${formatDate(snapshot.meta.date_range.start)} to ${formatDate(snapshot.meta.date_range.end_exclusive)}</span>
            <span>${snapshot.meta.frequency} research frequency</span>
            <span>${snapshot.meta.chain_name}</span>
          </div>
        </div>
        <aside class="masthead-panel">
          <p class="panel-label">Project Goal</p>
          <p class="panel-text">${snapshot.overview.goal}</p>
          <div class="status-chip-row">
            <span class="status-chip">Research pipeline ready</span>
            <span class="status-chip">Backtest artifacts loaded</span>
            <span class="status-chip">Vault prototype synced locally</span>
          </div>
        </aside>
      </header>

      <section class="metrics-ribbon">
        ${metricCard(
          "Data Window",
          `${formatNumber(snapshot.research.canonical_rows, 0)} hours`,
          `${formatNumber(snapshot.research.funding_events, 0)} funding events across the primary BTCUSDT sample.`,
        )}
        ${metricCard(
          "Best Backtest",
          formatUsd(snapshot.backtest.best_strategy.total_net_pnl_usd),
          `${snapshot.backtest.best_strategy.strategy_name} with ${formatNumber(snapshot.backtest.best_strategy.trade_count, 0)} trades.`,
        )}
        ${metricCard(
          "Baseline Benchmark",
          formatNumber((baselineBest["pearson_corr"] as number | null | undefined) ?? null, 3),
          `${String(baselineBest["model_name"] ?? "baseline")} test-set correlation.`,
        )}
        ${metricCard(
          "LSTM Benchmark",
          formatNumber((dlBest["pearson_corr"] as number | null | undefined) ?? null, 3),
          `${String(dlBest["model_name"] ?? "lstm")} test-set correlation.`,
        )}
      </section>

      <section class="section-grid">
        <section class="story-panel">
          <div class="section-heading">
            <p class="section-kicker">Project Overview</p>
            <h2>One prototype, four connected layers</h2>
          </div>
          <div class="story-list">
            ${snapshot.overview.layers
              .map(
                (layer) => `
                  <article class="story-card">
                    <p class="story-index">${layer.label}</p>
                    <p>${layer.detail}</p>
                  </article>
                `,
              )
              .join("")}
          </div>
          <div class="story-points">
            ${snapshot.overview.story_points
              .map((point) => `<div class="story-point">${point}</div>`)
              .join("")}
          </div>
        </section>

        <aside class="research-panel">
          <div class="section-heading">
            <p class="section-kicker">Research Snapshot</p>
            <h2>Why this market is interesting</h2>
          </div>
          <div class="research-grid">
            ${metricCard("Coverage", formatPercent(snapshot.research.coverage_ratio), "No missing hours inside the observed research range.")}
            ${metricCard("Funding Mean", formatBps(snapshot.research.funding_mean_bps), "Persistent positive funding dominates the sample.") }
            ${metricCard("Spread Mean", formatBps(snapshot.research.spread_mean_bps), "Basis is small on average but wide enough for short-lived dislocations.") }
            ${metricCard("Perp Vol", formatPercent(snapshot.research.annualized_volatility), "Average realized annualized volatility from hourly returns.") }
          </div>
        </aside>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <p class="section-kicker">Key Charts</p>
          <h2>From funding regimes to backtest outcomes</h2>
        </div>
        <div class="chart-gallery">
          ${snapshot.charts
            .map(
              (chart) => `
                <figure class="chart-card">
                  <div class="chart-header">
                    <p class="chart-section">${chart.section}</p>
                    <h3>${chart.title}</h3>
                    <p>${chart.subtitle}</p>
                  </div>
                  <img src="${chart.image}" alt="${chart.title}" loading="lazy" />
                </figure>
              `,
            )
            .join("")}
        </div>
      </section>

      <section class="section-grid">
        <section class="results-panel">
          <div class="section-heading">
            <p class="section-kicker">Strategy Metrics</p>
            <h2>Benchmark the rule-based, ML, and deep-learning outputs</h2>
          </div>
          <div class="model-strip">
            <article class="model-card">
              <p class="model-type">Baseline Leader</p>
              <h3>${String(baselineBest["model_name"] ?? "n/a")}</h3>
              <p>Task: ${String(baselineBest["task"] ?? "n/a")}</p>
              <dl>
                <div><dt>Split</dt><dd>${String(baselineBest["split"] ?? "n/a")}</dd></div>
                <div><dt>Pearson</dt><dd>${formatNumber((baselineBest["pearson_corr"] as number | null | undefined) ?? null, 3)}</dd></div>
                <div><dt>RMSE</dt><dd>${formatNumber((baselineBest["rmse"] as number | null | undefined) ?? null, 3)}</dd></div>
              </dl>
            </article>
            <article class="model-card">
              <p class="model-type">Deep Learning</p>
              <h3>${String(dlBest["model_name"] ?? "n/a")}</h3>
              <p>Task: ${String(dlBest["task"] ?? "n/a")}</p>
              <dl>
                <div><dt>Split</dt><dd>${String(dlBest["split"] ?? "n/a")}</dd></div>
                <div><dt>Pearson</dt><dd>${formatNumber((dlBest["pearson_corr"] as number | null | undefined) ?? null, 3)}</dd></div>
                <div><dt>RMSE</dt><dd>${formatNumber((dlBest["rmse"] as number | null | undefined) ?? null, 3)}</dd></div>
              </dl>
            </article>
            <article class="model-card">
              <p class="model-type">Backtest Winner</p>
              <h3>${snapshot.backtest.best_strategy.strategy_name}</h3>
              <p>${snapshot.backtest.best_strategy.source_subtype}</p>
              <dl>
                <div><dt>PnL</dt><dd>${formatUsd(snapshot.backtest.best_strategy.total_net_pnl_usd)}</dd></div>
                <div><dt>Sharpe</dt><dd>${formatNumber(snapshot.backtest.best_strategy.sharpe_ratio, 3)}</dd></div>
                <div><dt>Win Rate</dt><dd>${formatPercent(snapshot.backtest.best_strategy.win_rate)}</dd></div>
              </dl>
            </article>
          </div>
          <div class="table-shell">
            <table>
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Source</th>
                  <th>Trades</th>
                  <th>Cum Return</th>
                  <th>Sharpe</th>
                  <th>Net PnL</th>
                </tr>
              </thead>
              <tbody>
                ${snapshot.backtest.top_strategies
                  .map(
                    (row) => `
                      <tr>
                        <td>${row.strategy_name}</td>
                        <td>${row.source_subtype}</td>
                        <td>${formatNumber(row.trade_count, 0)}</td>
                        <td>${formatPercent(row.cumulative_return)}</td>
                        <td>${formatNumber(row.sharpe_ratio, 3)}</td>
                        <td>${formatUsd(row.total_net_pnl_usd)}</td>
                      </tr>
                    `,
                  )
                  .join("")}
              </tbody>
            </table>
          </div>
        </section>

        <aside class="assumptions-panel">
          <div class="section-heading">
            <p class="section-kicker">Backtest Assumptions</p>
            <h2>Explicit and presentation-friendly</h2>
          </div>
          <ul class="assumption-list">
            ${snapshot.backtest.assumptions
              .slice(0, 6)
              .map((item) => `<li>${item}</li>`)
              .join("")}
          </ul>
        </aside>
      </section>

      <section class="section-grid vault-zone">
        <section class="vault-panel">
          <div class="section-heading">
            <p class="section-kicker">Vault Status</p>
            <h2>Mock operator state mirrored into the on-chain vault</h2>
          </div>
          <div class="vault-status-grid">
            ${metricCard("Strategy State", snapshot.vault.strategy_state.toUpperCase(), `Selected strategy: ${snapshot.vault.selected_strategy}`)}
            ${metricCard("Reported NAV", formatAssets(snapshot.vault.reported_nav_assets, assetSymbol, assetDecimals), `Summary PnL: ${formatUsd(snapshot.vault.summary_pnl_usd)}`)}
            ${metricCard("Suggested Direction", snapshot.vault.suggested_direction, `${snapshot.vault.call_count} prepared contract calls in the latest operator payload.`)}
            ${metricCard("Execution Mode", String(snapshot.vault.execution_summary["mode"] ?? "dry-run"), `Vault address ${formatAddress(snapshot.vault.vault_address)}`)}
          </div>
          <div class="vault-meta-grid">
            <div>
              <p class="meta-label">Chain</p>
              <p>${snapshot.vault.chain_name}</p>
            </div>
            <div>
              <p class="meta-label">Vault</p>
              <p>${formatAddress(snapshot.vault.vault_address)}</p>
            </div>
            <div>
              <p class="meta-label">Stablecoin</p>
              <p>${formatAddress(snapshot.vault.stablecoin_address)}</p>
            </div>
            <div>
              <p class="meta-label">Operator Mode</p>
              <p>${String(snapshot.vault.execution_summary["mode"] ?? "dry-run")}</p>
            </div>
          </div>
        </section>

        <section class="console-panel">
          <div class="section-heading">
            <p class="section-kicker">Local Demo Console</p>
            <h2>Deposit, update strategy state, apply NAV, and inspect accounting</h2>
          </div>
          <p class="console-note">
            This console is intentionally local and educational. It simulates the vault accounting flow using the exported snapshot rather than a live wallet connection.
          </p>
          <div class="console-grid">
            <article class="console-card">
              <p class="console-label">Wallet Cash</p>
              <h3>${formatAssets(state.walletCashAssets, assetSymbol, assetDecimals)}</h3>
            </article>
            <article class="console-card">
              <p class="console-label">Vault Cash</p>
              <h3>${formatAssets(state.vaultCashAssets, assetSymbol, assetDecimals)}</h3>
            </article>
            <article class="console-card">
              <p class="console-label">Reported NAV</p>
              <h3>${formatAssets(state.reportedNavAssets, assetSymbol, assetDecimals)}</h3>
            </article>
            <article class="console-card">
              <p class="console-label">User Shares</p>
              <h3>${formatAssets(state.userShares, "shares", assetDecimals)}</h3>
            </article>
          </div>
          <div class="console-status-row">
            <span class="status-chip accent">${state.strategyState.toUpperCase()}</span>
            <span class="status-chip">${state.selectedStrategy}</span>
            <span class="status-chip">${state.suggestedDirection}</span>
          </div>
          <div class="control-panel">
            <label class="control-label" for="amount-input">Demo amount (${assetSymbol})</label>
            <div class="control-row">
              <input id="amount-input" class="amount-input" type="number" min="0" step="100" value="${amountInputValue}" />
              <button class="action-button" data-action="deposit">Deposit</button>
              <button class="action-button ghost" data-action="withdraw">Withdraw</button>
            </div>
            <div class="control-row secondary">
              <button class="action-button" data-action="toggle-strategy">Strategy Update</button>
              <button class="action-button" data-action="apply-operator">NAV/PnL Update</button>
              <button class="action-button ghost" data-action="reset">Reset</button>
            </div>
          </div>
          <div class="console-footnote">
            <p>Demo operator plan: ${snapshot.simulation.operator_plan.selected_strategy}, target NAV ${formatAssets(snapshot.simulation.operator_plan.reported_nav_assets, assetSymbol, assetDecimals)}, summary PnL ${formatUsd(snapshot.simulation.operator_plan.summary_pnl_usd)}.</p>
          </div>
        </section>
      </section>

      <section class="section-block log-panel">
        <div class="section-heading">
          <p class="section-kicker">Example Activity Log</p>
          <h2>Project milestones plus live demo interactions</h2>
        </div>
        <div class="log-grid">
          ${visibleEvents
            .map(
              (item) => `
                <article class="log-entry log-${item.kind}">
                  <p class="log-time">${formatDateTime(item.timestamp)}</p>
                  <h3>${item.title}</h3>
                  <p>${item.detail}</p>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    </div>
  `;

  const amountInput = document.querySelector<HTMLInputElement>("#amount-input");
  if (amountInput) {
    amountInput.addEventListener("input", () => {
      if (!simulationState) {
        return;
      }
      const parsed = Number(amountInput.value);
      simulationState = {
        ...simulationState,
        amountInputAssets: Number.isFinite(parsed) ? Math.max(parsed, 0) * 10 ** assetDecimals : 0,
      };
    });
  }

  document.querySelectorAll<HTMLButtonElement>("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!snapshotState || !simulationState) {
        return;
      }
      const action = button.dataset.action;
      const amountAssets = Math.round(simulationState.amountInputAssets);
      const now = new Date().toISOString();

      if (action === "deposit") {
        if (amountAssets <= 0 || amountAssets > simulationState.walletCashAssets) {
          simulationState = pushActivity(simulationState, {
            timestamp: now,
            kind: "demo",
            title: "Deposit rejected",
            detail: "Choose a positive amount that is smaller than the demo wallet cash balance.",
          });
          renderDashboard(snapshotState, simulationState);
          return;
        }
        const mintedShares = convertToShares(simulationState, amountAssets);
        simulationState = pushActivity(
          {
            ...simulationState,
            walletCashAssets: simulationState.walletCashAssets - amountAssets,
            vaultCashAssets: simulationState.vaultCashAssets + amountAssets,
            reportedNavAssets: simulationState.reportedNavAssets + amountAssets,
            totalShares: simulationState.totalShares + mintedShares,
            userShares: simulationState.userShares + mintedShares,
          },
          {
            timestamp: now,
            kind: "vault",
            title: "Deposit simulated",
            detail: `Deposited ${formatAssets(amountAssets, assetSymbol, assetDecimals)} and minted ${formatAssets(mintedShares, "shares", assetDecimals)}.`,
          },
        );
      }

      if (action === "withdraw") {
        const burnedShares = previewWithdrawShares(simulationState, amountAssets);
        if (
          amountAssets <= 0 ||
          burnedShares > simulationState.userShares ||
          amountAssets > simulationState.vaultCashAssets
        ) {
          simulationState = pushActivity(simulationState, {
            timestamp: now,
            kind: "demo",
            title: "Withdraw rejected",
            detail: "The demo user needs enough shares and the vault needs enough cash for the requested withdrawal.",
          });
          renderDashboard(snapshotState, simulationState);
          return;
        }
        simulationState = pushActivity(
          {
            ...simulationState,
            walletCashAssets: simulationState.walletCashAssets + amountAssets,
            vaultCashAssets: simulationState.vaultCashAssets - amountAssets,
            reportedNavAssets: Math.max(simulationState.reportedNavAssets - amountAssets, 0),
            totalShares: Math.max(simulationState.totalShares - burnedShares, 0),
            userShares: Math.max(simulationState.userShares - burnedShares, 0),
          },
          {
            timestamp: now,
            kind: "vault",
            title: "Withdrawal simulated",
            detail: `Withdrew ${formatAssets(amountAssets, assetSymbol, assetDecimals)} and burned ${formatAssets(burnedShares, "shares", assetDecimals)}.`,
          },
        );
      }

      if (action === "toggle-strategy") {
        const active = simulationState.strategyState !== "active";
        simulationState = pushActivity(
          {
            ...simulationState,
            strategyState: active
              ? snapshotState.simulation.operator_plan.demo_activation_state
              : "idle",
            suggestedDirection: active
              ? snapshotState.simulation.operator_plan.demo_activation_direction
              : "flat",
            selectedStrategy: snapshotState.simulation.operator_plan.selected_strategy,
          },
          {
            timestamp: now,
            kind: "strategy",
            title: active ? "Strategy activated" : "Strategy idled",
            detail: active
              ? `Demo operator switched the strategy to ${snapshotState.simulation.operator_plan.demo_activation_direction}.`
              : "The local demo returned the strategy to an idle flat state.",
          },
        );
      }

      if (action === "apply-operator") {
        const targetNav = snapshotState.simulation.operator_plan.reported_nav_assets;
        const pnlDelta = snapshotState.simulation.operator_plan.summary_pnl_assets;
        const cashDelta = targetNav - simulationState.reportedNavAssets;
        simulationState = pushActivity(
          {
            ...simulationState,
            reportedNavAssets: targetNav,
            vaultCashAssets: Math.max(simulationState.vaultCashAssets + cashDelta, 0),
            selectedStrategy: snapshotState.simulation.operator_plan.selected_strategy,
          },
          {
            timestamp: now,
            kind: "vault",
            title: "Operator NAV update applied",
            detail: `Reported NAV moved to ${formatAssets(targetNav, assetSymbol, assetDecimals)} with a demo PnL delta of ${formatUsd(snapshotState.simulation.operator_plan.summary_pnl_usd)}.`,
          },
        );
        if (pnlDelta !== 0) {
          simulationState = pushActivity(simulationState, {
            timestamp: now,
            kind: "demo",
            title: "Mock liquidity synchronized",
            detail: "For demo readability, vault cash was mirrored with the operator NAV update so withdrawals remain intuitive.",
          });
        }
      }

      if (action === "reset") {
        simulationState = createInitialSimulationState(snapshotState);
      }

      renderDashboard(snapshotState, simulationState);
    });
  });
}

async function loadDashboard(): Promise<void> {
  renderLoading();
  try {
    const response = await fetch("/demo/demo_snapshot.json", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    snapshotState = (await response.json()) as DemoSnapshot;
    simulationState = createInitialSimulationState(snapshotState);
    renderDashboard(snapshotState, simulationState);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error while loading the demo snapshot.";
    renderError(message);
  }
}

void loadDashboard();
