"""
Fundamental Analysis Engine - Valuation ratios, balance sheet health, growth, and ownership metrics
"""
from typing import Dict, Any, Optional


def format_market_cap(mcap: Optional[float], currency: str = "INR") -> str:
    """Format market cap into Indian Cr / Lakh Cr or Billions for USD"""
    if mcap is None or mcap <= 0:
        return "Not Available"
    
    if currency == "INR":
        # Indian Crore formatting: 1 Cr = 10,000,000 (10^7)
        crores = mcap / 1e7
        if crores >= 100000:
            lakh_cr = crores / 100000
            return f"₹ {lakh_cr:.2f} Lakh Cr"
        else:
            return f"₹ {crores:,.0f} Cr"
    else:
        # USD formatting
        if mcap >= 1e12:
            return f"${mcap / 1e12:.2f} Trillion"
        elif mcap >= 1e9:
            return f"${mcap / 1e9:.2f} Billion"
        elif mcap >= 1e6:
            return f"${mcap / 1e6:.2f} Million"
        return f"${mcap:,.0f}"


class FundamentalEngine:
    @staticmethod
    def analyze(info: Dict[str, Any], currency: str = "INR") -> Dict[str, Any]:
        """
        Analyzes valuation, profitability, leverage, growth, and holdings.
        Computes a transparent Fundamental Score (0-100).
        """
        if not info:
            return {
                "available": False,
                "score": 50,
                "summary": "Fundamental data not available for this ticker."
            }

        mcap = info.get("marketCap")
        pe = info.get("trailingPE")
        fwd_pe = info.get("forwardPE")
        pb = info.get("priceToBook")
        eps = info.get("trailingEps")
        roe = info.get("returnOnEquity")
        roce = info.get("roce")  # May be calculated or provided in demo
        debt_to_equity = info.get("debtToEquity")
        rev_growth = info.get("revenueGrowth")
        profit_growth = info.get("earningsGrowth")
        div_yield = info.get("dividendYield")
        promoter_holding = info.get("heldPercentInsiders")
        inst_holding = info.get("heldPercentInstitutions")
        
        sector = info.get("sector", "General")
        industry = info.get("industry", "Diversified")
        is_financial = any(w in (sector + industry).lower() for w in ["bank", "financial", "nbfc", "insurance"])

        # Valuation Assessment
        pe_status = "N/A"
        if pe is not None:
            if pe < 15:
                pe_status = "Attractive / Value"
            elif pe <= 30:
                pe_status = "Fairly Valued"
            elif pe <= 50:
                pe_status = "Growth Premium"
            else:
                pe_status = "High Valuation"

        # Debt Assessment
        debt_status = "N/A"
        if debt_to_equity is not None:
            if is_financial:
                debt_status = "Banking Typical (High Leverage Normal)"
            else:
                # Yahoo Finance sometimes reports debtToEquity as a percentage (e.g., 36.65 for 0.3665)
                # or ratio (e.g., 0.36)
                de_ratio = debt_to_equity / 100.0 if debt_to_equity > 5.0 else debt_to_equity
                if de_ratio < 0.4:
                    debt_status = "Low Debt / Conservative"
                elif de_ratio <= 1.0:
                    debt_status = "Manageable Leverage"
                else:
                    debt_status = "High Leverage (Monitor closely)"

        # Profitability Assessment
        roe_status = "N/A"
        if roe is not None:
            if roe > 0.20:
                roe_status = "Exceptional (> 20%)"
            elif roe >= 0.12:
                roe_status = "Healthy (12% – 20%)"
            elif roe > 0:
                roe_status = "Modest (< 12%)"
            else:
                roe_status = "Negative ROE"

        # Ownership Assessment
        promoter_pct = round(promoter_holding * 100, 2) if promoter_holding is not None else None
        inst_pct = round(inst_holding * 100, 2) if inst_holding is not None else None
        
        ownership_note = "Balanced Shareholding"
        if promoter_pct is not None and promoter_pct > 50:
            ownership_note = "High Promoter Commitment (>50%)"
        elif inst_pct is not None and inst_pct > 50:
            ownership_note = "Heavy Institutional Backing (>50%)"

        # Fundamental Score calculation (0 - 100)
        # Transparent rule-based point allocation
        score = 50.0
        factors_evaluated = 0
        
        # P/E valuation points (max +15 / -15)
        if pe is not None:
            factors_evaluated += 1
            if pe < 15: score += 12
            elif pe < 25: score += 8
            elif pe < 40: score += 0
            elif pe > 60: score -= 10
            
        # ROE points (max +15 / -10)
        if roe is not None:
            factors_evaluated += 1
            if roe >= 0.20: score += 15
            elif roe >= 0.12: score += 8
            elif roe < 0.05: score -= 8
            
        # Debt points (max +12 / -12)
        if debt_to_equity is not None and not is_financial:
            factors_evaluated += 1
            de_val = debt_to_equity / 100.0 if debt_to_equity > 5.0 else debt_to_equity
            if de_val < 0.3: score += 12
            elif de_val < 0.8: score += 5
            elif de_val > 1.5: score -= 12
        elif is_financial:
            score += 5 # Neutral credit profile baseline
            
        # Revenue & Profit Growth points (max +15 / -10)
        if rev_growth is not None:
            factors_evaluated += 1
            if rev_growth > 0.15: score += 8
            elif rev_growth > 0.05: score += 4
            elif rev_growth < -0.05: score -= 6
            
        if profit_growth is not None:
            factors_evaluated += 1
            if profit_growth > 0.15: score += 7
            elif profit_growth > 0: score += 3
            elif profit_growth < -0.15: score -= 8

        # Ownership points
        if promoter_pct is not None and promoter_pct >= 50:
            score += 5
        if inst_pct is not None and inst_pct >= 25:
            score += 5

        final_score = int(max(15, min(95, round(score))))
        
        # Health classification
        if final_score >= 75:
            health = "Robust & Healthy"
        elif final_score >= 60:
            health = "Stable / Moderate"
        elif final_score >= 45:
            health = "Fair / Average"
        else:
            health = "Stretched / High Caution"

        return {
            "available": True,
            "score": final_score,
            "health": health,
            "market_cap": mcap,
            "market_cap_formatted": format_market_cap(mcap, currency),
            "pe_ratio": round(pe, 2) if pe is not None else None,
            "forward_pe": round(fwd_pe, 2) if fwd_pe is not None else None,
            "pe_status": pe_status,
            "pb_ratio": round(pb, 2) if pb is not None else None,
            "eps": round(eps, 2) if eps is not None else None,
            "roe_pct": round(roe * 100, 2) if roe is not None else None,
            "roe_status": roe_status,
            "roce_pct": round(roce * 100, 2) if roce is not None else None,
            "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity is not None else None,
            "debt_status": debt_status,
            "revenue_growth_pct": round(rev_growth * 100, 2) if rev_growth is not None else None,
            "profit_growth_pct": round(profit_growth * 100, 2) if profit_growth is not None else None,
            "dividend_yield_pct": round(div_yield * 100, 2) if div_yield is not None else None,
            "promoter_holding_pct": promoter_pct,
            "institutional_holding_pct": inst_pct,
            "ownership_note": ownership_note,
            "sector": sector,
            "industry": industry
        }
