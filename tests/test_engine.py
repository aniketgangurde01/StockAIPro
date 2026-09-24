# Unit and Integration test for StockAI Engine
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.market_data import normalize_symbol, get_demo_historical_data, MarketDataService
from app.services.technical_engine import TechnicalEngine
from app.services.fundamental_engine import FundamentalEngine, format_market_cap
from app.services.sentiment_engine import SentimentEngine
from app.services.ai_analyzer import AIAnalyzer


def test_symbol_normalization():
    sym, ticker, name = normalize_symbol("RELIANCE")
    assert sym == "RELIANCE"
    assert ticker == "RELIANCE.NS"
    assert "Reliance" in name
    
    sym2, ticker2, _ = normalize_symbol("500325")
    assert ticker2 == "500325.BO"
    
    sym3, ticker3, _ = normalize_symbol("AAPL")
    assert ticker3 == "AAPL"

    sym4, ticker4, name4 = normalize_symbol("^NSEI")
    assert ticker4 == "^NSEI"
    assert "NIFTY" in name4

    sym5, ticker5, _ = normalize_symbol("S&P 500")
    assert ticker5 == "^GSPC"


def test_technical_engine_math():
    df = get_demo_historical_data("RELIANCE", period="1y")
    assert len(df) >= 200
    
    indicators = TechnicalEngine.calculate_indicators(df)
    assert "moving_averages" in indicators
    assert "rsi" in indicators
    assert "macd" in indicators
    assert "bollinger_bands" in indicators
    assert "support_resistance" in indicators
    
    # Check RSI range
    rsi = indicators["rsi"]["value"]
    assert 0 <= rsi <= 100
    
    # Check Moving Averages
    ma = indicators["moving_averages"]
    assert ma["sma_20"] is not None
    assert ma["sma_50"] is not None
    assert ma["ema_9"] is not None
    
    # Check Support/Resistance
    sr = indicators["support_resistance"]
    assert sr["immediate_support"] <= sr["current_price"] <= sr["immediate_resistance"]


def test_fundamental_engine():
    info = {
        "marketCap": 16888525000000,
        "trailingPE": 22.5,
        "priceToBook": 1.9,
        "returnOnEquity": 0.14,
        "debtToEquity": 35.0,
        "revenueGrowth": 0.18,
        "earningsGrowth": 0.12,
        "heldPercentInsiders": 0.51,
        "heldPercentInstitutions": 0.28
    }
    fund = FundamentalEngine.analyze(info, "INR")
    assert fund["available"] is True
    assert 10 <= fund["score"] <= 100
    assert "Lakh Cr" in fund["market_cap_formatted"] or "Cr" in fund["market_cap_formatted"]


def test_ai_analyzer_pipeline():
    stock_data = MarketDataService.get_stock_data("RELIANCE", force_demo=True)
    analysis = AIAnalyzer.analyze(stock_data)
    
    assert "ai_outlook" in analysis
    assert "scores" in analysis
    assert "scenarios" in analysis
    assert "timeframe_analysis" in analysis
    
    outlook = analysis["ai_outlook"]
    assert outlook["outlook"] in ["BULLISH", "MODERATELY BULLISH", "NEUTRAL", "MODERATELY BEARISH", "BEARISH"]
    assert outlook["potential_direction"] in ["UPWARD", "SIDEWAYS", "DOWNWARD"]
    assert 50 <= outlook["confidence_pct"] <= 90
    assert len(outlook["factors"]) > 0
    
    # Check scenarios
    scenarios = analysis["scenarios"]
    assert "bullish" in scenarios
    assert "neutral" in scenarios
    assert "bearish" in scenarios
    
    # Check timeframes
    timeframes = analysis["timeframe_analysis"]
    assert len(timeframes) == 4
    labels = [tf["timeframe"] for tf in timeframes]
    assert any("Intraday" in l for l in labels)
    assert any("Short" in l for l in labels)
    assert any("Swing" in l for l in labels)
    assert any("Medium" in l for l in labels)


if __name__ == "__main__":
    print("Running StockAI engine verification...")
    test_symbol_normalization()
    print("[OK] Symbol normalization passed")
    test_technical_engine_math()
    print("[OK] Technical engine math passed")
    test_fundamental_engine()
    print("[OK] Fundamental engine passed")
    test_ai_analyzer_pipeline()
    print("[OK] AI Analyzer pipeline passed")
    print("All backend engine tests successfully passed!")
