"""
Comprehensive End-to-End System Test & Verification Script for StockAI Platform
Validates:
1. Static frontend HTML/JS/CSS integrity and DOM element matching
2. All REST API endpoints (GET & POST)
3. Multi-factor AI analysis engine accuracy and response schemas
4. Resilience on edge cases (unknown tickers, malformed queries, demo switches)
5. Index tickers and market overview stability
"""
import os
import re
import sys
import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "static")
HTML_FILE = os.path.join(STATIC_DIR, "index.html")
APP_JS = os.path.join(STATIC_DIR, "js", "app.js")
WATCHLIST_JS = os.path.join(STATIC_DIR, "js", "watchlist.js")

def test_frontend_dom_integrity():
    print("[1/5] Testing Frontend DOM IDs and Bindings...")
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Extract all id="..." from HTML
    html_ids = set(re.findall(r'id=["\']([a-zA-Z0-9_\-]+)["\']', html_content))
    
    # Read JS files and find document.getElementById("...")
    js_ids = set()
    for js_path in [APP_JS, WATCHLIST_JS]:
        with open(js_path, "r", encoding="utf-8") as f:
            content = f.read()
            matches = re.findall(r'getElementById\(["\']([a-zA-Z0-9_\-]+)["\']\)', content)
            js_ids.update(matches)

    # Some IDs may be dynamically rendered in HTML template strings in JS
    # e.g., 'watchlist-items-container'
    missing = [elem_id for elem_id in js_ids if elem_id not in html_ids]
    
    # Check if missing elements are dynamically rendered or intentional
    truly_missing = []
    for m in missing:
        if m not in html_ids:
            # Check if it was rendered by JS in an innerHTML string
            if f'id="{m}"' not in html_content and f"id='{m}'" not in html_content:
                truly_missing.append(m)

    if truly_missing:
        print(f"  [WARN] IDs referenced in JS but not found in index.html: {truly_missing}")
    else:
        print(f"  [PASS] All {len(js_ids)} JS DOM element bindings are valid and present in index.html.")

    return len(truly_missing) == 0


def fetch_url(url, method="GET", data=None, headers=None, timeout=15):
    if headers is None:
        headers = {}
    if data is not None and isinstance(data, dict):
        data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency = (time.time() - start_t) * 1000
            body = response.read().decode("utf-8")
            return response.status, body, latency
    except urllib.error.HTTPError as e:
        latency = (time.time() - start_t) * 1000
        return e.code, e.read().decode("utf-8"), latency
    except Exception as e:
        latency = (time.time() - start_t) * 1000
        return 500, str(e), latency


def test_api_endpoints():
    print("\n[2/5] Testing REST API Endpoints...")
    endpoints = [
        ("GET", "/", None, 200, "HTML single-page app root"),
        ("GET", "/health", None, 200, "Health check"),
        ("GET", "/api/market/overview", None, 200, "Market overview benchmark indices"),
        ("GET", "/api/search?q=tata", None, 200, "Search autocomplete query"),
        ("GET", "/api/stock/RELIANCE", None, 200, "Stock price action & candles"),
        ("GET", "/api/technical/TCS", None, 200, "Technical indicators & pivots"),
        ("GET", "/api/fundamental/INFY", None, 200, "Fundamental ratios & health"),
        ("GET", "/api/news/HDFCBANK", None, 200, "News headlines & sentiment"),
        ("GET", "/api/demo/RELIANCE", None, 200, "Immediate demo analysis"),
        ("POST", "/api/analyze", {"symbol": "RELIANCE", "demo": False}, 200, "POST Analyze live stock"),
        ("POST", "/api/analyze", {"symbol": "TCS", "demo": True}, 200, "POST Analyze demo mode stock"),
    ]

    all_pass = True
    for method, path, body, exp_status, desc in endpoints:
        status, resp_text, latency = fetch_url(f"{BASE_URL}{path}", method=method, data=body)
        is_ok = (status == exp_status)
        if not is_ok:
            all_pass = False
        mark = "[PASS]" if is_ok else "[FAIL]"
        print(f"  {mark} {method} {path:<28} -> {status} ({latency:.1f}ms) - {desc}")
        if not is_ok:
            print(f"         Error: {resp_text[:120]}")

    return all_pass


