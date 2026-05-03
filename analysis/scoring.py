"""Scoring System"""


def compute_scores(market_struct, volume_analysis, smart_money, signals) -> dict:
    trend_strength = market_struct.get('trend_strength', 50)
    accum_score = smart_money.get('accumulation_prob', 0)
    dist_score = smart_money.get('distribution_risk', 0)
    vol_ratio = volume_analysis.get('vol_ratio', 1.0)

    # Breakout score
    struct_break = market_struct.get('structure_break', '')
    breakout_score = 0
    if "突破阻力" in struct_break:
        breakout_score = min(50 + int(vol_ratio * 15), 100)
    elif "跌破支撐" in struct_break:
        breakout_score = max(50 - int(vol_ratio * 15), 0)
    else:
        breakout_score = 45

    fakeout_score = smart_money.get('distribution_risk', 30)

    # Overall rating
    buy_score = signals.get('buy_score', 0)
    sell_score = signals.get('sell_score', 0)
    confidence = max(buy_score, sell_score, 10)

    if buy_score >= 70:
        overall_rating = "強烈看多 🚀"
    elif buy_score >= 50:
        overall_rating = "偏多 📈"
    elif sell_score >= 70:
        overall_rating = "強烈看空 💀"
    elif sell_score >= 50:
        overall_rating = "偏空 📉"
    else:
        overall_rating = "中性 ⟷"

    return {
        "trend_strength": trend_strength,
        "accumulation_score": accum_score,
        "distribution_score": dist_score,
        "breakout_score": breakout_score,
        "fakeout_score": fakeout_score,
        "overall_rating": overall_rating,
        "confidence": min(confidence, 95),
    }
