"""
Technical Analysis Engine - Mathematical indicators, pivots, trend & volume signals
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class TechnicalEngine:
    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Takes an OHLCV historical dataframe (at least 20 rows, ideally 200+)
        and computes all technical indicators and support/resistance levels.
        """
        if df is None or len(df) < 15:
            return {"error": "Insufficient historical data for technical analysis (minimum 15 bars required)"}
        
        close = df["Close"].copy()
        high = df["High"].copy()
        low = df["Low"].copy()
        volume = df["Volume"].copy()
        
        current_price = float(close.iloc[-1])
        
        # 1. Moving Averages (SMA 20, 50, 200)
        sma20 = close.rolling(window=20).mean()
        sma50 = close.rolling(window=50).mean() if len(close) >= 50 else None
        sma200 = close.rolling(window=200).mean() if len(close) >= 200 else None
        
        # EMA 9, EMA 21
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        
        val_sma20 = round(float(sma20.iloc[-1]), 2) if not pd.isna(sma20.iloc[-1]) else None
        val_sma50 = round(float(sma50.iloc[-1]), 2) if sma50 is not None and not pd.isna(sma50.iloc[-1]) else None
        val_sma200 = round(float(sma200.iloc[-1]), 2) if sma200 is not None and not pd.isna(sma200.iloc[-1]) else None
        val_ema9 = round(float(ema9.iloc[-1]), 2)
        val_ema21 = round(float(ema21.iloc[-1]), 2)
        
        # Distance from Moving Averages
        dist_sma20_pct = round(((current_price - val_sma20) / val_sma20) * 100, 2) if val_sma20 else None
        dist_sma50_pct = round(((current_price - val_sma50) / val_sma50) * 100, 2) if val_sma50 else None
        dist_sma200_pct = round(((current_price - val_sma200) / val_sma200) * 100, 2) if val_sma200 else None

        # Golden Cross / Death Cross detection (SMA 50 vs SMA 200)
        cross_signal = "None"
        if sma50 is not None and sma200 is not None and len(sma50.dropna()) > 2 and len(sma200.dropna()) > 2:
            prev_diff = float(sma50.iloc[-2]) - float(sma200.iloc[-2])
            curr_diff = float(sma50.iloc[-1]) - float(sma200.iloc[-1])
            if prev_diff <= 0 and curr_diff > 0:
                cross_signal = "Golden Cross (Bullish)"
            elif prev_diff >= 0 and curr_diff < 0:
                cross_signal = "Death Cross (Bearish)"
            elif curr_diff > 0:
                cross_signal = "Bullish Alignment (SMA50 > SMA200)"
            else:
                cross_signal = "Bearish Alignment (SMA50 < SMA200)"
                
        # 2. RSI (14) - Wilder's Smoothing
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        rsi_series = 100 - (100 / (1 + rs))
        current_rsi = round(float(rsi_series.iloc[-1]), 2)
        
        if current_rsi >= 70:
            rsi_status = "Overbought"
            rsi_interpretation = "Stock is in overbought territory; short-term consolidation or pullback possible."
        elif current_rsi <= 30:
            rsi_status = "Oversold"
            rsi_interpretation = "Stock is in oversold territory; technical bounce or accumulation possible."
        elif current_rsi >= 55:
            rsi_status = "Bullish Momentum"
            rsi_interpretation = "RSI indicates healthy bullish momentum with room to run."
        elif current_rsi <= 45:
            rsi_status = "Bearish Momentum"
            rsi_interpretation = "RSI reflects negative momentum and selling pressure."
        else:
            rsi_status = "Neutral"
            rsi_interpretation = "RSI is in the neutral consolidation zone (45–55)."

        # 3. MACD (12, 26, 9)
        fast_ema = close.ewm(span=12, adjust=False).mean()
        slow_ema = close.ewm(span=26, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        val_macd = round(float(macd_line.iloc[-1]), 2)
        val_signal = round(float(signal_line.iloc[-1]), 2)
        val_hist = round(float(histogram.iloc[-1]), 2)
        prev_hist = round(float(histogram.iloc[-2]), 2) if len(histogram) > 1 else val_hist
        
        macd_crossover = "Neutral"
        if val_hist > 0 and prev_hist <= 0:
            macd_crossover = "Bullish Crossover (Recent)"
        elif val_hist < 0 and prev_hist >= 0:
            macd_crossover = "Bearish Crossover (Recent)"
        elif val_macd > val_signal and val_hist > prev_hist:
            macd_crossover = "Strong Bullish Expansion"
        elif val_macd > val_signal:
            macd_crossover = "Bullish (MACD above Signal)"
        elif val_macd < val_signal and val_hist < prev_hist:
            macd_crossover = "Strong Bearish Expansion"
        else:
            macd_crossover = "Bearish (MACD below Signal)"

        # 4. Bollinger Bands (20, 2)
        bb_mid = sma20
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_mid + (2.0 * bb_std)
        bb_lower = bb_mid - (2.0 * bb_std)
        
        val_bb_upper = round(float(bb_upper.iloc[-1]), 2) if not pd.isna(bb_upper.iloc[-1]) else current_price * 1.05
        val_bb_mid = round(float(bb_mid.iloc[-1]), 2) if not pd.isna(bb_mid.iloc[-1]) else current_price
        val_bb_lower = round(float(bb_lower.iloc[-1]), 2) if not pd.isna(bb_lower.iloc[-1]) else current_price * 0.95
        
        # Bandwidth & %B
        bandwidth = round(((val_bb_upper - val_bb_lower) / val_bb_mid) * 100, 2) if val_bb_mid else 0.0
        percent_b = round(((current_price - val_bb_lower) / (val_bb_upper - val_bb_lower + 1e-10)), 2)
        
        bb_status = "Within Bands"
        if percent_b >= 1.0:
            bb_status = "Piercing Upper Band (Overbought)"
        elif percent_b <= 0.0:
            bb_status = "Piercing Lower Band (Oversold)"
        elif percent_b >= 0.8:
            bb_status = "Upper Range"
        elif percent_b <= 0.2:
            bb_status = "Lower Range"
        else:
            bb_status = "Middle Band Equilibrium"

        # 5. Volume Analysis (20-day SMA Volume)
        vol_window = min(20, len(volume))
        avg_vol_20 = int(volume.iloc[-vol_window:].mean()) if vol_window > 0 else 0
        current_vol = int(volume.iloc[-1])
        vol_ratio = round(current_vol / (avg_vol_20 + 1e-10), 2)
        
        if vol_ratio >= 1.8:
            vol_signal = "Unusual Volume Surge"
        elif vol_ratio >= 1.25:
            vol_signal = "Above Average Volume"
        elif vol_ratio >= 0.75:
            vol_signal = "Average Volume"
        else:
            vol_signal = "Low Volume (Subdued)"

        # 6. Breakout / Breakdown Signals
        # 20-day high and low
        high_20d = float(high.iloc[-20:].max()) if len(high) >= 20 else float(high.max())
        low_20d = float(low.iloc[-20:].min()) if len(low) >= 20 else float(low.min())
        
        breakout_signal = "Consolidation"
        if current_price >= high_20d * 0.998 and vol_ratio >= 1.2:
            breakout_signal = "Bullish 20-Day Range Breakout"
        elif current_price <= low_20d * 1.002 and vol_ratio >= 1.2:
            breakout_signal = "Bearish 20-Day Range Breakdown"
        elif current_price >= high_20d * 0.99:
            breakout_signal = "Testing 20-Day Resistance High"
        elif current_price <= low_20d * 1.01:
            breakout_signal = "Testing 20-Day Support Low"

        # 7. Support & Resistance Calculations
        # Pivot point (P) based on previous period
        prev_h = float(high.iloc[-2]) if len(high) > 1 else float(high.iloc[-1])
        prev_l = float(low.iloc[-2]) if len(low) > 1 else float(low.iloc[-1])
        prev_c = float(close.iloc[-2]) if len(close) > 1 else float(close.iloc[-1])
        
        pivot_p = (prev_h + prev_l + prev_c) / 3.0
        r1 = (2 * pivot_p) - prev_l
        s1 = (2 * pivot_p) - prev_h
        r2 = pivot_p + (prev_h - prev_l)
        s2 = pivot_p - (prev_h - prev_l)
        
        # Swing Highs & Lows (last 30 days)
        recent_window = min(30, len(df))
        recent_highs = high.iloc[-recent_window:]
        recent_lows = low.iloc[-recent_window:]
        
        # Levels above current price = Resistances
        candidates_r = [h for h in [r1, r2, val_bb_upper, float(recent_highs.max())] if h > current_price]
        candidates_r.sort()
        immediate_resistance = round(candidates_r[0], 2) if candidates_r else round(current_price * 1.03, 2)
        strong_resistance = round(max(candidates_r), 2) if len(candidates_r) > 1 else round(immediate_resistance * 1.04, 2)
        
        # Levels below current price = Supports
        candidates_s = [s for s in [s1, s2, val_bb_lower, val_sma50, float(recent_lows.min())] if s is not None and s < current_price]
        candidates_s.sort(reverse=True)
        immediate_support = round(candidates_s[0], 2) if candidates_s else round(current_price * 0.97, 2)
        strong_support = round(min(candidates_s), 2) if len(candidates_s) > 1 else round(immediate_support * 0.96, 2)

        # 8. Trend Direction and Strength
        # Multi-factor trend calculation: Price vs SMA20, SMA50, SMA200, EMA9 vs EMA21, and RSI
        bull_points = 0
        total_points = 6
        
        if val_sma20 and current_price > val_sma20: bull_points += 1
        if val_sma50 and current_price > val_sma50: bull_points += 1.5
        if val_sma200 and current_price > val_sma200: bull_points += 1.5
        if val_ema9 > val_ema21: bull_points += 1
        if current_rsi > 50: bull_points += 1
        
        bull_ratio = bull_points / total_points
        if bull_ratio >= 0.75:
            trend_direction = "Strong Bullish"
            trend_strength = "High (Trend strongly supported by multiple moving averages)"
        elif bull_ratio >= 0.55:
            trend_direction = "Moderately Bullish"
            trend_strength = "Moderate (Price above primary short-term trendlines)"
        elif bull_ratio >= 0.40:
            trend_direction = "Neutral / Sideways"
            trend_strength = "Weak (Mixed moving average signals, rangebound consolidation)"
        elif bull_ratio >= 0.25:
            trend_direction = "Moderately Bearish"
            trend_strength = "Moderate (Short-term breakdown below key moving averages)"
        else:
            trend_direction = "Strong Bearish"
            trend_strength = "High (Clear downward trend across short and long moving averages)"

        # Prepare Moving Average series data points for chart overlays
        overlay_ma20 = []
        overlay_ma50 = []
        overlay_ma200 = []
        
        for i in range(len(df)):
            dt = df.index[i]
            time_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]
            
            v20 = sma20.iloc[i]
            if not pd.isna(v20):
                overlay_ma20.append({"time": time_str, "value": round(float(v20), 2)})
                
            if sma50 is not None:
                v50 = sma50.iloc[i]
                if not pd.isna(v50):
                    overlay_ma50.append({"time": time_str, "value": round(float(v50), 2)})
                    
            if sma200 is not None:
                v200 = sma200.iloc[i]
                if not pd.isna(v200):
                    overlay_ma200.append({"time": time_str, "value": round(float(v200), 2)})

        return {
            "summary": {
                "trend_direction": trend_direction,
                "trend_strength": trend_strength,
                "breakout_signal": breakout_signal,
                "cross_signal": cross_signal
            },
            "moving_averages": {
                "sma_20": val_sma20,
                "sma_50": val_sma50,
                "sma_200": val_sma200,
                "ema_9": val_ema9,
                "ema_21": val_ema21,
                "price_vs_sma20_pct": dist_sma20_pct,
                "price_vs_sma50_pct": dist_sma50_pct,
                "price_vs_sma200_pct": dist_sma200_pct,
                "is_above_sma20": current_price > val_sma20 if val_sma20 else False,
                "is_above_sma50": current_price > val_sma50 if val_sma50 else False,
                "is_above_sma200": current_price > val_sma200 if val_sma200 else False,
            },
            "rsi": {
                "value": current_rsi,
                "status": rsi_status,
                "interpretation": rsi_interpretation
            },
            "macd": {
                "macd_line": val_macd,
                "signal_line": val_signal,
                "histogram": val_hist,
                "status": macd_crossover
            },
            "bollinger_bands": {
                "upper": val_bb_upper,
                "middle": val_bb_mid,
                "lower": val_bb_lower,
                "bandwidth_pct": bandwidth,
                "percent_b": percent_b,
                "status": bb_status
            },
            "volume": {
                "current_volume": current_vol,
                "average_volume_20": avg_vol_20,
                "volume_ratio": vol_ratio,
                "status": vol_signal
            },
            "support_resistance": {
                "current_price": current_price,
                "immediate_support": immediate_support,
                "strong_support": strong_support,
                "immediate_resistance": immediate_resistance,
                "strong_resistance": strong_resistance,
                "pivot_point": round(pivot_p, 2),
                "dist_to_resistance_pct": round(((immediate_resistance - current_price) / current_price) * 100, 2),
                "dist_to_support_pct": round(((current_price - immediate_support) / current_price) * 100, 2)
            },
            "chart_overlays": {
                "ma20": overlay_ma20[-100:] if len(overlay_ma20) > 100 else overlay_ma20,
                "ma50": overlay_ma50[-100:] if len(overlay_ma50) > 100 else overlay_ma50,
                "ma200": overlay_ma200[-100:] if len(overlay_ma200) > 100 else overlay_ma200
            }
        }
