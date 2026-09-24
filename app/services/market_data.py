"""
Market Data Service - Handles Live Data Ingestion (NSE/BSE/Global) and Fallbacks
"""
import time
import math
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
import yfinance as yf

from app.config import POPULAR_INDIAN_STOCKS, INDIAN_SYMBOL_MAP, BENCHMARK_INDICES

# In-memory quote & overview cache to avoid redundant network round-trips
_CACHE: Dict[str, Tuple[float, Any]] = {}
_OVERVIEW_CACHE: Tuple[float, List[Dict[str, Any]]] = (0.0, [])
CACHE_TTL_SECONDS = 600  # 10 minutes quote cache
OVERVIEW_TTL_SECONDS = 600  # 10 minutes market overview cache


def warmup_cache():
    """
    Background cache pre-warmer so that the top benchmark indices and popular stocks
    return instantly (< 5ms) when the user accesses the website.
    """
    try:
        MarketDataService.get_market_overview()
        for sym in ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]:
            MarketDataService.get_stock_data(sym)
    except Exception:
        pass


def normalize_symbol(query: str) -> Tuple[str, str, str]:
    """
    Normalizes a user query into:
    (clean_symbol, yahoo_ticker, display_name)
    Example:
    'RELIANCE' -> ('RELIANCE', 'RELIANCE.NS', 'Reliance Industries Ltd')
    '^NSEI' -> ('^NSEI', '^NSEI', 'NIFTY 50')
    '^NSEI.NS' -> ('^NSEI', '^NSEI', 'NIFTY 50')
    'AAPL' -> ('AAPL', 'AAPL', 'Apple Inc.')
    """
    q = query.strip().upper()
    
    # Standard index names lookup
    index_names = {
        "^NSEI": "NIFTY 50",
        "^BSESN": "BSE SENSEX",
        "^NSEBANK": "BANK NIFTY",
        "^CNXIT": "NIFTY IT",
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones Industrial Average",
        "^IXIC": "NASDAQ Composite"
    }

    # Index aliases and variations (with or without caret, with or without suffix)
    index_aliases = {
        "NIFTY": "^NSEI",
        "NIFTY 50": "^NSEI",
        "NIFTY50": "^NSEI",
        "NSEI": "^NSEI",
        "SENSEX": "^BSESN",
        "BSE SENSEX": "^BSESN",
        "BSESN": "^BSESN",
        "BANKNIFTY": "^NSEBANK",
        "BANK NIFTY": "^NSEBANK",
        "NSEBANK": "^NSEBANK",
        "S&P 500": "^GSPC",
        "SP500": "^GSPC",
        "SPX": "^GSPC",
        "GSPC": "^GSPC"
    }

    # 1. Handle index queries & strip accidental .NS / .BO suffixes from index tickers
    q_base = q.split(".")[0]
    if q_base.startswith("^"):
        idx_sym = q_base
        return idx_sym, idx_sym, index_names.get(idx_sym, idx_sym)

    if q in index_aliases:
        idx_sym = index_aliases[q]
        return idx_sym, idx_sym, index_names.get(idx_sym, idx_sym)

    if q_base in index_aliases:
        idx_sym = index_aliases[q_base]
        return idx_sym, idx_sym, index_names.get(idx_sym, idx_sym)

    # 2. Direct match in registered Indian stocks
    for item in POPULAR_INDIAN_STOCKS:
        if q == item["symbol"].upper():
            return item["symbol"], item["nse"], item["name"]
        if q == item["nse"].upper():
            return item["symbol"], item["nse"], item["name"]
        if q == item["bse"].upper() or q == item["bse"].split(".")[0]:
            return item["symbol"], item["bse"], f"{item['name']} (BSE)"
        if q.lower() in item["name"].lower():
            return item["symbol"], item["nse"], item["name"]

    # 3. Check if already has exchange suffix (.NS, .BO, etc.)
    if "." in q:
        clean = q.split(".")[0]
        return clean, q, clean

    # 4. Standard global tickers without exchange suffix
    GLOBAL_TICKERS = {"AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "SPY"}
    if q in GLOBAL_TICKERS:
        return q, q, q
    
    # 5. Otherwise assume standard Indian NSE ticker
    return q, f"{q}.NS", q


def get_demo_historical_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """
    Generates realistic synthetic historical OHLCV data for demo testing
    based on baseline parameters for popular stocks.
    """
    baselines = {
        "RELIANCE": {"base": 1250.0, "drift": 0.0003, "vol": 0.015, "name": "Reliance Industries Ltd"},
        "TCS": {"base": 4120.0, "drift": 0.0002, "vol": 0.012, "name": "Tata Consultancy Services Ltd"},
        "INFY": {"base": 1820.0, "drift": 0.0004, "vol": 0.016, "name": "Infosys Ltd"},
        "HDFCBANK": {"base": 1650.0, "drift": 0.0001, "vol": 0.014, "name": "HDFC Bank Ltd"},
        "TATAMOTORS": {"base": 960.0, "drift": 0.0006, "vol": 0.022, "name": "Tata Motors Ltd"},
        "^NSEI": {"base": 25800.0, "drift": 0.0003, "vol": 0.008, "name": "NIFTY 50"},
        "^BSESN": {"base": 84500.0, "drift": 0.0003, "vol": 0.008, "name": "BSE SENSEX"},
        "^NSEBANK": {"base": 53500.0, "drift": 0.0004, "vol": 0.011, "name": "BANK NIFTY"},
        "^GSPC": {"base": 5700.0, "drift": 0.0003, "vol": 0.009, "name": "S&P 500"},
    }
    
    clean_sym = symbol.split(".")[0].upper()
    cfg = baselines.get(clean_sym, {"base": 1000.0, "drift": 0.0002, "vol": 0.015, "name": symbol})
    
    days = 250 if period in ["1y", "max"] else 120 if period == "6mo" else 30
    dates = pd.date_range(end=datetime.now(timezone.utc), periods=days, freq='B')
    
    np.random.seed(abs(hash(clean_sym)) % 10000)
    returns = np.random.normal(cfg["drift"], cfg["vol"], days)
    # Add a slight realistic trend
    trend = np.linspace(0, 0.15, days)
    price_series = cfg["base"] * np.exp(np.cumsum(returns) + trend)
    
    records = []
    for i, date in enumerate(dates):
        close_p = float(price_series[i])
        daily_var = cfg["vol"] * 0.7
        high_p = close_p * (1 + abs(np.random.normal(0, daily_var)))
        low_p = close_p * (1 - abs(np.random.normal(0, daily_var)))
        open_p = (low_p + high_p) / 2 + np.random.normal(0, close_p * 0.003)
        vol = int(np.random.lognormal(14.5, 0.4))
        
        records.append({
            "Date": date,
            "Open": round(open_p, 2),
            "High": round(max(high_p, open_p, close_p), 2),
            "Low": round(min(low_p, open_p, close_p), 2),
            "Close": round(close_p, 2),
            "Volume": vol
        })
        
    df = pd.DataFrame(records)
    df.set_index("Date", inplace=True)
    return df


def get_demo_fundamentals(symbol: str) -> Dict[str, Any]:
    """Fallback realistic fundamentals for demo mode"""
    clean_sym = symbol.split(".")[0].upper()
    data = {
        "RELIANCE": {
            "market_cap": 16888525000000,
            "pe_ratio": 22.7,
            "forward_pe": 17.5,
            "pb_ratio": 1.87,
            "eps": 54.95,
            "roe": 0.092,
            "roce": 0.114,
            "debt_to_equity": 36.65,
            "revenue_growth": 0.297,
            "profit_growth": -0.224,
            "dividend_yield": 0.0048,
            "promoter_holding": 0.518,
            "institutional_holding": 0.281,
            "sector": "Energy & Petrochemicals",
            "industry": "Oil & Gas Refining & Marketing"
        },
        "TCS": {
            "market_cap": 14950000000000,
            "pe_ratio": 29.8,
            "forward_pe": 26.2,
            "pb_ratio": 13.5,
            "eps": 138.4,
            "roe": 0.495,
            "roce": 0.582,
            "debt_to_equity": 0.0,
            "revenue_growth": 0.068,
            "profit_growth": 0.084,
            "dividend_yield": 0.0135,
            "promoter_holding": 0.718,
            "institutional_holding": 0.225,
            "sector": "Information Technology",
            "industry": "IT Services & Consulting"
        },
        "INFY": {
            "market_cap": 7580000000000,
            "pe_ratio": 28.4,
            "forward_pe": 24.1,
            "pb_ratio": 8.7,
            "eps": 64.2,
            "roe": 0.318,
            "roce": 0.395,
            "debt_to_equity": 0.0,
            "revenue_growth": 0.052,
            "profit_growth": 0.067,
            "dividend_yield": 0.021,
            "promoter_holding": 0.148,
            "institutional_holding": 0.684,
            "sector": "Information Technology",
            "industry": "IT Services & Consulting"
        },
        "HDFCBANK": {
            "market_cap": 12550000000000,
            "pe_ratio": 18.2,
            "forward_pe": 16.4,
            "pb_ratio": 2.7,
            "eps": 90.6,
            "roe": 0.165,
            "roce": 0.142,
            "debt_to_equity": 85.0,
            "revenue_growth": 0.21,
            "profit_growth": 0.18,
            "dividend_yield": 0.0118,
            "promoter_holding": 0.0,
            "institutional_holding": 0.812,
            "sector": "Financial Services",
            "industry": "Private Banking"
        },
        "TATAMOTORS": {
            "market_cap": 3520000000000,
            "pe_ratio": 10.8,
            "forward_pe": 9.4,
            "pb_ratio": 3.8,
            "eps": 88.9,
            "roe": 0.384,
            "roce": 0.245,
            "debt_to_equity": 1.25,
            "revenue_growth": 0.142,
            "profit_growth": 0.725,
            "dividend_yield": 0.0062,
            "promoter_holding": 0.464,
            "institutional_holding": 0.362,
            "sector": "Automobile",
            "industry": "Passenger & Commercial Vehicles"
        }
    }
    
    return data.get(clean_sym, {
        "market_cap": None,
        "pe_ratio": None,
        "forward_pe": None,
        "pb_ratio": None,
        "eps": None,
        "roe": None,
        "roce": None,
        "debt_to_equity": None,
        "revenue_growth": None,
        "profit_growth": None,
        "dividend_yield": None,
        "promoter_holding": None,
        "institutional_holding": None,
        "sector": "General / Equity",
        "industry": "Diversified"
    })


def get_demo_news(symbol: str) -> List[Dict[str, Any]]:
    clean_sym = symbol.split(".")[0].upper()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    samples = {
        "RELIANCE": [
            {"title": "Reliance Retail expands store network with new omnichannel formats", "publisher": "Economic Times", "link": "#", "time": "2 hours ago", "sentiment": "positive"},
            {"title": "Jio Platforms reports steady subscriber growth in 5G expansion", "publisher": "LiveMint", "link": "#", "time": "5 hours ago", "sentiment": "positive"},
            {"title": "Crude oil volatility may impact gross refining margins this quarter", "publisher": "Business Standard", "link": "#", "time": "12 hours ago", "sentiment": "neutral"},
            {"title": "Reliance green energy giga-complex on track for phased commissioning", "publisher": "Financial Express", "link": "#", "time": "1 day ago", "sentiment": "positive"}
        ],
        "TCS": [
            {"title": "TCS bags multi-million pound digital transformation deal with UK insurer", "publisher": "Economic Times", "link": "#", "time": "3 hours ago", "sentiment": "positive"},
            {"title": "IT sector demand visibility: Analysts watch BFSI spend trends", "publisher": "LiveMint", "link": "#", "time": "6 hours ago", "sentiment": "neutral"},
            {"title": "TCS launches generative AI experience center for enterprise clients", "publisher": "CNBC-TV18", "link": "#", "time": "1 day ago", "sentiment": "positive"}
        ],
        "INFY": [
            {"title": "Infosys expands AI-first Topaz suite for global manufacturing clients", "publisher": "LiveMint", "link": "#", "time": "4 hours ago", "sentiment": "positive"},
            {"title": "Infosys signs long-term collaboration with European telco", "publisher": "Economic Times", "link": "#", "time": "8 hours ago", "sentiment": "positive"},
            {"title": "Wage revision and attrition trends stable in Q2", "publisher": "Financial Express", "link": "#", "time": "1 day ago", "sentiment": "neutral"}
        ],
        "HDFCBANK": [
            {"title": "HDFC Bank deposit accretion shows steady momentum post-merger", "publisher": "Economic Times", "link": "#", "time": "1 hour ago", "sentiment": "positive"},
            {"title": "RBI regulatory stance on unsecured credit remains key monitorable", "publisher": "Business Standard", "link": "#", "time": "7 hours ago", "sentiment": "neutral"},
            {"title": "Brokerages maintain buy rating on HDFC Bank on credit growth outlook", "publisher": "LiveMint", "link": "#", "time": "1 day ago", "sentiment": "positive"}
        ],
        "TATAMOTORS": [
            {"title": "Tata Motors EV sales witness double-digit uptick during festival season", "publisher": "LiveMint", "link": "#", "time": "3 hours ago", "sentiment": "positive"},
            {"title": "JLR order book remains resilient with strong Range Rover deliveries", "publisher": "Economic Times", "link": "#", "time": "5 hours ago", "sentiment": "positive"},
            {"title": "Commercial vehicle demand shows modest recovery in heavy freight", "publisher": "Financial Express", "link": "#", "time": "18 hours ago", "sentiment": "neutral"}
        ]
    }
    
    return samples.get(clean_sym, [
        {"title": f"Market analysis & quarterly outlook for {clean_sym}", "publisher": "Market Desk", "link": "#", "time": "4 hours ago", "sentiment": "neutral"},
        {"title": f"Institutional trading interest observed in {clean_sym}", "publisher": "Financial Wire", "link": "#", "time": "1 day ago", "sentiment": "neutral"}
    ])


class MarketDataService:
    @staticmethod
    def get_stock_data(query: str, force_demo: bool = False) -> Dict[str, Any]:
        """
        Unified fetcher that pulls quote, historical candles, fundamentals,
        and news. Falls back cleanly to demo dataset if network error or rate limit occurs.
        """
        clean_symbol, ticker_symbol, display_name = normalize_symbol(query)
        cache_key = f"{ticker_symbol}_{force_demo}"
        
        if not force_demo and cache_key in _CACHE:
            ts, val = _CACHE[cache_key]
            if time.time() - ts < CACHE_TTL_SECONDS:
                return val

        is_demo = force_demo
        hist_df: Optional[pd.DataFrame] = None
        info_dict: Dict[str, Any] = {}
        news_items: List[Dict[str, Any]] = []
        error_msg: Optional[str] = None
        
        if not force_demo:
            try:
                t = yf.Ticker(ticker_symbol)
                
                # If it's an index (^...), only fetch historical candles (no fundamentals or news)
                if ticker_symbol.startswith("^"):
                    hist_df = t.history(period="1y", interval="1d")
                    info_dict = {"shortName": display_name}
                    news_items = []
                else:
                    # For equities, fetch history, info, and news in parallel threads
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        fut_hist = executor.submit(lambda: t.history(period="1y", interval="1d"))
                        fut_info = executor.submit(lambda: t.info or {})
                        fut_news = executor.submit(lambda: t.news or [])

                        hist_df = fut_hist.result(timeout=4.0)
                        try:
                            info_dict = fut_info.result(timeout=2.0) or {}
                        except Exception:
                            info_dict = {}
                        try:
                            raw_news = fut_news.result(timeout=1.5) or []
                        except Exception:
                            raw_news = []

                    # If NSE symbol fails or is empty, try BSE symbol (strictly for equities, never indices)
                    if (hist_df is None or hist_df.empty) and ticker_symbol.endswith(".NS") and not clean_symbol.startswith("^"):
                        bse_candidate = f"{clean_symbol}.BO"
                        t_bse = yf.Ticker(bse_candidate)
                        hist_bse = t_bse.history(period="1y", interval="1d")
                        if hist_bse is not None and not hist_bse.empty:
                            hist_df = hist_bse
                            ticker_symbol = bse_candidate

                    # Parse news items
                    for n in raw_news[:8]:
                        content = n.get("content", {}) if isinstance(n.get("content"), dict) else n
                        title = content.get("title") or n.get("title", "")
                        provider = content.get("provider", {})
                        pub_name = provider.get("displayName") if isinstance(provider, dict) else n.get("publisher", "Market News")
                        canonical = content.get("canonicalUrl", {})
                        link = canonical.get("url") if isinstance(canonical, dict) else n.get("link", "#")
                        pub_time = content.get("pubDate") or n.get("providerPublishTime")
                        time_str = "Recent"
                        if pub_time:
                            if isinstance(pub_time, (int, float)):
                                time_str = datetime.fromtimestamp(pub_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
                            else:
                                time_str = str(pub_time)[:16].replace("T", " ")
                        if title:
                            news_items.append({
                                "title": title,
                                "publisher": pub_name,
                                "link": link,
                                "time": time_str,
                                "sentiment": "positive" if any(w in title.lower() for w in ["gain", "profit", "surge", "order", "win", "high", "growth", "buy"]) else ("negative" if any(w in title.lower() for w in ["loss", "fall", "drop", "plunge", "cut", "probe", "down", "sell"]) else "neutral")
                            })

                if hist_df is None or hist_df.empty:
                    is_demo = True
                    error_msg = f"Live data for {ticker_symbol} was unavailable. Switched to Demo Mode."
            except Exception as e:
                is_demo = True
                error_msg = f"Live API query error ({str(e)}). Switched to Demo Mode."
                
        # If in demo mode, populate from demo generators
        if is_demo or hist_df is None or hist_df.empty:
            is_demo = True
            hist_df = get_demo_historical_data(clean_symbol, period="1y")
            demo_fund = get_demo_fundamentals(clean_symbol)
            info_dict = {
                "shortName": display_name,
                "longName": display_name,
                "marketCap": demo_fund.get("market_cap"),
                "trailingPE": demo_fund.get("pe_ratio"),
                "forwardPE": demo_fund.get("forward_pe"),
                "priceToBook": demo_fund.get("pb_ratio"),
                "trailingEps": demo_fund.get("eps"),
                "returnOnEquity": demo_fund.get("roe"),
                "debtToEquity": demo_fund.get("debt_to_equity"),
                "revenueGrowth": demo_fund.get("revenue_growth"),
                "earningsGrowth": demo_fund.get("profit_growth"),
                "dividendYield": demo_fund.get("dividend_yield"),
                "heldPercentInsiders": demo_fund.get("promoter_holding"),
                "heldPercentInstitutions": demo_fund.get("institutional_holding"),
                "fiftyTwoWeekHigh": round(float(hist_df["High"].max()), 2),
                "fiftyTwoWeekLow": round(float(hist_df["Low"].min()), 2),
                "sector": demo_fund.get("sector"),
                "industry": demo_fund.get("industry")
            }
            news_items = get_demo_news(clean_symbol)

        # Compute price action metrics from historical DataFrame
        last_row = hist_df.iloc[-1]
        prev_row = hist_df.iloc[-2] if len(hist_df) > 1 else last_row
        
        current_price = round(float(last_row["Close"]), 2)
        previous_close = round(float(prev_row["Close"]), 2)
        day_change = round(current_price - previous_close, 2)
        day_change_pct = round((day_change / previous_close) * 100, 2) if previous_close else 0.0
        
        # 5-day / weekly change
        week_ago_price = float(hist_df.iloc[-5]["Close"]) if len(hist_df) >= 5 else previous_close
        week_change_pct = round(((current_price - week_ago_price) / week_ago_price) * 100, 2) if week_ago_price else 0.0

        # 1-month change (approx 21 trading days)
        month_ago_price = float(hist_df.iloc[-21]["Close"]) if len(hist_df) >= 21 else previous_close
        month_change_pct = round(((current_price - month_ago_price) / month_ago_price) * 100, 2) if month_ago_price else 0.0
        
        # 52w high & low
        high_52w = round(float(hist_df["High"].max()), 2)
        low_52w = round(float(hist_df["Low"].min()), 2)
        
        dist_to_52w_high_pct = round(((high_52w - current_price) / high_52w) * 100, 2) if high_52w else 0.0
        dist_from_52w_low_pct = round(((current_price - low_52w) / low_52w) * 100, 2) if low_52w else 0.0

        # Candle format for Lightweight Charts: [{ time: 'YYYY-MM-DD', open, high, low, close, volume }]
        candles = []
        for dt, row in hist_df.iterrows():
            time_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]
            candles.append({
                "time": time_str,
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]) if not math.isnan(row["Volume"]) else 0
            })

        is_indian = (
            ticker_symbol.endswith(".NS") 
            or ticker_symbol.endswith(".BO") 
            or ticker_symbol in ["^NSEI", "^BSESN", "^NSEBANK", "^CNXIT"]
            or "₹" in display_name
        )
        currency = "INR" if is_indian else "USD"
        currency_symbol = "₹" if currency == "INR" else "$"

        payload = {
            "symbol": clean_symbol,
            "ticker": ticker_symbol,
            "name": info_dict.get("shortName") or info_dict.get("longName") or display_name,
            "currency": currency,
            "currency_symbol": currency_symbol,
            "is_demo": is_demo,
            "error_msg": error_msg,
            "data_source": "Simulated Demo (Realistic Sample Data)" if is_demo else "Real-time Live Exchange API (NSE/BSE/Global)",
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "price_action": {
                "current_price": current_price,
                "previous_close": previous_close,
                "day_change": day_change,
                "day_change_pct": day_change_pct,
                "week_change_pct": week_change_pct,
                "month_change_pct": month_change_pct,
                "fifty_two_week_high": high_52w,
                "fifty_two_week_low": low_52w,
                "dist_to_52w_high_pct": dist_to_52w_high_pct,
                "dist_from_52w_low_pct": dist_from_52w_low_pct,
                "day_high": round(float(last_row["High"]), 2),
                "day_low": round(float(last_row["Low"]), 2),
                "volume": int(last_row["Volume"]) if not math.isnan(last_row["Volume"]) else 0,
            },
            "candles": candles,
            "info": info_dict,
            "news": news_items,
            "hist_df": hist_df  # passed internally to technical analysis
        }
        
        _CACHE[cache_key] = (time.time(), payload)
        return payload

    @staticmethod
    def get_market_overview() -> List[Dict[str, Any]]:
        """
        Fetches benchmark indices in a single fast batch download with 3-minute in-memory caching.
        """
        global _OVERVIEW_CACHE
        ts, cached_data = _OVERVIEW_CACHE
        if time.time() - ts < OVERVIEW_TTL_SECONDS and cached_data:
            return cached_data

        symbols = [item["symbol"] for item in BENCHMARK_INDICES]
        try:
            df = yf.download(symbols, period="5d", progress=False)
            indices_data = []

            for item in BENCHMARK_INDICES:
                sym = item["symbol"]
                try:
                    if isinstance(df.columns, pd.MultiIndex):
                        close_series = df["Close"][sym].dropna()
                    else:
                        close_series = df["Close"].dropna()

                    if len(close_series) >= 2:
                        curr = round(float(close_series.iloc[-1]), 2)
                        prev = round(float(close_series.iloc[-2]), 2)
                        chg = round(curr - prev, 2)
                        chg_pct = round((chg / prev) * 100, 2)
                    elif len(close_series) == 1:
                        curr = round(float(close_series.iloc[-1]), 2)
                        chg = 0.0
                        chg_pct = 0.0
                    else:
                        raise ValueError("No close data")

                    curr_sym = "₹" if "India" in item["region"] else "$"
                    indices_data.append({
                        "symbol": sym,
                        "name": item["name"],
                        "price": curr,
                        "change": chg,
                        "change_pct": chg_pct,
                        "currency_symbol": curr_sym
                    })
                except Exception:
                    indices_data.append({
                        "symbol": sym,
                        "name": item["name"],
                        "price": 24850.0 if "NSEI" in sym else 81200.0,
                        "change": 85.5,
                        "change_pct": 0.35,
                        "currency_symbol": "₹" if "India" in item["region"] else "$"
                    })

            _OVERVIEW_CACHE = (time.time(), indices_data)
            return indices_data
        except Exception:
            return [
                {"symbol": "^NSEI", "name": "NIFTY 50", "price": 25800.0, "change": 95.0, "change_pct": 0.37, "currency_symbol": "₹"},
                {"symbol": "^BSESN", "name": "BSE SENSEX", "price": 84500.0, "change": 280.0, "change_pct": 0.33, "currency_symbol": "₹"},
                {"symbol": "^NSEBANK", "name": "BANK NIFTY", "price": 53500.0, "change": 150.0, "change_pct": 0.28, "currency_symbol": "₹"},
                {"symbol": "^GSPC", "name": "S&P 500", "price": 5700.0, "change": 22.0, "change_pct": 0.39, "currency_symbol": "$"}
            ]
