"""
AI Analysis Engine - Multi-Factor Scoring, Outlook Classification, Scenarios, and Multi-Timeframe Matrix
"""
from typing import Dict, Any, List, Tuple
from app.services.fundamental_engine import FundamentalEngine
from app.services.technical_engine import TechnicalEngine
from app.services.sentiment_engine import SentimentEngine


class AIAnalyzer:
    @classmethod
    def analyze(cls, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combines Price Action, Technicals, Fundamentals, Sentiment, and Risk
        into an AI Market Outlook with transparent multi-factor scores.
        """
        hist_df = stock_data.get("hist_df")
        pa = stock_data.get("price_action", {})
        info = stock_data.get("info", {})
        news = stock_data.get("news", [])
        curr_symbol = stock_data.get("currency_symbol", "₹")
        current_price = pa.get("current_price", 0.0)

        # 1. Calculate Technicals
        technicals = TechnicalEngine.calculate_indicators(hist_df)
        
        # 2. Calculate Fundamentals
        fundamentals = FundamentalEngine.analyze(info, stock_data.get("currency", "INR"))
        
        # 3. Calculate Sentiment
        sentiment = SentimentEngine.analyze(
            news, 
            sector=fundamentals.get("sector", "General"),
            inst_holding_pct=fundamentals.get("institutional_holding_pct")
        )
        
        # 4. Compute Modular Scores
        scores = cls._compute_scores(pa, technicals, fundamentals, sentiment)
        
        # 5. Synthesize AI Outlook and Confidence
        outlook_data = cls._generate_outlook(scores, pa, technicals, fundamentals, curr_symbol)
        
        # 6. Generate Risk Analysis
        risk_data = cls._generate_risk_analysis(scores, pa, technicals, fundamentals, curr_symbol)
        
        # 7. Generate Scenarios (Bullish / Neutral / Bearish)
        scenarios = cls._generate_scenarios(pa, technicals, curr_symbol)
        
        # 8. Generate Multi-Timeframe Matrix
        timeframes = cls._generate_timeframes(scores, pa, technicals, fundamentals, curr_symbol)
        
        return {
            "symbol": stock_data["symbol"],
            "ticker": stock_data["ticker"],
            "name": stock_data["name"],
            "currency_symbol": curr_symbol,
            "data_source": stock_data["data_source"],
            "is_demo": stock_data["is_demo"],
            "updated_at": stock_data["updated_at"],
            "scores": scores,
            "ai_outlook": outlook_data,
            "price_action": pa,
            "technicals": technicals,
            "fundamentals": fundamentals,
            "sentiment": sentiment,
            "risk_analysis": risk_data,
            "scenarios": scenarios,
            "timeframe_analysis": timeframes
        }

    @classmethod
    def _compute_scores(
        cls, 
        pa: Dict[str, Any], 
        technicals: Dict[str, Any], 
        fundamentals: Dict[str, Any], 
        sentiment: Dict[str, Any]
    ) -> Dict[str, int]:
        """
        Calculates 5 distinct transparent scores (0–100):
        1. Technical Score
        2. Fundamental Score
        3. Momentum Score
        4. Sentiment Score
        5. Risk Score
        """
        # --- 1. Technical Score (0-100) ---
        tech_pts = 50.0
        ma = technicals.get("moving_averages", {})
        if ma.get("is_above_sma20"): tech_pts += 8
        else: tech_pts -= 6
        if ma.get("is_above_sma50"): tech_pts += 12
        else: tech_pts -= 10
        if ma.get("is_above_sma200"): tech_pts += 12
        else: tech_pts -= 10
        if ma.get("ema_9", 0) > ma.get("ema_21", 0): tech_pts += 7
        else: tech_pts -= 5
        
        rsi_val = technicals.get("rsi", {}).get("value", 50)
        if 52 <= rsi_val <= 68: tech_pts += 10
        elif 40 <= rsi_val < 52: tech_pts += 2
        elif rsi_val > 75: tech_pts -= 4  # Overbought penalty
        elif rsi_val < 30: tech_pts += 4  # Oversold bounce possibility

        macd = technicals.get("macd", {})
        if macd.get("histogram", 0) > 0: tech_pts += 8
        else: tech_pts -= 6

        vol = technicals.get("volume", {})
        if vol.get("volume_ratio", 1.0) >= 1.25 and pa.get("day_change", 0) > 0:
            tech_pts += 7
        
        tech_score = int(max(10, min(95, round(tech_pts))))

        # --- 2. Fundamental Score (0-100) ---
        fund_score = fundamentals.get("score", 50)

        # --- 3. Momentum Score (0-100) ---
        mom_pts = 50.0
        day_chg_pct = pa.get("day_change_pct", 0)
        week_chg_pct = pa.get("week_change_pct", 0)
        month_chg_pct = pa.get("month_change_pct", 0)

        if week_chg_pct > 2.0: mom_pts += 10
        elif week_chg_pct < -2.0: mom_pts -= 10
        
        if month_chg_pct > 5.0: mom_pts += 14
        elif month_chg_pct < -5.0: mom_pts -= 14
        
        if day_chg_pct > 0.5: mom_pts += 6
        elif day_chg_pct < -0.5: mom_pts -= 6

        # Position in 52w range
        dist_low = pa.get("dist_from_52w_low_pct", 0)
        dist_high = pa.get("dist_to_52w_high_pct", 0)
        if dist_high < 10.0: mom_pts += 8 # Near yearly highs
        elif dist_low < 10.0: mom_pts -= 8 # Lagging near lows

        mom_score = int(max(10, min(95, round(mom_pts))))

        # --- 4. Sentiment Score (0-100) ---
        sent_score = sentiment.get("score", 50)

        # --- 5. Risk Score (0-100) --- (Higher = More risk)
        risk_pts = 40.0
        sr = technicals.get("support_resistance", {})
        dist_res = sr.get("dist_to_resistance_pct", 5.0)
        
        if dist_res < 1.5: risk_pts += 18  # Right at major ceiling
        elif dist_res < 3.0: risk_pts += 8

        if rsi_val >= 72: risk_pts += 15  # Stretched overbought
        if technicals.get("bollinger_bands", {}).get("percent_b", 0.5) >= 1.0: risk_pts += 10

        de = fundamentals.get("debt_to_equity")
        if de is not None and de > 150: risk_pts += 14  # High balance sheet leverage

        pe = fundamentals.get("pe_ratio")
        if pe is not None and pe > 65: risk_pts += 12  # Rich valuation multiple

        vol_ratio = vol.get("volume_ratio", 1.0)
        if vol_ratio > 2.5: risk_pts += 8  # Wild volume spike / volatility

        risk_score = int(max(15, min(92, round(risk_pts))))

        return {
            "technical_score": tech_score,
            "fundamental_score": fund_score,
            "momentum_score": mom_score,
            "sentiment_score": sent_score,
            "risk_score": risk_score
        }

    @classmethod
    def _generate_outlook(
        cls,
        scores: Dict[str, int],
        pa: Dict[str, Any],
        technicals: Dict[str, Any],
        fundamentals: Dict[str, Any],
        curr: str
    ) -> Dict[str, Any]:
        """
        Synthesizes the 5 scores into:
        - Outlook (BULLISH / MODERATELY BULLISH / NEUTRAL / MODERATELY BEARISH / BEARISH)
        - Potential Direction (UPWARD / SIDEWAYS / DOWNWARD)
        - Confidence % (Analytical confidence, explicitly NOT a guarantee)
        - 'Why?' list of positive and cautionary factors
        - Summary narrative
        """
        t = scores["technical_score"]
        f = scores["fundamental_score"]
        m = scores["momentum_score"]
        s = scores["sentiment_score"]
        r = scores["risk_score"]

        # Composite bullish index (weighted)
        composite = (t * 0.40) + (m * 0.25) + (f * 0.20) + (s * 0.15)
        
        # Classification
        if composite >= 72:
            outlook = "BULLISH"
            direction = "UPWARD"
            base_conf = 72 + int((composite - 72) * 0.5)
        elif composite >= 58:
            outlook = "MODERATELY BULLISH"
            direction = "UPWARD"
            base_conf = 65 + int((composite - 58) * 0.5)
        elif composite >= 44:
            outlook = "NEUTRAL"
            direction = "SIDEWAYS"
            base_conf = 60 + int(abs(composite - 50) * 0.4)
        elif composite >= 30:
            outlook = "MODERATELY BEARISH"
            direction = "DOWNWARD"
            base_conf = 65 + int((44 - composite) * 0.5)
        else:
            outlook = "BEARISH"
            direction = "DOWNWARD"
            base_conf = 72 + int((30 - composite) * 0.5)

        # Risk adjustment to confidence (if risk is very high, confidence in sustained trending softens)
        confidence = max(55, min(86, base_conf - int(max(0, r - 65) * 0.25)))

        # Build "Why?" itemized drivers
        factors: List[Dict[str, str]] = []
        ma = technicals.get("moving_averages", {})
        sr = technicals.get("support_resistance", {})
        rsi = technicals.get("rsi", {})
        macd = technicals.get("macd", {})
        vol = technicals.get("volume", {})

        # Moving average checks
        if ma.get("is_above_sma50") and ma.get("sma_50"):
            factors.append({
                "type": "positive",
                "text": f"Price is trading comfortably above the 50-day moving average ({curr}{ma['sma_50']:,})"
            })
        elif not ma.get("is_above_sma50") and ma.get("sma_50"):
            factors.append({
                "type": "caution",
                "text": f"Price is trading below the 50-day moving average ({curr}{ma['sma_50']:,}), indicating medium-term overhead pressure"
            })

        if ma.get("is_above_sma200") and ma.get("sma_200"):
            factors.append({
                "type": "positive",
                "text": f"Long-term structural uptrend intact above 200-day moving average ({curr}{ma['sma_200']:,})"
            })

        # MACD
        if macd.get("histogram", 0) > 0:
            factors.append({
                "type": "positive",
                "text": f"Positive MACD momentum ({macd.get('status', 'Bullish')})"
            })
        else:
            factors.append({
                "type": "caution",
                "text": f"Negative MACD divergence with histogram in bearish zone"
            })

        # RSI
        rsi_val = rsi.get("value", 50)
        if 50 <= rsi_val <= 68:
            factors.append({
                "type": "positive",
                "text": f"RSI at {rsi_val} reflects constructive momentum without being overextended"
            })
        elif rsi_val > 68:
            factors.append({
                "type": "caution",
                "text": f"RSI at {rsi_val} is nearing overbought levels, indicating potential for short-term consolidation"
            })
        elif rsi_val < 35:
            factors.append({
                "type": "neutral",
                "text": f"RSI at {rsi_val} is in deeply oversold territory, raising likelihood of technical bargain-hunting"
            })

        # Volume
        if vol.get("volume_ratio", 1.0) >= 1.25:
            factors.append({
                "type": "positive" if pa.get("day_change", 0) >= 0 else "caution",
                "text": f"Elevated volume ({vol.get('volume_ratio')}x 20-day average) confirming active institutional interest"
            })

        # Resistance Warning
        imm_res = sr.get("immediate_resistance")
        if imm_res:
            factors.append({
                "type": "caution",
                "text": f"Immediate resistance ceiling identified near {curr}{imm_res:,} ({sr.get('dist_to_resistance_pct', 0)}% away)"
            })

        # Fundamentals factor
        if fundamentals.get("available"):
            if fundamentals.get("score", 50) >= 65:
                factors.append({
                    "type": "positive",
                    "text": f"Solid fundamental profile: {fundamentals.get('health', 'Healthy')} with attractive return metrics"
                })
            elif fundamentals.get("score", 50) <= 40:
                factors.append({
                    "type": "caution",
                    "text": f"Fundamental valuation or leverage warrants caution (Health: {fundamentals.get('health', 'Stretched')})"
                })

        # Narrative Summary
        p_chg = pa.get("day_change_pct", 0)
        curr_p = pa.get("current_price", 0)
        summary = (
            f"The stock is currently showing a {outlook.lower()} setup at {curr}{curr_p:,} ({'+' if p_chg>=0 else ''}{p_chg}% today). "
            f"Technicals reflect a score of {t}/100, supported by {technicals.get('summary', {}).get('trend_direction', 'stable trends')}. "
            f"While momentum score is {m}/100, proximity to resistance near {curr}{imm_res:,} suggests potential consolidation before any extended breakout."
        )

        return {
            "outlook": outlook,
            "potential_direction": direction,
            "confidence_pct": confidence,
            "confidence_note": "Analytical confidence in pattern classification, not a directional price guarantee.",
            "factors": factors[:6],
            "summary": summary
        }

    @classmethod
    def _generate_risk_analysis(
        cls,
        scores: Dict[str, int],
        pa: Dict[str, Any],
        technicals: Dict[str, Any],
        fundamentals: Dict[str, Any],
        curr: str
    ) -> Dict[str, Any]:
        """Identifies specific risk items (volatility, overbought, resistance, etc.)"""
        rsi_val = technicals.get("rsi", {}).get("value", 50)
        sr = technicals.get("support_resistance", {})
        vol = technicals.get("volume", {})
        dist_res = sr.get("dist_to_resistance_pct", 5.0)
        
        risks = []
        
        if rsi_val >= 70:
            risks.append({"title": "Overbought Condition", "level": "High", "desc": f"RSI is currently {rsi_val}, suggesting stretched valuation in the very short term."})
        elif rsi_val <= 30:
            risks.append({"title": "Oversold Condition", "level": "Medium", "desc": f"RSI is depressed at {rsi_val}, reflecting severe selling pressure."})
        else:
            risks.append({"title": "Momentum State", "level": "Low", "desc": f"RSI is balanced at {rsi_val} with no extreme exhaustion signals."})

        if dist_res <= 2.0:
            risks.append({"title": "Strong Overhead Resistance", "level": "High", "desc": f"Price is within {dist_res}% of immediate supply zone ({curr}{sr.get('immediate_resistance')})."})
        else:
            risks.append({"title": "Resistance Cushion", "level": "Low", "desc": f"Has {dist_res}% head-room before testing immediate resistance."})

        if vol.get("volume_ratio", 1.0) >= 2.0:
            risks.append({"title": "Unusual Volume Surge", "level": "Medium", "desc": f"Volume is running {vol.get('volume_ratio')}x normal, which often brings sharp intraday whipsaws."})

        de = fundamentals.get("debt_to_equity")
        if de is not None and de > 150:
            risks.append({"title": "Balance Sheet Leverage", "level": "High", "desc": f"Debt-to-equity of {de}% indicates high financial leverage."})
        elif fundamentals.get("pe_ratio") and fundamentals["pe_ratio"] > 60:
            risks.append({"title": "Valuation Premium", "level": "Medium", "desc": f"Stock trades at a high P/E multiple of {fundamentals['pe_ratio']}x earnings."})

        return {
            "overall_risk_score": scores["risk_score"],
            "risk_level": "Elevated" if scores["risk_score"] >= 65 else ("Moderate" if scores["risk_score"] >= 45 else "Low / Defensive"),
            "risk_factors": risks
        }

    @classmethod
    def _generate_scenarios(
        cls,
        pa: Dict[str, Any],
        technicals: Dict[str, Any],
        curr: str
    ) -> Dict[str, Any]:
        """Generates Bullish, Neutral, and Bearish scenarios with exact levels"""
        curr_p = pa.get("current_price", 0)
        sr = technicals.get("support_resistance", {})
        imm_sup = sr.get("immediate_support", curr_p * 0.97)
        strong_sup = sr.get("strong_support", curr_p * 0.94)
        imm_res = sr.get("immediate_resistance", curr_p * 1.03)
        strong_res = sr.get("strong_resistance", curr_p * 1.06)

        return {
            "disclaimer": "These scenarios represent hypothetical analytical pathways based on support/resistance pivots, not guaranteed price forecasts.",
            "bullish": {
                "title": "Bullish Scenario",
                "trigger": f"Decisive close above immediate resistance at {curr}{imm_res:,} with volume expansion",
                "target_levels": f"{curr}{strong_res:,} (Secondary supply zone / 52w highs)",
                "conditions": "Sustained buying interest, institutional volume confirmation, and broader market index stability.",
                "invalidation": f"Rejection at {curr}{imm_res:,} followed by a slip below {curr}{imm_sup:,}."
            },
            "neutral": {
                "title": "Neutral / Sideways Scenario",
                "trigger": f"Price oscillates within the defined range between {curr}{imm_sup:,} and {curr}{imm_res:,}",
                "target_levels": f"{curr}{sr.get('pivot_point', curr_p):,} (Equilibrium pivot)",
                "conditions": "Decreasing trading volume, lack of fresh sector triggers, and balanced buyers vs sellers.",
                "invalidation": f"Strong directional breakout above {curr}{imm_res:,} or breakdown below {curr}{imm_sup:,}."
            },
            "bearish": {
                "title": "Bearish Scenario",
                "trigger": f"Failure to hold immediate support at {curr}{imm_sup:,} on rising sell volume",
                "target_levels": f"{curr}{strong_sup:,} (Major structural support / moving average floor)",
                "conditions": "Negative broader market breadth, breakdown below short-term 20 EMA, or headline headwinds.",
                "invalidation": f"Immediate V-shaped reclaim of {curr}{imm_sup:,} with aggressive dip buying."
            }
        }

    @classmethod
    def _generate_timeframes(
        cls,
        scores: Dict[str, int],
        pa: Dict[str, Any],
        technicals: Dict[str, Any],
        fundamentals: Dict[str, Any],
        curr: str
    ) -> List[Dict[str, Any]]:
        """
        Calculates separate analysis for:
        - Intraday
        - Short Term (1–5 trading days)
        - Swing (1–4 weeks)
        - Medium Term (1–6 months)
        """
        curr_p = pa.get("current_price", 0)
        sr = technicals.get("support_resistance", {})
        ma = technicals.get("moving_averages", {})
        imm_sup = sr.get("immediate_support", curr_p * 0.98)
        imm_res = sr.get("immediate_resistance", curr_p * 1.02)
        strong_sup = sr.get("strong_support", curr_p * 0.95)
        strong_res = sr.get("strong_resistance", curr_p * 1.05)
        t_score = scores["technical_score"]
        f_score = scores["fundamental_score"]
        m_score = scores["momentum_score"]

        # Intraday
        intraday_dir = "UPWARD" if pa.get("day_change", 0) > 0 and technicals.get("rsi", {}).get("value", 50) > 50 else ("DOWNWARD" if pa.get("day_change", 0) < 0 else "SIDEWAYS")
        intraday_conf = 62 + (5 if abs(pa.get("day_change_pct", 0)) > 1.0 else 0)

        # Short Term (1-5 days)
        short_dir = "UPWARD" if t_score >= 58 and m_score >= 50 else ("DOWNWARD" if t_score <= 42 else "SIDEWAYS")
        short_conf = max(55, min(80, int((t_score + m_score) / 2 * 0.9)))

        # Swing (1-4 weeks)
        swing_dir = "UPWARD" if ma.get("is_above_sma50") and t_score >= 52 else ("DOWNWARD" if not ma.get("is_above_sma50") and t_score <= 45 else "SIDEWAYS")
        swing_conf = max(58, min(82, int((t_score * 0.6 + f_score * 0.4))))

        # Medium Term (1-6 months)
        med_dir = "UPWARD" if ma.get("is_above_sma200") and f_score >= 55 else ("DOWNWARD" if not ma.get("is_above_sma200") and f_score <= 45 else "SIDEWAYS")
        med_conf = max(60, min(85, int((f_score * 0.6 + t_score * 0.4))))

        return [
            {
                "timeframe": "Intraday",
                "label": "Today's Session",
                "direction": intraday_dir,
                "confidence_pct": intraday_conf,
                "key_levels": f"Day Range: {curr}{pa.get('day_low', curr_p):,} – {curr}{pa.get('day_high', curr_p):,}",
                "main_reasons": f"Session momentum ({pa.get('day_change_pct', 0)}%) and intraday volume pacing ({technicals.get('volume', {}).get('status', 'Normal')}).",
                "risks": "Sudden broader index swings and market-close squaring off volatility."
            },
            {
                "timeframe": "Short Term (1–5 Days)",
                "label": "1–5 Trading Days",
                "direction": short_dir,
                "confidence_pct": short_conf,
                "key_levels": f"Support: {curr}{imm_sup:,} | Resistance: {curr}{imm_res:,}",
                "main_reasons": f"RSI momentum ({technicals.get('rsi', {}).get('value', 50)}) and alignment with short-term EMA 9 & 21.",
                "risks": f"Failure to hold immediate support at {curr}{imm_sup:,} on market profit-taking."
            },
            {
                "timeframe": "Swing (1–4 Weeks)",
                "label": "1–4 Weeks",
                "direction": swing_dir,
                "confidence_pct": swing_conf,
                "key_levels": f"Support: {curr}{imm_sup:,} | Target: {curr}{strong_res:,}",
                "main_reasons": f"50-day moving average positioning and MACD trend cycle state.",
                "risks": "Upcoming economic data releases, sector rotation, or consolidation at upper Bollinger Band."
            },
            {
                "timeframe": "Medium Term (1–6 Months)",
                "label": "1–6 Months",
                "direction": med_dir,
                "confidence_pct": med_conf,
                "key_levels": f"Major Support: {curr}{strong_sup:,} | Major Resistance: {curr}{pa.get('fifty_two_week_high', curr_p):,}",
                "main_reasons": f"Fundamental score ({f_score}/100), long-term 200 SMA structural support, and quarterly earnings trajectory.",
                "risks": "Macro interest rate policy shifts, inflation prints, and sector valuation multiple contractions."
            }
        ]
