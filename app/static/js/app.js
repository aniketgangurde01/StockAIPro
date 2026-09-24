/**
 * StockAI - Main Dashboard Application Controller
 */

let chartManager = null;
let watchlistManager = null;
let isDemoMode = false;
let currentSymbol = "RELIANCE";

document.addEventListener("DOMContentLoaded", () => {
  chartManager = new StockChartManager("tradingview-chart-container");
  watchlistManager = new WatchlistManager();
  
  initUIEvents();
  loadMarketOverview();
  
  // Load default stock analysis on page load
  analyzeStock("RELIANCE");
});

function initUIEvents() {
  const searchInput = document.getElementById("stock-search-input");
  const analyzeBtn = document.getElementById("btn-analyze-stock");
  const autocomplete = document.getElementById("autocomplete-dropdown");
  const themeToggle = document.getElementById("btn-theme-toggle");
  const demoToggle = document.getElementById("btn-demo-toggle");
  const watchlistBtn = document.getElementById("btn-watchlist-nav");
  const closeWatchlistBtn = document.getElementById("btn-close-watchlist");
  const drawerBackdrop = document.getElementById("drawer-backdrop");
  const addWatchlistBtn = document.getElementById("btn-add-watchlist");

  // Search input autocomplete with debounce
  let debounceTimer = null;
  searchInput.addEventListener("input", (e) => {
    clearTimeout(debounceTimer);
    const q = e.target.value.trim();
    if (q.length === 0) {
      autocomplete.classList.remove("active");
      return;
    }
    debounceTimer = setTimeout(() => fetchAutocomplete(q), 200);
  });

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const q = searchInput.value.trim();
      if (q) {
        autocomplete.classList.remove("active");
        analyzeStock(q);
      }
    }
  });

  // Click outside closes autocomplete
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-box-container")) {
      autocomplete.classList.remove("active");
    }
  });

  analyzeBtn.addEventListener("click", () => {
    const q = searchInput.value.trim();
    if (q) {
      autocomplete.classList.remove("active");
      analyzeStock(q);
    }
  });

  // Quick chip buttons
  document.querySelectorAll(".chip-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const sym = btn.dataset.symbol;
      searchInput.value = sym;
      analyzeStock(sym);
    });
  });

  // Demo mode toggle
  demoToggle.addEventListener("click", () => {
    isDemoMode = !isDemoMode;
    demoToggle.classList.toggle("active", isDemoMode);
    demoToggle.querySelector(".demo-label").textContent = isDemoMode ? "Demo Mode (ON)" : "Live Market Mode";
    analyzeStock(currentSymbol);
  });

  // Theme toggle
  themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nextTheme);
    themeToggle.textContent = nextTheme === "dark" ? "🌙" : "☀️";
    if (chartManager && chartManager.rawCandles.length > 0) {
      chartManager.renderData(chartManager.rawCandles, window.lastTechnicals, window.lastCurrency);
    }
  });

  // Watchlist drawer
  const openWatchlist = () => {
    document.getElementById("watchlist-drawer").classList.add("open");
    drawerBackdrop.classList.add("active");
    watchlistManager.render("watchlist-items-container", (sym) => {
      closeWatchlist();
      searchInput.value = sym;
      analyzeStock(sym);
    });
  };

  const closeWatchlist = () => {
    document.getElementById("watchlist-drawer").classList.remove("open");
    drawerBackdrop.classList.remove("active");
  };

  watchlistBtn.addEventListener("click", openWatchlist);
  closeWatchlistBtn.addEventListener("click", closeWatchlist);
  drawerBackdrop.addEventListener("click", closeWatchlist);

  // Watchlist Add/Remove on current stock
  addWatchlistBtn.addEventListener("click", () => {
    if (!window.currentStockData) return;
    const added = watchlistManager.toggle(currentSymbol, window.currentStockData.name);
    updateWatchlistButtonState(added);
  });

  // Chart Timeframe Buttons
  document.querySelectorAll(".tf-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tf-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      chartManager.filterPeriod(btn.dataset.tf);
    });
  });

  // Chart Overlay Toggles
  document.querySelectorAll(".toggle-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const overlay = chip.dataset.overlay;
      const isActive = chartManager.toggleOverlay(overlay);
      chip.classList.toggle("active", isActive);
    });
  });

  watchlistManager.updateBadge();
}

