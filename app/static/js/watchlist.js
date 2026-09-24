/**
 * StockAI - Watchlist Manager
 * Persists watchlist in localStorage and manages sidebar drawer
 */

class WatchlistManager {
  constructor(storageKey = "stockai_watchlist") {
    this.storageKey = storageKey;
    this.watchlist = this.load();
  }

  load() {
    try {
      const data = localStorage.getItem(this.storageKey);
      if (data) return JSON.parse(data);
    } catch (e) {
      console.error("Failed to load watchlist from localStorage", e);
    }
    // Default initial watchlist
    return [
      { symbol: "RELIANCE", name: "Reliance Industries Ltd" },
      { symbol: "TCS", name: "Tata Consultancy Services" },
      { symbol: "HDFCBANK", name: "HDFC Bank Ltd" },
      { symbol: "TATAMOTORS", name: "Tata Motors Ltd" }
    ];
  }

  save() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.watchlist));
      this.updateBadge();
    } catch (e) {
      console.error("Failed to save watchlist", e);
    }
  }

  has(symbol) {
    const clean = symbol.split(".")[0].toUpperCase();
    return this.watchlist.some(item => item.symbol.toUpperCase() === clean);
  }

  add(symbol, name) {
    const clean = symbol.split(".")[0].toUpperCase();
    if (!this.has(clean)) {
      this.watchlist.unshift({ symbol: clean, name: name || clean });
      this.save();
    }
  }

  remove(symbol) {
    const clean = symbol.split(".")[0].toUpperCase();
    this.watchlist = this.watchlist.filter(item => item.symbol.toUpperCase() !== clean);
    this.save();
  }

  toggle(symbol, name) {
    if (this.has(symbol)) {
      this.remove(symbol);
      return false;
    } else {
      this.add(symbol, name);
      return true;
    }
  }

  updateBadge() {
    const badge = document.getElementById("watchlist-count-badge");
    if (badge) {
      badge.textContent = this.watchlist.length;
    }
  }

  render(containerId, onSelect) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (this.watchlist.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 2rem 1rem;">
          <p>Your watchlist is empty.</p>
          <p style="font-size: 0.8rem; margin-top: 0.5rem;">Click the "Save to Watchlist" button on any stock to monitor it here.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = this.watchlist.map(item => `
      <div class="watchlist-card" data-symbol="${item.symbol}">
        <div>
          <div style="font-weight: 700; color: var(--text-primary);">${item.symbol}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted); max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
            ${item.name}
          </div>
        </div>
        <button class="btn-remove-wl" data-remove="${item.symbol}" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; padding: 4px;" title="Remove from watchlist">
          ✕
        </button>
      </div>
    `).join("");

    // Bind clicks
    container.querySelectorAll(".watchlist-card").forEach(el => {
      el.addEventListener("click", (e) => {
        if (e.target.dataset.remove) {
          e.stopPropagation();
          this.remove(e.target.dataset.remove);
          this.render(containerId, onSelect);
          const currentBtn = document.getElementById("btn-add-watchlist");
          if (currentBtn && window.currentSymbol === e.target.dataset.remove) {
            currentBtn.classList.remove("active");
            currentBtn.innerHTML = `★ Save to Watchlist`;
          }
          return;
        }
        const sym = el.dataset.symbol;
        if (onSelect) onSelect(sym);
      });
    });
  }
}

window.WatchlistManager = WatchlistManager;
