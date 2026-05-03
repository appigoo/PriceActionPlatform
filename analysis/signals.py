"""Signal Generation - BUY/SELL based on Price Action + Volume + Structure"""
import pandas as pd
import numpy as np


def generate_signals(df, patterns, market_struct, volume_analysis, sr_levels) -> dict:
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    vols = df['Volume'].values
    n = len(df)
    current = closes[-1]

    buy_score = 0
    sell_score = 0
    buy_reasons = []
    sell_reasons = []

    # ── Market Structure ─────────────────────────────────────────────────────
    trend = market_struct.get('trend', '')
    if "多頭" in trend:
        buy_score += 30
        buy_reasons.append("多頭市場結構 (HH+HL)")
    elif "空頭" in trend:
        sell_score += 30
        sell_reasons.append("空頭市場結構 (LH+LL)")
    elif "反轉" in trend:
        buy_score += 10

    # ── Volume ───────────────────────────────────────────────────────────────
    vol_sig = volume_analysis.get('vol_signal', '')
    vol_ratio = volume_analysis.get('vol_ratio', 1.0)
    if "低位爆量陽線" in vol_sig:
        buy_score += 25
        buy_reasons.append("低位爆量陽線")
    elif "放量突破" in vol_sig:
        buy_score += 20
        buy_reasons.append("放量突破")
    elif "高位爆量陰線" in vol_sig:
        sell_score += 25
        sell_reasons.append("高位爆量陰線")
    elif "放量下跌" in vol_sig:
        sell_score += 20
        sell_reasons.append("放量下跌")

    # ── Patterns ─────────────────────────────────────────────────────────────
    detected = patterns.get('detected', [])
    for p in detected[-5:]:
        if p['bias'] == 'bull':
            buy_score += 10
            buy_reasons.append(p['name'])
        elif p['bias'] == 'bear':
            sell_score += 10
            sell_reasons.append(p['name'])

    # ── Support/Resistance ───────────────────────────────────────────────────
    supports = sr_levels.get('supports', [])
    resistances = sr_levels.get('resistances', [])

    if supports:
        nearest_sup = supports[0]
        if abs(current - nearest_sup) / current < 0.02:
            buy_score += 15
            buy_reasons.append(f"回踩支撐 ${nearest_sup:.2f}")

    if resistances:
        nearest_res = resistances[0]
        if abs(current - nearest_res) / current < 0.02:
            sell_score += 15
            sell_reasons.append(f"觸及阻力 ${nearest_res:.2f}")

    # Structure break
    struct_break = market_struct.get('structure_break', '')
    if "突破阻力" in struct_break and vol_ratio > 1.3:
        buy_score += 20
        buy_reasons.append("放量突破阻力")
    elif "跌破支撐" in struct_break and vol_ratio > 1.3:
        sell_score += 20
        sell_reasons.append("放量跌破支撐")

    # ── Primary Signal ───────────────────────────────────────────────────────
    if buy_score >= 50 and buy_score > sell_score + 20:
        primary = "BUY"
        strength = "強" if buy_score >= 70 else "中"
    elif sell_score >= 50 and sell_score > buy_score + 20:
        primary = "SELL"
        strength = "強" if sell_score >= 70 else "中"
    else:
        primary = "NEUTRAL"
        strength = "弱"

    # ── Trade Setup ───────────────────────────────────────────────────────────
    key_support = supports[0] if supports else current * 0.97
    key_resistance = resistances[0] if resistances else current * 1.03
    breakout_level = resistances[0] if resistances else current * 1.03
    
    if primary == "BUY":
        stop_loss = key_support * 0.985
        target = key_resistance
        risk = current - stop_loss
        reward = target - current
    elif primary == "SELL":
        stop_loss = key_resistance * 1.015
        target = key_support
        risk = stop_loss - current
        reward = current - target
    else:
        stop_loss = current * 0.97
        target = current * 1.03
        risk = current - stop_loss
        reward = target - current

    rrr = f"1:{reward/risk:.1f}" if risk > 0 else "N/A"

    short_term = "看多 📈" if primary == "BUY" else ("看空 📉" if primary == "SELL" else "觀望 ⟷")
    mid_trend = market_struct.get('trend', '橫盤')
    mid_term = "多頭 ▲" if "多頭" in mid_trend else ("空頭 ▼" if "空頭" in mid_trend else "中性 ⟷")

    # ── Historical signals for backtest ──────────────────────────────────────
    signal_history = _generate_historical_signals(df, market_struct)

    return {
        "primary": primary,
        "strength": strength,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "buy_reasons": buy_reasons,
        "sell_reasons": sell_reasons,
        "trade_setup": {
            "short_term": short_term,
            "mid_term": mid_term,
            "key_support": key_support,
            "key_resistance": key_resistance,
            "breakout_level": breakout_level,
            "stop_loss": stop_loss,
            "rrr": rrr,
        },
        "signal_history": signal_history,
        "buy_arrows": [],
        "sell_arrows": [],
    }


def _generate_historical_signals(df, market_struct):
    """Simple historical signal generation for backtest"""
    signals = []
    closes = df['Close'].values
    vols = df['Volume'].values
    n = len(df)
    avg_vol = np.mean(vols[-20:]) if n >= 20 else np.mean(vols)
    
    for i in range(5, n - 1):
        price_momentum = (closes[i] - closes[i-5]) / closes[i-5]
        vol_r = vols[i] / avg_vol
        
        if price_momentum > 0.02 and vol_r > 1.3:
            signals.append({"index": i, "type": "BUY", "price": closes[i]})
        elif price_momentum < -0.02 and vol_r > 1.3:
            signals.append({"index": i, "type": "SELL", "price": closes[i]})
    
    return signals
