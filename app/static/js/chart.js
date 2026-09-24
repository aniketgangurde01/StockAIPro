/**
 * StockAI - Interactive Financial Charting Module
 * Powered by TradingView Lightweight Charts (v4.x)
 */

class StockChartManager {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.chart = null;
    this.candleSeries = null;
    this.volumeSeries = null;
    this.ma20Series = null;
    this.ma50Series = null;
    this.ma200Series = null;
    
    this.rawCandles = [];
    this.currentPeriod = "1Y";
    this.showMA20 = true;
    this.showMA50 = true;
    this.showMA200 = true;
    this.showVolume = true;

    this.supportLines = [];
    this.resistanceLines = [];

    window.addEventListener("resize", () => this.handleResize());
  }

  handleResize() {
    if (this.chart && this.container) {
      this.chart.applyOptions({
        width: this.container.clientWidth,
        height: this.container.clientHeight || 480
      });
    }
  }

  initChart() {
    if (this.chart) {
      this.chart.remove();
      this.chart = null;
    }

    if (!window.LightweightCharts) {
      console.error("LightweightCharts library not loaded");
      return;
    }

    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    const bg = isLight ? "#ffffff" : "#0d121d";
    const textColor = isLight ? "#475569" : "#94a3b8";
    const gridColor = isLight ? "rgba(0, 0, 0, 0.05)" : "rgba(255, 255, 255, 0.04)";

    this.chart = window.LightweightCharts.createChart(this.container, {
      width: this.container.clientWidth,
      height: this.container.clientHeight || 480,
      layout: {
        background: { type: "solid", color: bg },
        textColor: textColor,
        fontFamily: "'Inter', -apple-system, sans-serif",
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      crosshair: {
        mode: window.LightweightCharts.CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: gridColor,
        scaleMargins: {
          top: 0.1,
          bottom: 0.22, // Space for volume subchart at bottom
        },
      },
      timeScale: {
        borderColor: gridColor,
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // 1. Candlestick Series
    this.candleSeries = this.chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#ef4444",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    // 2. Volume Series (histogram on bottom)
    this.volumeSeries = this.chart.addHistogramSeries({
      color: "#3b82f6",
      priceFormat: { type: "volume" },
      priceScaleId: "", // overlay
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // 3. Moving Average Series Overlays
    this.ma20Series = this.chart.addLineSeries({
      color: "#38bdf8",
      lineWidth: 2,
      title: "MA 20",
    });

    this.ma50Series = this.chart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 2,
      title: "MA 50",
    });

    this.ma200Series = this.chart.addLineSeries({
      color: "#a855f7",
      lineWidth: 2,
      title: "MA 200",
    });
  }

  renderData(candles, technicals, currencySymbol = "₹") {
    if (!candles || candles.length === 0) return;
    this.rawCandles = candles;
    this.initChart();

    // Format candlestick data
    const formattedCandles = candles.map(c => ({
      time: c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    // Volume data colored by candle direction
    const formattedVolume = candles.map(c => ({
      time: c.time,
      value: c.volume,
      color: c.close >= c.open ? "rgba(16, 185, 129, 0.45)" : "rgba(239, 68, 68, 0.45)",
    }));

    this.candleSeries.setData(formattedCandles);
    this.volumeSeries.setData(formattedVolume);

    // Compute moving averages dynamically across the candles
    const ma20Data = this.calculateSMA(candles, 20);
    const ma50Data = this.calculateSMA(candles, 50);
    const ma200Data = this.calculateSMA(candles, 200);

    if (this.showMA20) this.ma20Series.setData(ma20Data);
    if (this.showMA50) this.ma50Series.setData(ma50Data);
    if (this.showMA200) this.ma200Series.setData(ma200Data);

    // Add Support & Resistance horizontal lines if provided
    if (technicals && technicals.support_resistance) {
      const sr = technicals.support_resistance;
      this.drawPriceLevel(sr.immediate_resistance, "Imm Resistance", "#ef4444", currencySymbol);
      this.drawPriceLevel(sr.strong_resistance, "Strong Resistance", "#dc2626", currencySymbol);
      this.drawPriceLevel(sr.immediate_support, "Imm Support", "#10b981", currencySymbol);
      this.drawPriceLevel(sr.strong_support, "Strong Support", "#059669", currencySymbol);
    }

    this.chart.timeScale().fitContent();
  }

  drawPriceLevel(price, title, color, curr) {
    if (!price || !this.candleSeries) return;
    this.candleSeries.createPriceLine({
      price: price,
      color: color,
      lineWidth: 1,
      lineStyle: window.LightweightCharts.LineStyle.Dotted,
      axisLabelVisible: true,
      title: `${title} (${curr}${price})`,
    });
  }

  calculateSMA(candles, period) {
    const result = [];
    for (let i = period - 1; i < candles.length; i++) {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += candles[i - j].close;
      }
      result.push({
        time: candles[i].time,
        value: Number((sum / period).toFixed(2))
      });
    }
    return result;
  }

  filterPeriod(period) {
    if (!this.rawCandles || this.rawCandles.length === 0 || !this.chart) return;
    this.currentPeriod = period;

    let bars = this.rawCandles.length;
    if (period === "5D") bars = Math.min(5, this.rawCandles.length);
    else if (period === "1M") bars = Math.min(22, this.rawCandles.length);
    else if (period === "6M") bars = Math.min(125, this.rawCandles.length);
    else if (period === "1Y") bars = this.rawCandles.length;

    const slice = this.rawCandles.slice(-bars);
    if (slice.length > 0) {
      this.chart.timeScale().setVisibleRange({
        from: slice[0].time,
        to: slice[slice.length - 1].time
      });
    }
  }

  toggleOverlay(overlayName) {
    if (overlayName === "ma20") {
      this.showMA20 = !this.showMA20;
      this.ma20Series.applyOptions({ visible: this.showMA20 });
      return this.showMA20;
    }
    if (overlayName === "ma50") {
      this.showMA50 = !this.showMA50;
      this.ma50Series.applyOptions({ visible: this.showMA50 });
      return this.showMA50;
    }
    if (overlayName === "ma200") {
      this.showMA200 = !this.showMA200;
      this.ma200Series.applyOptions({ visible: this.showMA200 });
      return this.showMA200;
    }
    if (overlayName === "vol") {
      this.showVolume = !this.showVolume;
      this.volumeSeries.applyOptions({ visible: this.showVolume });
      return this.showVolume;
    }
    return false;
  }
}

window.StockChartManager = StockChartManager;
