(function () {
  const snapshotUrl = "/demo_showcase/demo_snapshot.json";
  const exploratoryUrl = "/demo_showcase/exploratory_dl_summary.json";
  const reportSummaryUrl = "/demo_showcase/report/summary.json";

  const chartOrder = [
    "DEMO ONLY | Synthetic funding-rate regime map",
    "DEMO ONLY | Synthetic perpetual-vs-spot spread",
    "DEMO ONLY | DL test metric comparison",
    "DEMO ONLY | Strict equity curves",
    "DEMO ONLY | Strict drawdown comparison",
    "DEMO ONLY | Family comparison",
    "DEMO ONLY | Exploratory cumulative PnL",
  ];

  const rubricItems = [
    {
      title: "Project idea",
      detail:
        "Explain why funding-rate dislocations are interesting only when they survive execution frictions and basis convergence risk.",
    },
    {
      title: "Technical design",
      detail:
        "Show the hybrid architecture: off-chain data and modeling, on-chain vault accounting, and a lightweight frontend.",
    },
    {
      title: "Implementation",
      detail:
        "Walk through data context, features and labels, model zoo comparison, cost-aware backtest, and vault-state mirroring.",
    },
    {
      title: "System demo",
      detail:
        "Use this presentation page first, then switch to the interactive dashboard and final report for live evidence.",
    },
  ];

  const problemCards = [
    {
      title: "Funding-rate mispricing is not automatic alpha",
      detail:
        "A high funding rate does not guarantee profit. We still need basis convergence, disciplined entry timing, and post-cost validation.",
    },
    {
      title: "Execution frictions matter",
      detail:
        "Fees, slippage, holding horizon, and spread reversion speed can erase a strategy that looks profitable before costs.",
    },
    {
      title: "Prediction is only one layer",
      detail:
        "A useful system must connect data, signals, trade logic, risk metrics, and reporting instead of stopping at a model score.",
    },
    {
      title: "Smart contracts cannot run the full pipeline alone",
      detail:
        "The vault is the on-chain accounting layer, while market data processing and model inference remain off-chain.",
    },
  ];

  const implementationBlueprint = [
    {
      title: "Market context build",
      detail:
        "We construct hourly funding, spread, and volatility context so the presentation still mirrors a realistic BTCUSDT pipeline.",
      metric: (snapshot) => `${formatNumber(snapshot.research.canonical_rows, 0)} hourly rows`,
    },
    {
      title: "Model comparison layer",
      detail:
        "Rule-based baselines, simple ML, and multiple deep-learning families are compared under one standardized scoring story.",
      metric: (_, reportSummary) =>
        `${formatNumber(reportSummary.models.deep_learning_comparison.run_count, 0)} DL runs`,
    },
    {
      title: "Cost-aware backtest",
      detail:
        "Strategy outputs are evaluated with return, Sharpe, drawdown, trade count, and path behavior rather than raw prediction only.",
      metric: (snapshot) => `${formatNumber(snapshot.backtest.summary.strategy_count, 0)} strict strategies`,
    },
    {
      title: "Vault-state mirroring",
      detail:
        "The prototype ends with a vault update payload so the demo can show how off-chain intelligence maps into on-chain state.",
      metric: (snapshot) => `${formatNumber(snapshot.vault.call_count, 0)} prepared calls`,
    },
  ];

  async function readJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.status}`);
    }
    return response.json();
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
            <strong>${author}</strong>
          </div>
        `,
      )
      .join("");

    verdictNode.textContent = reportSummary.verdict;
    metricsNode.innerHTML = [
      createSummaryBadge("Best strict return", formatPercent(best.cumulative_return)),
      createSummaryBadge("Strict Sharpe", formatNumber(best.sharpe_ratio, 3)),
      createSummaryBadge(
        "Exploratory return",
        formatPercent(exploratoryBest?.cumulative_return ?? null),
      ),
      createSummaryBadge("Funding events", formatNumber(snapshot.research.funding_events, 0)),
    ].join("");
    artifactNode.textContent = `${snapshot.meta.artifact_label}: isolated synthetic showcase bundle for presentation use`;
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
        createDetailRow("Market", `${snapshot.meta.symbol} on ${snapshot.meta.venue}`),
        createDetailRow("Frequency", snapshot.meta.frequency),
        createDetailRow(
          "Time window",
          `${formatDate(snapshot.meta.date_range.start)} - ${formatDate(
            snapshot.meta.date_range.end_exclusive,
          )}`,
        ),
        createDetailRow("Generated", formatDateTime(snapshot.meta.generated_at)),
        createDetailRow("Bundle", snapshot.meta.bundle_name || "demo_showcase"),
      ].join("");
    }

    setList("story-points", snapshot.overview.story_points || []);
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

  function renderArchitecture(snapshot, reportSummary) {
    const node = document.getElementById("architecture-rail");
    if (!node) {
      return;
    }
    const layers = snapshot.overview.layers?.length
      ? snapshot.overview.layers
      : (reportSummary.layers || []).map((label) => ({ label, detail: "" }));
    node.innerHTML = layers
      .map(
        (layer, index) => `
          <article class="architecture-step">
            <div class="architecture-index">${index + 1}</div>
            <div>
              <strong>${layer.label}</strong>
              <p>${layer.detail}</p>
            </div>
          </article>
        `,
      )
      .join("");
  }

  function renderImplementation(snapshot, reportSummary) {
    const node = document.getElementById("implementation-grid");
    if (!node) {
      return;
    }
    node.innerHTML = implementationBlueprint
      .map(
        (item) => `
          <article class="module-card">
            <p class="section-kicker">Module</p>
            <strong>${item.title}</strong>
            <p>${item.detail}</p>
            <div class="module-metric">${item.metric(snapshot, reportSummary)}</div>
          </article>
        `,
      )
      .join("");
  }

  function renderResults(snapshot, exploratory, reportSummary) {
    const resultsNode = document.getElementById("results-highlight");
    const leaderboardNode = document.getElementById("leaderboard-panel");
    const robustnessNode = document.getElementById("robustness-panel");
    if (!resultsNode || !leaderboardNode || !robustnessNode) {
      return;
    }

    const best = snapshot.backtest.best_strategy;
    const exploratoryBest = exploratory.exploratory_summary?.best_showcase_row;
    const robustness = reportSummary.robustness;
    const costLow = robustness.cost_sensitivity?.[0];
    const costHigh = robustness.cost_sensitivity?.[robustness.cost_sensitivity.length - 1];
    const bestHolding = [...(robustness.holding_window_sensitivity || [])].sort(
      (left, right) => (right.cumulative_return || 0) - (left.cumulative_return || 0),
    )[0];
    const baseThreshold = (robustness.threshold_sensitivity || []).find(
      (item) => item.threshold_label === "base",
    );

    resultsNode.innerHTML = `
      <p class="section-kicker">Main takeaway</p>
      <h3>Strict track remains the primary claim</h3>
      <p class="panel-text">${reportSummary.verdict}</p>
      <div class="micro-grid">
        <article class="micro-card">
          <p class="metric-label">Best strategy</p>
          <strong>${best.display_name}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Net PnL</p>
          <strong>${formatUsd(best.total_net_pnl_usd)}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Trade count</p>
          <strong>${formatNumber(best.trade_count, 0)}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Max drawdown</p>
          <strong>${formatPercent(best.mark_to_market_max_drawdown)}</strong>
        </article>
      </div>
      <ul class="story-list">
        <li>TransformerEncoder leads the strict track, but the path is still visibly noisy.</li>
        <li>The exploratory branch is richer in opportunity count, not a replacement for the strict conclusion.</li>
        <li>We should present the exploratory metrics as supplementary behavior evidence.</li>
      </ul>
      <div class="subsection">
        <h3>Exploratory support</h3>
        <div class="detail-stack">
          ${createDetailRow(
            "Exploratory best",
            exploratoryBest?.display_name || exploratoryBest?.model_name || "n/a",
          )}
          ${createDetailRow(
            "Exploratory return",
            formatPercent(exploratoryBest?.cumulative_return ?? null),
          )}
          ${createDetailRow(
            "Exploratory drawdown",
            formatPercent(exploratoryBest?.mark_to_market_max_drawdown ?? null),
          )}
        </div>
      </div>
    `;

    leaderboardNode.innerHTML = `
      <p class="section-kicker">Strict leaderboard</p>
      <h3>Strategy ranking for the presentation</h3>
      <div class="table-shell">
        <table>
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Trades</th>
              <th>Return</th>
              <th>Sharpe</th>
              <th>Drawdown</th>
            </tr>
          </thead>
          <tbody>
            ${snapshot.backtest.top_strategies
              .map(
                (row) => `
                  <tr>
                    <td>${row.display_name}</td>
                    <td>${formatNumber(row.trade_count, 0)}</td>
                    <td>${formatPercent(row.cumulative_return)}</td>
                    <td>${formatNumber(row.sharpe_ratio, 3)}</td>
                    <td>${formatPercent(row.mark_to_market_max_drawdown)}</td>
                  </tr>
                `,
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;

    robustnessNode.innerHTML = `
      <p class="section-kicker">Robustness snapshots</p>
      <h3>How the strict winner behaves under perturbations</h3>
      <div class="micro-grid">
        <article class="micro-card">
          <p class="metric-label">Low cost case</p>
          <strong>${formatPercent(costLow?.cumulative_return ?? null)}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">High cost case</p>
          <strong>${formatPercent(costHigh?.cumulative_return ?? null)}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Best holding window</p>
          <strong>${bestHolding ? `${bestHolding.holding_window_hours}h` : "n/a"}</strong>
        </article>
        <article class="micro-card">
          <p class="metric-label">Base threshold trades</p>
          <strong>${formatNumber(baseThreshold?.trade_count ?? null, 0)}</strong>
        </article>
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
                  <span>Sharpe ${formatNumber(item.sharpe_ratio, 3)}</span>
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
      .slice(0, 6);

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
              <h3>${chart.title.replace("DEMO ONLY | ", "")}</h3>
              <p>${chart.subtitle}</p>
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

    timelineNode.innerHTML = (snapshot.activity_log || [])
      .map(
        (item) => `
          <article class="timeline-item">
            <div class="timeline-time">${formatDate(item.timestamp)}</div>
            <div>
              <strong>${item.title}</strong>
              <p>${item.detail}</p>
            </div>
          </article>
        `,
      )
      .join("");

    vaultNode.innerHTML = [
      createDetailRow("Chain", snapshot.vault.chain_name),
      createDetailRow("Selected strategy", snapshot.vault.selected_strategy),
      createDetailRow("Strategy state", snapshot.vault.strategy_state),
      createDetailRow("Suggested direction", snapshot.vault.suggested_direction),
      createDetailRow("Reported NAV", formatNumber(snapshot.vault.reported_nav_assets, 0)),
      createDetailRow("Summary PnL", formatUsd(snapshot.vault.summary_pnl_usd)),
      createDetailRow("Prepared calls", formatNumber(snapshot.vault.call_count, 0)),
    ].join("");

    vaultCalloutNode.textContent = snapshot.vault.execution_summary.status;
  }

  function renderClosingPanels(reportSummary) {
    setList("executive-summary", reportSummary.executive_summary || []);
    setList("limitations", reportSummary.limitations || []);
    setList("contributions", reportSummary.contributions || []);
    setList("future-work", reportSummary.future_work || []);
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
      renderArchitecture(snapshot, reportSummary);
      renderImplementation(snapshot, reportSummary);
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
})();