async function fetchAutocomplete(query) {
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    const dropdown = document.getElementById("autocomplete-dropdown");
    
    if (!data.results || data.results.length === 0) {
      dropdown.classList.remove("active");
      return;
    }

    dropdown.innerHTML = data.results.map(r => `
      <div class="autocomplete-item" data-symbol="${r.symbol}">
        <div>
          <span class="autocomplete-sym">${r.symbol}</span>
          <span class="autocomplete-name">${r.name}</span>
        </div>
        <span class="autocomplete-badge">${r.sector}</span>
      </div>
    `).join("");

    dropdown.classList.add("active");

    dropdown.querySelectorAll(".autocomplete-item").forEach(item => {
      item.addEventListener("click", () => {
        const sym = item.dataset.symbol;
        document.getElementById("stock-search-input").value = sym;
        dropdown.classList.remove("active");
        analyzeStock(sym);
      });
    });
  } catch (err) {
    console.error("Autocomplete error:", err);
  }
}

async function loadMarketOverview() {
  try {
    const res = await fetch("/api/market/overview");
    const data = await res.json();
    const container = document.getElementById("benchmark-marquee");
    if (!container || !data.indices) return;

    container.innerHTML = data.indices.map(idx => {
      const isUp = idx.change >= 0;
      const cls = isUp ? "text-bullish" : "text-bearish";
      const sign = isUp ? "+" : "";
      return `
        <div class="benchmark-chip">
          <span style="font-weight: 700;">${idx.name}:</span>
          <span>${idx.currency_symbol}${idx.price.toLocaleString()}</span>
          <span class="${cls}">(${sign}${idx.change_pct}%)</span>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Market overview error:", err);
  }
}

async function analyzeStock(symbol) {
  const loading = document.getElementById("dashboard-loading");
  const dashboard = document.getElementById("analysis-dashboard");
  const analyzeBtn = document.getElementById("btn-analyze-stock");

  currentSymbol = symbol.split(".")[0].toUpperCase();
  window.currentSymbol = currentSymbol;

  loading.classList.add("active");
  dashboard.classList.remove("active");
  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = `<span class="loading-spinner"></span> Analyzing...`;

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol: symbol, demo: isDemoMode })
    });

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    
    window.currentStockData = data;
    window.lastTechnicals = data.technicals;
    window.lastCurrency = data.currency_symbol;

    renderDashboard(data);

    loading.classList.remove("active");
    dashboard.classList.add("active");
    
    // Render Chart
    setTimeout(() => {
      chartManager.renderData(data.candles, data.technicals, data.currency_symbol);
    }, 50);

  } catch (err) {
    console.error("Analysis failed:", err);
    loading.classList.remove("active");
    alert(`Could not analyze stock "${symbol}". Error: ${err.message}. Try switching to Demo Mode for sample testing.`);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = `Analyze Stock`;
  }
}

function renderDashboard(data) {
  const pa = data.price_action;
  const outlook = data.ai_outlook;
  const tech = data.technicals;
  const fund = data.fundamentals;
  const sent = data.sentiment;
  const risk = data.risk_analysis;
  const curr = data.currency_symbol || "₹";

  // 1. Stock Header Bar
  document.getElementById("stock-name").textContent = data.name;
  document.getElementById("stock-ticker").textContent = data.ticker;
  document.getElementById("stock-avatar-text").textContent = data.symbol.slice(0, 3);
  
  const sourcePill = document.getElementById("stock-source-pill");
  sourcePill.textContent = data.is_demo ? "● Simulated Demo Data" : "● Live Exchange Data";
  sourcePill.className = `stock-source-pill ${data.is_demo ? "source-demo" : "source-live"}`;

  document.getElementById("data-updated-time").textContent = `Data updated: ${data.updated_at}`;

  updateWatchlistButtonState(watchlistManager.has(currentSymbol));

  // 2. Top Metric Cards
  const isUp = pa.day_change >= 0;
  const sign = isUp ? "+" : "";
  const chgColor = isUp ? "var(--bullish)" : "var(--bearish)";

  document.getElementById("metric-price").textContent = `${curr}${pa.current_price.toLocaleString()}`;
  document.getElementById("metric-change").innerHTML = `
    <span style="color: ${chgColor};">${sign}${curr}${pa.day_change} (${sign}${pa.day_change_pct}%)</span>
  `;
  const metricChangeMain = document.getElementById("metric-change-main");
  if (metricChangeMain) {
    metricChangeMain.innerHTML = `<span style="color: ${chgColor};">${sign}${pa.day_change_pct}%</span>`;
  }

  // Market Trend
  document.getElementById("metric-trend").textContent = tech.summary.trend_direction;
  document.getElementById("metric-trend-sub").textContent = tech.summary.trend_strength;

  // AI Outlook
  const outlookEl = document.getElementById("metric-outlook");
  outlookEl.textContent = outlook.outlook;
  outlookEl.className = `outlook-badge outlook-${outlook.outlook.toLowerCase().replace(/\s+/g, '-')}`;

  // Confidence
  document.getElementById("metric-confidence").textContent = `${outlook.confidence_pct}%`;
  document.getElementById("metric-confidence-bar").style.width = `${outlook.confidence_pct}%`;

  // 3. AI Market Outlook Card & Why? Factors
  const heroOutlook = document.getElementById("hero-ai-outlook");
  heroOutlook.textContent = outlook.outlook;
  heroOutlook.className = `outlook-badge outlook-${outlook.outlook.toLowerCase().replace(/\s+/g, '-')}`;

  const dirArrow = outlook.potential_direction === "UPWARD" ? "▲" : (outlook.potential_direction === "DOWNWARD" ? "▼" : "◀▶");
  const dirColor = outlook.potential_direction === "UPWARD" ? "var(--bullish)" : (outlook.potential_direction === "DOWNWARD" ? "var(--bearish)" : "var(--neutral)");
  document.getElementById("hero-direction").innerHTML = `
    <span class="direction-arrow" style="color: ${dirColor};">${dirArrow}</span>
    <span style="color: ${dirColor};">${outlook.potential_direction}</span>
  `;

  document.getElementById("hero-confidence-val").textContent = `${outlook.confidence_pct}%`;
  document.getElementById("hero-confidence-fill").style.width = `${outlook.confidence_pct}%`;

  // Why Factors List
  const whyList = document.getElementById("why-factors-list");
  whyList.innerHTML = outlook.factors.map(f => {
    const icon = f.type === "positive" ? `<span class="why-icon-pos">✓</span>` :
                 f.type === "caution" ? `<span class="why-icon-caution">⚠</span>` :
                 `<span class="why-icon-neg">✕</span>`;
    return `<li class="why-item">${icon} <span>${f.text}</span></li>`;
  }).join("");

  document.getElementById("narrative-summary-text").textContent = outlook.summary;

  // Multi-Factor Score Chips
  const scores = data.scores;
  document.getElementById("score-technical").textContent = `${scores.technical_score}/100`;
  document.getElementById("score-fundamental").textContent = `${scores.fundamental_score}/100`;
  document.getElementById("score-momentum").textContent = `${scores.momentum_score}/100`;
  document.getElementById("score-sentiment").textContent = `${scores.sentiment_score}/100`;
  document.getElementById("score-risk").textContent = `${scores.risk_score}/100`;

  // 4. Price Levels Analysis Card
  const sr = tech.support_resistance;
  document.getElementById("lvl-current-price").textContent = `${curr}${pa.current_price.toLocaleString()}`;
  document.getElementById("lvl-imm-support").textContent = `${curr}${sr.immediate_support.toLocaleString()}`;
  document.getElementById("lvl-imm-support-dist").textContent = `-${sr.dist_to_support_pct}% below price`;
  document.getElementById("lvl-strong-support").textContent = `${curr}${sr.strong_support.toLocaleString()}`;
  
  document.getElementById("lvl-imm-res").textContent = `${curr}${sr.immediate_resistance.toLocaleString()}`;
  document.getElementById("lvl-imm-res-dist").textContent = `+${sr.dist_to_resistance_pct}% above price`;
  document.getElementById("lvl-strong-res").textContent = `${curr}${sr.strong_resistance.toLocaleString()}`;

  document.getElementById("lvl-52w-high").textContent = `${curr}${pa.fifty_two_week_high.toLocaleString()}`;
  document.getElementById("lvl-52w-low").textContent = `${curr}${pa.fifty_two_week_low.toLocaleString()}`;

  // 5. Technical Indicators Grid
  // RSI
  document.getElementById("tech-rsi-val").textContent = tech.rsi.value;
  document.getElementById("tech-rsi-status").textContent = tech.rsi.status;
  document.getElementById("tech-rsi-desc").textContent = tech.rsi.interpretation;

  // MACD
  document.getElementById("tech-macd-val").textContent = tech.macd.macd_line;
  document.getElementById("tech-macd-signal").textContent = tech.macd.signal_line;
  document.getElementById("tech-macd-hist").textContent = tech.macd.histogram;
  document.getElementById("tech-macd-status").textContent = tech.macd.status;

  // Moving Averages
  const ma = tech.moving_averages;
  document.getElementById("tech-sma-20").textContent = ma.sma_20 ? `${curr}${ma.sma_20}` : "N/A";
  document.getElementById("tech-sma-50").textContent = ma.sma_50 ? `${curr}${ma.sma_50}` : "N/A";
  document.getElementById("tech-sma-200").textContent = ma.sma_200 ? `${curr}${ma.sma_200}` : "N/A";
  document.getElementById("tech-ema-9").textContent = `${curr}${ma.ema_9}`;
  document.getElementById("tech-cross-signal").textContent = tech.summary.cross_signal;

  // Bollinger Bands
  const bb = tech.bollinger_bands;
  document.getElementById("tech-bb-upper").textContent = `${curr}${bb.upper}`;
  document.getElementById("tech-bb-mid").textContent = `${curr}${bb.middle}`;
  document.getElementById("tech-bb-lower").textContent = `${curr}${bb.lower}`;
  document.getElementById("tech-bb-bandwidth").textContent = `${bb.bandwidth_pct}%`;
  document.getElementById("tech-bb-status").textContent = bb.status;

  // Volume
  const vol = tech.volume;
  document.getElementById("tech-vol-current").textContent = vol.current_volume.toLocaleString();
  document.getElementById("tech-vol-avg").textContent = vol.average_volume_20.toLocaleString();
  document.getElementById("tech-vol-ratio").textContent = `${vol.volume_ratio}x`;
  document.getElementById("tech-vol-status").textContent = vol.status;

  // Breakout Signal
  document.getElementById("tech-breakout-signal").textContent = tech.summary.breakout_signal;

  // 6. Fundamental Analysis Grid
  document.getElementById("fund-mcap").textContent = fund.market_cap_formatted;
  document.getElementById("fund-pe").textContent = fund.pe_ratio !== null ? `${fund.pe_ratio}x` : "N/A";
  document.getElementById("fund-pe-status").textContent = fund.pe_status;
  document.getElementById("fund-pb").textContent = fund.pb_ratio !== null ? `${fund.pb_ratio}x` : "N/A";
  document.getElementById("fund-eps").textContent = fund.eps !== null ? `${curr}${fund.eps}` : "N/A";
  document.getElementById("fund-roe").textContent = fund.roe_pct !== null ? `${fund.roe_pct}%` : "N/A";
  document.getElementById("fund-roe-status").textContent = fund.roe_status;
  document.getElementById("fund-de").textContent = fund.debt_to_equity !== null ? `${fund.debt_to_equity}%` : "N/A";
  document.getElementById("fund-de-status").textContent = fund.debt_status;
  document.getElementById("fund-rev-growth").textContent = fund.revenue_growth_pct !== null ? `${fund.revenue_growth_pct}%` : "N/A";
  document.getElementById("fund-profit-growth").textContent = fund.profit_growth_pct !== null ? `${fund.profit_growth_pct}%` : "N/A";
  document.getElementById("fund-div-yield").textContent = fund.dividend_yield_pct !== null ? `${fund.dividend_yield_pct}%` : "N/A";
  document.getElementById("fund-promoter-holding").textContent = fund.promoter_holding_pct !== null ? `${fund.promoter_holding_pct}%` : "Not Disclosed";
  document.getElementById("fund-inst-holding").textContent = fund.institutional_holding_pct !== null ? `${fund.institutional_holding_pct}%` : "Not Disclosed";
  document.getElementById("fund-health").textContent = fund.health;

  // 7. Scenarios
  const sc = data.scenarios;
  document.getElementById("scenario-bull-trigger").textContent = sc.bullish.trigger;
  document.getElementById("scenario-bull-targets").textContent = sc.bullish.target_levels;
  document.getElementById("scenario-bull-cond").textContent = sc.bullish.conditions;
  document.getElementById("scenario-bull-inval").textContent = sc.bullish.invalidation;

  document.getElementById("scenario-neut-trigger").textContent = sc.neutral.trigger;
  document.getElementById("scenario-neut-targets").textContent = sc.neutral.target_levels;
  document.getElementById("scenario-neut-cond").textContent = sc.neutral.conditions;

  document.getElementById("scenario-bear-trigger").textContent = sc.bearish.trigger;
  document.getElementById("scenario-bear-targets").textContent = sc.bearish.target_levels;
  document.getElementById("scenario-bear-cond").textContent = sc.bearish.conditions;
  document.getElementById("scenario-bear-inval").textContent = sc.bearish.invalidation;

  // 8. Multi-Timeframe Analysis Matrix
  const tfContainer = document.getElementById("timeframes-container");
  tfContainer.innerHTML = data.timeframe_analysis.map(tf => {
    const dirCls = tf.direction === "UPWARD" ? "text-bullish" : (tf.direction === "DOWNWARD" ? "text-bearish" : "text-neutral");
    return `
      <div class="tf-card glass-card">
        <div class="tf-header">
          <span class="tf-title">${tf.timeframe}</span>
          <span class="tf-badge ${dirCls}">${tf.direction} (${tf.confidence_pct}%)</span>
        </div>
        <div style="font-size: 0.8rem; margin-bottom: 0.4rem; color: var(--text-muted);">${tf.label}</div>
        <div style="font-size: 0.82rem; margin-bottom: 0.4rem;"><strong>Key Levels:</strong> ${tf.key_levels}</div>
        <div style="font-size: 0.82rem; margin-bottom: 0.4rem;"><strong>Main Drivers:</strong> ${tf.main_reasons}</div>
        <div style="font-size: 0.8rem; color: var(--neutral);"><strong>Risks:</strong> ${tf.risks}</div>
      </div>
    `;
  }).join("");

  // 9. Risk Factors
  document.getElementById("risk-overall-level").textContent = `${risk.risk_level} (Score: ${risk.overall_risk_score}/100)`;
  const riskList = document.getElementById("risk-factors-container");
  riskList.innerHTML = risk.risk_factors.map(r => {
    const pillCls = r.level === "High" ? "risk-pill-high" : (r.level === "Medium" ? "risk-pill-med" : "risk-pill-low");
    return `
      <div class="risk-item">
        <div class="risk-item-head">
          <span class="risk-item-title">${r.title}</span>
          <span class="${pillCls}">${r.level} Risk</span>
        </div>
        <div style="font-size: 0.78rem; color: var(--text-secondary);">${r.desc}</div>
      </div>
    `;
  }).join("");

  // 10. News & Sentiment
  document.getElementById("sentiment-label").textContent = `${sent.label} (${sent.score}/100)`;
  document.getElementById("sentiment-inst-activity").textContent = sent.institutional_activity;
  document.getElementById("sentiment-summary").textContent = sent.summary;

  const newsList = document.getElementById("news-container");
  if (sent.news && sent.news.length > 0) {
    newsList.innerHTML = sent.news.map(n => {
      const sentBadgeCls = n.sentiment === "positive" ? "badge-bull" : (n.sentiment === "negative" ? "badge-bear" : "badge-neut");
      return `
        <div class="news-card">
          <a href="${n.link}" target="_blank" rel="noopener noreferrer" class="news-title">${n.title}</a>
          <div class="news-footer">
            <span>${n.publisher} • ${n.time}</span>
            <span class="tech-status-badge ${sentBadgeCls}">${n.sentiment.toUpperCase()}</span>
          </div>
        </div>
      `;
    }).join("");
  } else {
    newsList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem;">No recent news items found for this ticker.</div>`;
  }
}

function updateWatchlistButtonState(isInWatchlist) {
  const btn = document.getElementById("btn-add-watchlist");
  if (!btn) return;
  if (isInWatchlist) {
    btn.classList.add("active");
    btn.innerHTML = `★ In Watchlist`;
  } else {
    btn.classList.remove("active");
    btn.innerHTML = `☆ Save to Watchlist`;
  }
}
