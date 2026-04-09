import "./style.css";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root not found.");
}

const cards = [
  {
    title: "Strategy Snapshot",
    body: "Start with BTC perpetual funding-rate arbitrage on a single venue, then expand only after the pipeline is stable.",
  },
  {
    title: "Backtest Layer",
    body: "The initial scaffold expects cost-aware backtests with fees, slippage, funding accrual, and clear performance metrics.",
  },
  {
    title: "Vault Prototype",
    body: "Foundry workspace includes a mock stablecoin and a starter delta-neutral vault for deposits, withdrawals, shares, NAV updates, and pause control.",
  },
  {
    title: "Next Milestone",
    body: "Implement real ingestion for one exchange, define the cleaned schema, and wire the first baseline signal into the backtest engine.",
  },
];

app.innerHTML = `
  <main class="page-shell">
    <section class="hero">
      <p class="eyebrow">Course Project Prototype</p>
      <h1>Deep Learning-Based Delta-Neutral Statistical Arbitrage</h1>
      <p class="summary">
        A lightweight dashboard scaffold for the quant pipeline, backtesting engine,
        Solidity vault, and presentation demo.
      </p>
    </section>
    <section class="grid">
      ${cards
        .map(
          (card) => `
            <article class="card">
              <h2>${card.title}</h2>
              <p>${card.body}</p>
            </article>
          `,
        )
        .join("")}
    </section>
  </main>
`;

