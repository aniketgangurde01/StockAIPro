# StockAI - AI-Powered Stock Analysis Platform

A modern, professional financial analytics web application designed for the Indian stock market (NSE/BSE) and global equities. StockAI synthesizes real-time and historical market data into probability-based analytical classifications, technical indicators, fundamental health scores, news sentiment, price scenarios, and multi-timeframe outlooks.

---

## 🌟 Key Features

1. **Intelligent Stock Search**:
   - Accepts company names, NSE symbols (`RELIANCE`), BSE codes (`500325`), or global tickers (`AAPL`, `MSFT`).
   - Dynamic search-as-you-type autocomplete with popular Indian stocks quick chips.

2. **AI Market Outlook Engine**:
   - Classifications: `BULLISH`, `MODERATELY BULLISH`, `NEUTRAL`, `MODERATELY BEARISH`, `BEARISH`.
   - Direction: `UPWARD`, `SIDEWAYS`, `DOWNWARD`.
   - Calibrated Analytical Confidence % (model classification confidence, clearly framed as non-guaranteed).
   - Itemized **"Why?"** breakdown highlighting positive catalysts (`✓`) and cautionary signals (`⚠`).
   - Narrative analysis summary card.

3. **Interactive TradingView Chart**:
   - Candlestick price chart with real OHLCV data.
   - Toggleable overlays: MA20 (blue), MA50 (amber), MA200 (purple), Volume histogram (green/red).
   - Automatic Support & Resistance horizontal price lines.
   - Timeframe filters: 5D, 1M, 6M, 1Y.

4. **Multi-Factor Scoring (0–100)**:
   - Technical Score
   - Fundamental Score
   - Momentum Score
   - Sentiment Score
   - Risk Score

5. **Price Levels & Pivots**:
   - Current Price, Immediate Support, Strong Support, Immediate Resistance, Strong Resistance, 52-Week Range with % distances.

6. **Technical Indicators**:
   - RSI (14) with overbought/oversold status.
   - MACD (12, 26, 9) with Signal line, Histogram, and Crossover signals.
   - Moving Averages (SMA 20, 50, 200, EMA 9, 21, Golden/Death cross).
   - Bollinger Bands (20, 2) with Upper, Middle, Lower, Bandwidth %, %B.
   - Volume Analysis (Current volume, 20-day Average, Volume surge ratio).
   - Breakout and Breakdown detection.
   - Hover tooltips explaining each indicator in plain English.

7. **Fundamental Health & Valuation**:
   - Market Capitalization (formatted in ₹ Lakh Cr / ₹ Cr for Indian equities).
   - P/E (Trailing & Forward), P/B, EPS, ROE, ROCE, Debt-to-Equity.
   - Revenue Growth (YoY), Profit Growth (YoY), Dividend Yield.
   - Promoter Holding % & Institutional Holding % (FII / DII).

8. **Hypothetical Price Scenarios**:
   - Bullish Scenario (Catalyst trigger, target levels, supporting conditions, invalidation).
   - Neutral / Sideways Scenario (Range bounds, equilibrium pivot, conditions).
   - Bearish Scenario (Breakdown trigger, structural floor, invalidation).

9. **Multi-Timeframe Analysis Matrix**:
   - Intraday (Today's session)
   - Short Term (1–5 trading days)
   - Swing (1–4 weeks)
   - Medium Term (1–6 months)
   - Each with Direction, Confidence %, Key Levels, Main Reasons, and Risks.

10. **Watchlist & Demo Mode**:
    - LocalStorage-backed watchlist manager with slide-over drawer.
    - Offline Demo Mode switch with pre-calibrated sample data for RELIANCE, TCS, INFY, HDFCBANK, TATAMOTORS.
    - Dark and Light mode toggle.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ (Tested with Python 3.14)

### Running the Application

1. Open PowerShell / Command Prompt in the project folder:
   ```bash
   cd C:\Users\APMC\.gemini\antigravity\scratch\stockai-platform
   ```

2. Start the server:
   ```bash
   py main.py
   ```

3. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

---

## 📁 Project Architecture

```
stockai-platform/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # FastAPI REST endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── market_data.py        # yfinance fetcher, ticker normalizer & demo datasets
│   │   ├── technical_engine.py   # RSI, MACD, MAs, Bollinger, Volume & Pivots
│   │   ├── fundamental_engine.py # P/E, P/B, EPS, ROE, ROCE, D/E, Holdings
│   │   ├── sentiment_engine.py   # News NLP sentiment analysis
│   │   └── ai_analyzer.py        # Multi-factor scoring, Outlook, Scenarios & Timeframes
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css        # Dark glassmorphism trading dashboard styling
│   │   ├── js/
│   │   │   ├── app.js            # Main application controller
│   │   │   ├── chart.js          # Lightweight Charts integration
│   │   │   ├── watchlist.js      # LocalStorage watchlist manager
│   │   │   └── lightweight-charts.js # Cached TradingView canvas charting library
│   │   └── index.html            # Single-page dashboard UI
│   └── config.py                 # Popular Indian stocks registry & disclaimer
├── tests/
│   └── test_engine.py            # Unit and integration test suite
├── main.py                       # FastAPI entrypoint & static mount
└── requirements.txt              # Dependency specifications
```

---

## ⚖️ Legal & Educational Disclaimer

> **This analysis is for educational and informational purposes only.** It is not financial advice, investment recommendation, or solicitation. It does not guarantee future stock price movements. Market conditions can change rapidly. Always conduct your own independent research and consult a certified financial advisor before making investment decisions.
