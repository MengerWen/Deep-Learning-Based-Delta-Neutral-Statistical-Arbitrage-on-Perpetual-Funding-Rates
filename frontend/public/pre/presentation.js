(function () {
  const snapshotUrl = "../demo_showcase/demo_snapshot.json";
  const exploratoryUrl = "../demo_showcase/exploratory_dl_summary.json";
  const reportSummaryUrl = "../demo_showcase/report/summary.json";

  const formatNumber = (value, digits = 2) => {
    if (value == null || Number.isNaN(Number(value))) {
      return "n/a";
    }
    return new Intl.NumberFormat("en-US", {
      maximumFractionDigits: digits,
    }).format(Number(value));
  };

  const formatPercent = (value, digits = 2) => {
    if (value == null || Number.isNaN(Number(value))) {
      return "n/a";
    }
    return `${(Number(value) * 100).toFixed(digits)}%`;
  };

  const formatUsd = (value) => {
    if (value == null || Number.isNaN(Number(value))) {
      return "n/a";
    }
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(Number(value));
  };

  const formatDate = (value) =>
    new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "2-digit",
    }).format(new Date(value));

  const setList = (elementId, items) => {
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
  };

  const createDetailRow = (label, value) =>
    `<div class="detail-row"><span>${label}</span><span>${value}</span></div>`;

  const createMetricCard = (label, value, note) =>
    `<article class="metric-card"><p class="metric-label">${label}</p><strong>${value}</strong><p>${note}</p></article>`;

  const chartPriority = [
    "DEMO ONLY | Strict equity curves",
    "DEMO ONLY | DL test metric comparison",
    "DEMO ONLY | Family comparison",
    "DEMO ONLY | Exploratory cumulative PnL",
  ];

  function renderHero(snapshot, reportSummary) {
    const node = document.getElementById("hero-panel");
    if (!node) {
      return;
    }
    const best = snapshot.backtest.best_strategy;
    const dateRange = `${formatDate(snapshot.meta.date_range.start)} - ${formatDate(
      snapshot.meta.date_range.end_exclusive,
    )}`;
    node.innerHTML = `
      <p class="panel-kicker">${snapshot.meta.artifact_label || "Demo Bundle"}</p>
      <h2>${snapshot.meta.symbol} | ${snapshot.meta.venue} | ${snapshot.meta.frequency}</h2>
      <p>${reportSummary.verdict}</p>
      <div class="summary-badge-row">
        <div class="summary-badge">
          <span>Best strict strategy</span>
          <strong>${best.display_name}</strong>
        </div>
        <div class="summary-badge">
          <span>Net PnL</span>
          <strong>${formatUsd(best.total_net_pnl_usd)}</strong>
        </div>
        <div class="summary-badge">
          <span>Test return</span>
          <strong>${formatPercent(best.cumulative_return)}</strong>
        </div>
        <div class="summary-badge">
          <span>Date window</span>
          <strong>${dateRange}</strong>
        </div>
      </div>
      <div class="status-pill">Synthetic presentation bundle | keep this clearly labeled in the pre</div>
    `;
  }

  function renderGoalAndLayers(snapshot, reportSummary) {
    const goalNode = document.getElementById("goal-text");
    if (goalNode) {
      goalNode.textContent = snapshot.overview.goal || reportSummary.verdict;
    }

    const layerNode = document.getElementById("layer-list");
    if (!layerNode) {
      return;
    }
    const layers = snapshot.overview.layers?.length ? snapshot.overview.layers : [];
    layerNode.innerHTML = layers
      .map(
        (layer, index) => `
          <div class="flow-step">
            <div class="step-index">${index + 1}</div>
            <div>
              <strong>${layer.label}</strong>
              <p>${layer.detail}</p>
            </div>
          </div>
        `,
      )
      .join("");
  }

  function renderResearch(snapshot) {
    const node = document.getElementById("research-metrics");
    if (!node) {
      return;
    }
    const research = snapshot.research;
    node.innerHTML = [
      createMetricCard(
        "Canonical rows",
        formatNumber(research.canonical_rows, 0),
        "Hourly canonical market dataset used for the showcase window.",
      ),
      createMetricCard(
        "Funding events",
        formatNumber(research.funding_events, 0),
        "Observed funding timestamps aligned into the research dataset.",
      ),
      createMetricCard(
        "Coverage ratio",
        formatPercent(research.coverage_ratio),
        "We keep the market context almost fully covered after processing.",
      ),
      createMetricCard(
        "Funding mean",
        `${formatNumber(research.funding_mean_bps)} bps`,
        "Average funding level in the synthetic narrative series.",
      ),
      createMetricCard(
        "Funding std",
        `${formatNumber(research.funding_std_bps)} bps`,
        "Variation matters because dislocations are not stable across regimes.",
      ),
      createMetricCard(
        "Spread mean",
        `${formatNumber(research.spread_mean_bps)} bps`,
        "Perp-versus-spot spread is the mean-reversion anchor in the story.",
      ),
      createMetricCard(
        "Annualized vol",
        formatPercent(research.annualized_volatility),
        "Volatility keeps timing difficult even in a delta-neutral setup.",
      ),
      createMetricCard(
        "Primary market",
        `${snapshot.meta.symbol} @ ${snapshot.meta.venue}`,
        "Single-market scope keeps the prototype focused and explainable.",
      ),
    ].join("");
  }

  function renderModelSections(snapshot, exploratory, reportSummary) {
    const modelNode = document.getElementById("model-summary");
    const strictNode = document.getElementById("strict-summary");
    const exploratoryNode = document.getElementById("exploratory-summary");
    if (!modelNode || !strictNode || !exploratoryNode) {
      return;
    }

    const baseline = reportSummary.models.baseline_best;
    const deep = reportSummary.models.deep_learning_best;
    const best = snapshot.backtest.best_strategy;
    const exploratoryBest = exploratory.exploratory_summary?.best_showcase_row || null;

    modelNode.innerHTML = `
      <p class="section-kicker">Model hierarchy</p>
      <h3>Why deep learning is part of the story</h3>
      <div class="detail-stack">
        ${createDetailRow("Best baseline", baseline.display_name || baseline.model_name)}
        ${createDetailRow("Baseline corr", formatNumber(baseline.pearson_corr, 3))}
        ${createDetailRow("Best DL model", deep.display_name || deep.model_name)}
        ${createDetailRow("DL corr", formatNumber(deep.test_pearson_corr, 3))}
        ${createDetailRow("DL RMSE", formatNumber(deep.test_rmse, 2))}
      </div>
      <ul class="story-list">
        <li>The baseline proves the signal is not pure noise.</li>
        <li>The Transformer takes the lead without looking implausibly perfect.</li>
        <li>The ranking stays believable enough for a classroom demo narrative.</li>
      </ul>
    `;

    strictNode.innerHTML = `
      <p class="section-kicker">Strict track</p>
      <h3>Main conclusion under cost-aware assumptions</h3>
      <div class="detail-stack">
        ${createDetailRow("Selected strategy", best.display_name)}
        ${createDetailRow("Trades", formatNumber(best.trade_count, 0))}
        ${createDetailRow("Cumulative return", formatPercent(best.cumulative_return))}
        ${createDetailRow("Sharpe", formatNumber(best.sharpe_ratio, 3))}
        ${createDetailRow("Max drawdown", formatPercent(best.mark_to_market_max_drawdown))}
        ${createDetailRow("Net PnL", formatUsd(best.total_net_pnl_usd))}
      </div>
      <ul class="story-list">
        <li>The strict track is the main result we should present as the disciplined version.</li>
        <li>Returns stay positive after synthetic cost assumptions.</li>
        <li>Drawdown remains visible, which makes the result more credible.</li>
      </ul>
    `;

    exploratoryNode.innerHTML = `
      <p class="section-kicker">Exploratory track</p>
      <h3>Supplementary evidence, not the primary claim</h3>
      <div class="detail-stack">
        ${createDetailRow(
          "Best exploratory model",
          exploratoryBest?.display_name || exploratoryBest?.model_name || "n/a",
        )}
        ${createDetailRow("Trades", formatNumber(exploratoryBest?.trade_count, 0))}
        ${createDetailRow("Cumulative return", formatPercent(exploratoryBest?.cumulative_return))}
        ${createDetailRow("Sharpe", formatNumber(exploratoryBest?.sharpe_ratio, 3))}
        ${createDetailRow(
          "Disclaimer",
          exploratory.disclaimer ? "supplementary synthetic track" : "n/a",
        )}
      </div>
      <ul class="story-list">
        <li>The exploratory branch shows a more aggressive opportunity definition.</li>
        <li>We should frame it as model-behavior evidence, not as the main thesis result.</li>
        <li>This helps us discuss upside and robustness without overstating the claim.</li>
      </ul>
    `;
  }

  function renderCharts(snapshot) {
    const node = document.getElementById("chart-grid");
    if (!node) {
      return;
    }
    const rank = new Map(chartPriority.map((title, index) => [title, index]));
    const charts = [...snapshot.charts]
      .sort((a, b) => (rank.get(a.title) ?? 99) - (rank.get(b.title) ?? 99))
      .slice(0, 4);

    node.innerHTML = charts
      .map(
        (chart) => `
          <article class="panel chart-card">
            <div class="chart-frame">
              <img src="../${chart.image}" alt="${chart.title}" />
            </div>
            <div class="chart-copy">
              <p class="chart-tag">${chart.section}</p>
              <h3>${chart.title.replace("DEMO ONLY | ", "")}</h3>
              <p>${chart.subtitle}</p>
            </div>
          </article>
        `,
      )
      .join("");
  }

  function renderVault(snapshot) {
    const node = document.getElementById("vault-summary");
    if (!node) {
      return;
    }
    const vault = snapshot.vault;
    node.innerHTML = `
      ${createDetailRow("Chain", vault.chain_name)}
      ${createDetailRow("Strategy", vault.selected_strategy)}
      ${createDetailRow("State", vault.strategy_state)}
      ${createDetailRow("Direction", vault.suggested_direction)}
      ${createDetailRow("Reported NAV", formatNumber(vault.reported_nav_assets, 0))}
      ${createDetailRow("Summary PnL", formatUsd(vault.summary_pnl_usd))}
      ${createDetailRow("Prepared calls", formatNumber(vault.call_count, 0))}
    `;
  }

  function renderPresentationNotes(snapshot, reportSummary) {
    const notes = [
      "Start from the problem framing: funding dislocation is only interesting if it survives execution frictions.",
      "Use the strict track as the main result and keep the exploratory branch as supplementary evidence.",
      "Highlight the full pipeline: data -> features -> model -> signal -> backtest -> vault accounting.",
      "State clearly that this presentation page uses the isolated DEMO ONLY synthetic showcase bundle.",
      `Close with the verdict: ${reportSummary.verdict}`,
      `If asked about deployment realism, point to the vault mirror: ${snapshot.vault.execution_summary.status}`,
    ];
    setList("presentation-notes", notes);
  }

  function renderCaveats(reportSummary) {
    setList("executive-summary", reportSummary.executive_summary || []);
    setList("limitations", reportSummary.limitations || []);
  }

  function renderError(message) {
    const root = document.getElementById("presentation-root");
    const hero = document.getElementById("hero-panel");
    if (hero) {
      hero.innerHTML = `<div class="error-card"><strong>Failed to load presentation data.</strong><p>${message}</p></div>`;
    }
    if (root) {
      root.innerHTML = `<section class="section"><article class="panel"><div class="error-card"><strong>Presentation data unavailable.</strong><p>${message}</p></div></article></section>`;
    }
  }

  Promise.all([
    fetch(snapshotUrl).then((response) => response.json()),
    fetch(exploratoryUrl).then((response) => response.json()),
    fetch(reportSummaryUrl).then((response) => response.json()),
  ])
    .then(([snapshot, exploratory, reportSummary]) => {
      renderHero(snapshot, reportSummary);
      renderGoalAndLayers(snapshot, reportSummary);
      renderResearch(snapshot);
      renderModelSections(snapshot, exploratory, reportSummary);
      renderCharts(snapshot);
      renderVault(snapshot);
      renderPresentationNotes(snapshot, reportSummary);
      renderCaveats(reportSummary);
    })
    .catch((error) => {
      renderError(error instanceof Error ? error.message : String(error));
    });
})();