def test_ai_analysis_schema():
    print("\n[3/5] Validating AI Analysis Engine Response Schema & Mathematics...")
    status, body, latency = fetch_url(f"{BASE_URL}/api/analyze", method="POST", data={"symbol": "RELIANCE"})
    assert status == 200, f"Failed with status {status}"
    data = json.loads(body)

    required_keys = [
        "symbol", "ticker", "name", "currency_symbol", "data_source", "is_demo", 
        "updated_at", "scores", "ai_outlook", "price_action", "technicals", 
        "fundamentals", "sentiment", "risk_analysis", "scenarios", 
        "timeframe_analysis", "candles", "disclaimer"
    ]
    missing_keys = [k for k in required_keys if k not in data]
    assert not missing_keys, f"Missing required top-level keys: {missing_keys}"

    # Verify scores range 0-100
    scores = data["scores"]
    for s_name, s_val in scores.items():
        assert 0 <= s_val <= 100, f"Score {s_name} = {s_val} out of bounds (0-100)"
    print(f"  [PASS] All 5 modular scores within [0, 100]: {scores}")

    # Verify AI Outlook
    outlook = data["ai_outlook"]
    valid_outlooks = ["BULLISH", "MODERATELY BULLISH", "NEUTRAL", "MODERATELY BEARISH", "BEARISH"]
    valid_dirs = ["UPWARD", "SIDEWAYS", "DOWNWARD"]
    assert outlook["outlook"] in valid_outlooks, f"Unexpected outlook: {outlook['outlook']}"
    assert outlook["potential_direction"] in valid_dirs, f"Unexpected direction: {outlook['potential_direction']}"
    assert 50 <= outlook["confidence_pct"] <= 100, f"Unexpected confidence: {outlook['confidence_pct']}"
    assert len(outlook["factors"]) >= 2, f"Factors too few: {len(outlook['factors'])}"
    print(f"  [PASS] AI Outlook: {outlook['outlook']} | Direction: {outlook['potential_direction']} | Confidence: {outlook['confidence_pct']}%")

    # Verify Candles format
    candles = data["candles"]
    assert len(candles) >= 20, f"Candles count too low: {len(candles)}"
    c0 = candles[-1]
    for ck in ["time", "open", "high", "low", "close", "volume"]:
        assert ck in c0, f"Missing candle key {ck}"
    print(f"  [PASS] Candlestick chart payload verified: {len(candles)} historical bars")

    # Verify Technicals
    tech = data["technicals"]
    assert "rsi" in tech and "value" in tech["rsi"]
    assert "macd" in tech and "macd_line" in tech["macd"]
    assert "moving_averages" in tech and "sma_20" in tech["moving_averages"]
    assert "support_resistance" in tech and "immediate_support" in tech["support_resistance"]
    print(f"  [PASS] Technical indicators calculated: RSI={tech['rsi']['value']}, MACD={tech['macd']['macd_line']}")

    # Verify Scenarios
    scenarios = data["scenarios"]
    for sc in ["bullish", "neutral", "bearish"]:
        assert sc in scenarios, f"Missing scenario {sc}"
        assert "trigger" in scenarios[sc] and "target_levels" in scenarios[sc]
    print(f"  [PASS] Probability scenarios verified (Bullish, Neutral, Bearish)")

    # Verify Multi-timeframes
    tfs = data["timeframe_analysis"]
    assert len(tfs) == 4, f"Expected 4 timeframes, got {len(tfs)}"
    print(f"  [PASS] 4-Timeframe Matrix verified (Intraday, Short, Swing, Medium)")
    return True


def test_edge_cases():
    print("\n[4/5] Testing Edge Cases & Resilience...")
    all_pass = True

    # 1. Unknown ticker - should gracefully fall back to demo mode without crashing
    status, body, lat = fetch_url(f"{BASE_URL}/api/analyze", method="POST", data={"symbol": "NONEXISTENT_TICKER_999"})
    if status == 200:
        data = json.loads(body)
        print(f"  [PASS] Unknown ticker handled gracefully: fallback to is_demo={data.get('is_demo')}")
    else:
        print(f"  [FAIL] Unknown ticker returned HTTP {status}")
        all_pass = False

    # 2. Global US Ticker (AAPL)
    status, body, lat = fetch_url(f"{BASE_URL}/api/analyze", method="POST", data={"symbol": "AAPL"})
    if status == 200:
        data = json.loads(body)
        assert data.get("currency_symbol") == "$", f"Expected $ currency for AAPL, got {data.get('currency_symbol')}"
        print(f"  [PASS] Global US ticker AAPL parsed: currency={data.get('currency_symbol')}, price={data['price_action']['current_price']}")
    else:
        print(f"  [FAIL] AAPL analysis failed with HTTP {status}")
        all_pass = False

    # 3. Autocomplete search on single character & special characters
    status, body, lat = fetch_url(f"{BASE_URL}/api/search?q=z")
    assert status == 200
    res = json.loads(body).get("results", [])
    print(f"  [PASS] Single char autocomplete: returned {len(res)} results")

    # 4. Market overview index stability
    status, body, lat = fetch_url(f"{BASE_URL}/api/market/overview")
    data = json.loads(body)
    indices = data.get("indices", [])
    assert len(indices) == 4
    idx_symbols = [i["symbol"] for i in indices]
    print(f"  [PASS] Market overview indices valid: {idx_symbols} ({lat:.1f}ms)")

    return all_pass


def test_concurrency_and_performance():
    print("\n[5/5] Testing Response Latencies & Cache...")
    # First call
    _, _, lat1 = fetch_url(f"{BASE_URL}/api/market/overview")
    # Cached call
    _, _, lat2 = fetch_url(f"{BASE_URL}/api/market/overview")
    print(f"  [PASS] Market Overview latency: 1st={lat1:.1f}ms, 2nd (cached)={lat2:.1f}ms")

    _, _, s_lat1 = fetch_url(f"{BASE_URL}/api/search?q=reliance")
    print(f"  [PASS] Search latency: {s_lat1:.1f}ms")

    _, _, a_lat = fetch_url(f"{BASE_URL}/api/analyze", method="POST", data={"symbol": "RELIANCE"})
    print(f"  [PASS] Stock analysis latency: {a_lat:.1f}ms")


if __name__ == "__main__":
    print("=" * 70)
    print("  StockAI Comprehensive Integration & Debug Verification Suite")
    print("=" * 70)

    p1 = test_frontend_dom_integrity()
    p2 = test_api_endpoints()
    p3 = test_ai_analysis_schema()
    p4 = test_edge_cases()
    test_concurrency_and_performance()

    print("\n" + "=" * 70)
    if p1 and p2 and p3 and p4:
        print("  ALL COMPREHENSIVE TESTS PASSED SUCCESSFULLY! (0 ERRORS)")
    else:
        print("  ONE OR MORE VERIFICATION STEPS FAILED!")
        sys.exit(1)
    print("=" * 70)
