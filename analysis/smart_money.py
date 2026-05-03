"""Smart Money Concept (SMC) Analysis"""
import pandas as pd
import numpy as np


def analyze_smart_money(df: pd.DataFrame, vol_analysis: dict) -> dict:
    closes = df['Close'].values
    opens = df['Open'].values
    highs = df['High'].values
    lows = df['Low'].values
    vols = df['Volume'].values
    n = len(df)

    avg_vol = np.mean(vols[-20:]) if n >= 20 else np.mean(vols)
    current = closes[-1]
    mean_20 = np.mean(closes[-20:]) if n >= 20 else np.mean(closes)

    # ── Liquidity Grab Detection ─────────────────────────────────────────────
    # Fake breakdown: price broke below recent low then recovered
    recent_low_5 = min(lows[-6:-1]) if n >= 6 else lows[0]
    liquidity_grab = "無"
    if lows[-1] < recent_low_5 and closes[-1] > recent_low_5:
        liquidity_grab = "疑似下方流動性清洗 ↓↑"
    elif highs[-1] > max(highs[-6:-1]) and closes[-1] < max(highs[-6:-1]) if n >= 6 else False:
        liquidity_grab = "疑似上方流動性清洗 ↑↓"

    # ── Stop Hunt ────────────────────────────────────────────────────────────
    stop_hunt = False
    if n >= 3:
        range_before = highs[-3] - lows[-3]
        if (lows[-1] < lows[-2] - range_before * 0.3 and
                closes[-1] > lows[-2]):
            stop_hunt = True

    # ── Accumulation Probability ─────────────────────────────────────────────
    accum_score = 0
    # Low position
    if current < mean_20: accum_score += 25
    # Volume with bullish close
    if vols[-1] > avg_vol and closes[-1] > opens[-1]: accum_score += 25
    # Lower shadow
    lower_shadow = min(closes[-1], opens[-1]) - lows[-1]
    body = abs(closes[-1] - opens[-1])
    if lower_shadow > body: accum_score += 20
    # Liquidity grab
    if "下方" in liquidity_grab: accum_score += 30

    # ── Distribution Risk ────────────────────────────────────────────────────
    dist_score = 0
    if current > mean_20: dist_score += 25
    if vols[-1] > avg_vol * 1.5 and closes[-1] < opens[-1]: dist_score += 30
    upper_shadow = highs[-1] - max(closes[-1], opens[-1])
    if upper_shadow > body: dist_score += 25
    if "上方" in liquidity_grab: dist_score += 20

    accum_score = min(accum_score, 100)
    dist_score = min(dist_score, 100)

    # ── Behavior Classification ───────────────────────────────────────────────
    if accum_score > 70:
        behavior = "主力吸籌"
        fakeout_risk = "低"
    elif dist_score > 70:
        behavior = "主力派發"
        fakeout_risk = "高"
    elif stop_hunt:
        behavior = "Stop Hunt"
        fakeout_risk = "中"
    elif "清洗" in liquidity_grab:
        behavior = "流動性清洗"
        fakeout_risk = "中"
    elif vols[-1] > avg_vol * 2.5:
        behavior = "爆量異動"
        fakeout_risk = "中"
    else:
        behavior = "正常波動"
        fakeout_risk = "低"

    # ── Natural Language Description ─────────────────────────────────────────
    desc = _build_description(behavior, liquidity_grab, vol_analysis, current, mean_20)

    return {
        "behavior": behavior,
        "accumulation_prob": accum_score,
        "distribution_risk": dist_score,
        "liquidity_grab": liquidity_grab,
        "stop_hunt": "是" if stop_hunt else "否",
        "fakeout_risk": fakeout_risk,
        "description": desc,
    }


def _build_description(behavior, liquidity_grab, vol_analysis, current, mean20):
    desc_parts = []

    if behavior == "主力吸籌":
        desc_parts.append("價格處於低位，出現放量多頭K線，主力資金跡象明顯進場吸籌。")
    elif behavior == "主力派發":
        desc_parts.append("高位出現大量拋壓，爆量陰線顯示主力派發風險升高，建議謹慎追高。")
    elif behavior == "Stop Hunt":
        desc_parts.append("價格短暫跌破近期低點後迅速拉回，疑似主力掃除止損單後重新吸籌。")
    elif behavior == "流動性清洗":
        if "下方" in liquidity_grab:
            desc_parts.append("價格跌破前低後快速收回，伴隨爆量長下影，疑似主力進行流動性清洗後吸籌。")
        else:
            desc_parts.append("價格假突破前高後迅速回落，疑似主力誘多後打壓出貨。")
    elif behavior == "爆量異動":
        desc_parts.append(f"成交量異常放大至均量 {vol_analysis.get('vol_ratio', 0):.1f} 倍，市場出現重大資金異動，方向待確認。")
    else:
        desc_parts.append("目前無明顯主力異常行為，市場處於正常波動狀態。")

    if vol_analysis.get('extra_signal'):
        desc_parts.append(vol_analysis['extra_signal'])

    return " ".join(desc_parts)
