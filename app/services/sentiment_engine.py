"""
Market & Sentiment Analysis Engine - News NLP scoring, sector context, and institutional activity
"""
from typing import Dict, Any, List


class SentimentEngine:
    BULLISH_KEYWORDS = [
        "gain", "profit", "surge", "order", "contract", "deal", "win", "high", "growth",
        "buy", "upgrade", "expansion", "beat", "rally", "record", "jump", "bull", "dividend",
        "partnership", "strong", "outperform", "robust", "hike", "positive"
    ]
    
    BEARISH_KEYWORDS = [
        "loss", "fall", "drop", "plunge", "cut", "probe", "down", "sell", "downgrade",
        "penalty", "notice", "fraud", "default", "slump", "bear", "weak", "miss", "drag",
        "caution", "investigation", "decline", "debt", "curb", "negative"
    ]

    @classmethod
    def analyze(cls, news_items: List[Dict[str, Any]], sector: str = "General", inst_holding_pct: float = None) -> Dict[str, Any]:
        """
        Calculates a Sentiment Score (0-100) based on news headline NLP,
        institutional ownership dynamics, and sector sentiment.
        """
        if not news_items:
            return {
                "score": 50,
                "label": "Neutral / Balanced",
                "summary": "No recent major news headlines detected. Sentiment remains neutral.",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "institutional_activity": "Stable / Normal",
                "news": []
            }

        pos_count = 0
        neg_count = 0
        neu_count = 0
        enriched_news = []

        for item in news_items:
            title = item.get("title", "")
            title_lower = title.lower()
            
            p_score = sum(1 for w in cls.BULLISH_KEYWORDS if w in title_lower)
            n_score = sum(1 for w in cls.BEARISH_KEYWORDS if w in title_lower)
            
            if p_score > n_score:
                sent = "positive"
                pos_count += 1
            elif n_score > p_score:
                sent = "negative"
                neg_count += 1
            else:
                sent = "neutral"
                neu_count += 1
                
            enriched_news.append({
                **item,
                "sentiment": sent
            })

        total = len(news_items)
        # Compute baseline news sentiment (0 - 100)
        # If all positive -> 90, if all negative -> 15, balanced -> 50
        sentiment_delta = ((pos_count - neg_count) / max(total, 1)) * 35.0
        score = 50.0 + sentiment_delta
        
        # Institutional holding modifier
        inst_note = "Normal Institutional Participation"
        if inst_holding_pct is not None:
            if inst_holding_pct >= 60:
                score += 5
                inst_note = f"High Institutional Backing ({inst_holding_pct:.1f}% FII/DII)"
            elif inst_holding_pct <= 10:
                inst_note = f"Low Institutional Float ({inst_holding_pct:.1f}% FII/DII)"

        final_score = int(max(10, min(95, round(score))))
        
        if final_score >= 65:
            label = "Positive / Bullish News Flow"
            summary = f"News headlines lean favorably ({pos_count} positive mentions vs {neg_count} negative). Market sentiment is constructive."
        elif final_score <= 40:
            label = "Cautious / Bearish News Flow"
            summary = f"News flow reflects headline headwinds ({neg_count} negative mentions). Short-term sentiment is restrained."
        else:
            label = "Neutral / Balanced"
            summary = f"News flow is balanced ({pos_count} positive, {neg_count} negative, {neu_count} neutral). No significant headline shock."

        return {
            "score": final_score,
            "label": label,
            "summary": summary,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "neutral_count": neu_count,
            "institutional_activity": inst_note,
            "news": enriched_news
        }
