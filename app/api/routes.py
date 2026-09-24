"""
FastAPI Routes for StockAI Platform
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.config import POPULAR_INDIAN_STOCKS, BENCHMARK_INDICES, DISCLAIMER_TEXT
from app.services.market_data import MarketDataService, normalize_symbol
from app.services.technical_engine import TechnicalEngine
from app.services.fundamental_engine import FundamentalEngine
from app.services.sentiment_engine import SentimentEngine
from app.services.ai_analyzer import AIAnalyzer

router = APIRouter(prefix="/api", tags=["Stock Analytics"])


class AnalyzeRequest(BaseModel):
    symbol: str
    demo: bool = False


@router.get("/search")
def search_stocks(q: str = Query(..., min_length=1, description="Company name, ticker or symbol")):
    """
    Autocomplete search endpoint matching Indian equities (NSE/BSE) and global tickers.
    """
    query = q.strip().lower()
    matches = []
    
    for item in POPULAR_INDIAN_STOCKS:
        if (query in item["symbol"].lower() or 
            query in item["name"].lower() or 
            query in item["nse"].lower() or 
            query in item["bse"].lower() or 
            query in item["sector"].lower()):
            matches.append({
                "symbol": item["symbol"],
                "name": item["name"],
                "nse": item["nse"],
                "bse": item["bse"],
                "sector": item["sector"],
                "market": "NSE / BSE (India)"
            })
            
    # If the user typed a ticker not in top list (e.g. TRENT, ZOMATO, AAPL)
    clean_sym = q.strip().upper()
    if not any(m["symbol"] == clean_sym for m in matches):
        matches.insert(0, {
            "symbol": clean_sym,
            "name": f"Search '{clean_sym}' on NSE / Global",
            "nse": f"{clean_sym}.NS",
            "bse": f"{clean_sym}.BO",
            "sector": "Equity",
            "market": "Dynamic Lookup"
        })
        
    return {"query": q, "results": matches[:8]}


@router.get("/stock/{symbol}")
def get_stock(symbol: str, demo: bool = False):
    """
    Fetch stock quote, price action, and historical candlestick chart data.
    """
    data = MarketDataService.get_stock_data(symbol, force_demo=demo)
    return {
        "symbol": data["symbol"],
        "ticker": data["ticker"],
        "name": data["name"],
        "currency": data["currency"],
        "currency_symbol": data["currency_symbol"],
        "is_demo": data["is_demo"],
        "data_source": data["data_source"],
        "updated_at": data["updated_at"],
        "price_action": data["price_action"],
        "candles": data["candles"]
    }


@router.get("/technical/{symbol}")
def get_technical(symbol: str, demo: bool = False):
    """
    Calculate and return all technical indicators, moving averages, RSI, MACD, and pivots.
    """
    data = MarketDataService.get_stock_data(symbol, force_demo=demo)
    technicals = TechnicalEngine.calculate_indicators(data["hist_df"])
    return {
        "symbol": data["symbol"],
        "ticker": data["ticker"],
        "current_price": data["price_action"]["current_price"],
        "currency_symbol": data["currency_symbol"],
        "technicals": technicals
    }


@router.get("/fundamental/{symbol}")
def get_fundamental(symbol: str, demo: bool = False):
    """
    Calculate valuation, profitability, balance sheet ratios, and shareholding metrics.
    """
    data = MarketDataService.get_stock_data(symbol, force_demo=demo)
    fundamentals = FundamentalEngine.analyze(data["info"], data["currency"])
    return {
        "symbol": data["symbol"],
        "ticker": data["ticker"],
        "currency_symbol": data["currency_symbol"],
        "fundamentals": fundamentals
    }


@router.get("/news/{symbol}")
def get_news(symbol: str, demo: bool = False):
    """
    Fetch recent market news and computed sentiment scores.
    """
    data = MarketDataService.get_stock_data(symbol, force_demo=demo)
    sentiment = SentimentEngine.analyze(data["news"])
    return {
        "symbol": data["symbol"],
        "ticker": data["ticker"],
        "sentiment": sentiment
    }


@router.post("/analyze")
def analyze_stock(request: AnalyzeRequest):
    """
    Comprehensive Multi-Factor AI Analysis combining Price Action,
    Technicals, Fundamentals, Sentiment, Risk, Scenarios, and Multi-Timeframe Matrix.
    """
    data = MarketDataService.get_stock_data(request.symbol, force_demo=request.demo)
    analysis = AIAnalyzer.analyze(data)
    
    # Also attach chart candles for direct visualization
    analysis["candles"] = data["candles"]
    analysis["disclaimer"] = DISCLAIMER_TEXT
    return analysis


@router.get("/demo/{symbol}")
def get_demo_analysis(symbol: str):
    """
    Shortcut to get immediate demo analysis for testing and offline presentations.
    """
    data = MarketDataService.get_stock_data(symbol, force_demo=True)
    analysis = AIAnalyzer.analyze(data)
    analysis["candles"] = data["candles"]
    analysis["disclaimer"] = DISCLAIMER_TEXT
    return analysis


@router.get("/market/overview")
def get_market_overview():
    """
    Fast benchmark indices overview for market context (Nifty 50, Sensex, Bank Nifty, S&P 500)
    with batch downloading and 3-minute caching.
    """
    indices_data = MarketDataService.get_market_overview()
    return {
        "indices": indices_data,
        "disclaimer": DISCLAIMER_TEXT
    }
