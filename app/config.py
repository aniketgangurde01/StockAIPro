"""
Application Configuration and Indian Stock Registry
"""
from typing import Dict, List, Any

DISCLAIMER_TEXT = (
    "This analysis is for educational and informational purposes only. "
    "It is not financial advice and does not guarantee future stock price movements. "
    "Market conditions can change rapidly. Always conduct your own research before making investment decisions."
)

POPULAR_INDIAN_STOCKS: List[Dict[str, str]] = [
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "nse": "RELIANCE.NS", "bse": "500325.BO", "sector": "Energy / Conglomerate"},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "nse": "TCS.NS", "bse": "532540.BO", "sector": "Information Technology"},
    {"symbol": "INFY", "name": "Infosys Ltd", "nse": "INFY.NS", "bse": "500209.BO", "sector": "Information Technology"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "nse": "HDFCBANK.NS", "bse": "500180.BO", "sector": "Financial Services / Banking"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "nse": "ICICIBANK.NS", "bse": "532174.BO", "sector": "Financial Services / Banking"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd", "nse": "TATAMOTORS.NS", "bse": "500570.BO", "sector": "Automobile"},
    {"symbol": "SBIN", "name": "State Bank of India", "nse": "SBIN.NS", "bse": "500112.BO", "sector": "Banking / PSU"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "nse": "BHARTIARTL.NS", "bse": "532454.BO", "sector": "Telecommunications"},
    {"symbol": "ITC", "name": "ITC Ltd", "nse": "ITC.NS", "bse": "500875.BO", "sector": "Consumer Goods / FMCG"},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd", "nse": "LT.NS", "bse": "500510.BO", "sector": "Engineering & Construction"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd", "nse": "KOTAKBANK.NS", "bse": "500247.BO", "sector": "Banking"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "nse": "HINDUNILVR.NS", "bse": "500696.BO", "sector": "FMCG"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "nse": "BAJFINANCE.NS", "bse": "500034.BO", "sector": "NBFC / Finance"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd", "nse": "MARUTI.NS", "bse": "532500.BO", "sector": "Automobile"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries", "nse": "SUNPHARMA.NS", "bse": "524715.BO", "sector": "Pharmaceuticals"},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd", "nse": "TATASTEEL.NS", "bse": "500470.BO", "sector": "Metals & Mining"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd", "nse": "ADANIENT.NS", "bse": "512599.BO", "sector": "Metals / Trading"},
    {"symbol": "WIPRO", "name": "Wipro Ltd", "nse": "WIPRO.NS", "bse": "507685.BO", "sector": "Information Technology"},
    {"symbol": "NTPC", "name": "NTPC Ltd", "nse": "NTPC.NS", "bse": "532555.BO", "sector": "Power Generation"},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India", "nse": "POWERGRID.NS", "bse": "532898.BO", "sector": "Power Transmission"}
]

# Quick lookup mapping for symbols to primary yahoo ticker
INDIAN_SYMBOL_MAP: Dict[str, str] = {item["symbol"].upper(): item["nse"] for item in POPULAR_INDIAN_STOCKS}
for item in POPULAR_INDIAN_STOCKS:
    # Also index by BSE code
    bse_code = item["bse"].split(".")[0]
    INDIAN_SYMBOL_MAP[bse_code] = item["bse"]

# Global Indices tracking
BENCHMARK_INDICES = [
    {"symbol": "^NSEI", "name": "NIFTY 50", "region": "India"},
    {"symbol": "^BSESN", "name": "BSE SENSEX", "region": "India"},
    {"symbol": "^NSEBANK", "name": "BANK NIFTY", "region": "India"},
    {"symbol": "^GSPC", "name": "S&P 500", "region": "Global"}
]
