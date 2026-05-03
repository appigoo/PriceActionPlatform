"""Market Structure Analysis - Higher High/Low, Lower High/Low, Trend Detection"""
import pandas as pd
import numpy as np


def find_swing_points(df: pd.DataFrame, window: int = 5) -> dict:
    highs = df['High'].values
    lows = df['Low'].values
    n = len(df)

    swing_highs = []
    swing_lows = []

    for i in range(window, n - window):
        if highs[i] == max(highs[i-window:i+window+1]):
            swing_highs.append((i, highs[i]))
        if lows[i] == min(lows[i-window:i+window+1]):
            swing_lows.append((i, lows[i]))

    return {"swing_highs": swing_highs[-8:], "swing_lows": swing_lows[-8:]}


def analyze_market_structure(df: pd.DataFrame) -> dict:
    swings = find_swing_points(df)
    sh = swings['swing_highs']
    sl = swings['swing_lows']

    if len(sh) < 2 or len(sl) < 2:
        return {
            "trend": "橫盤整理",
            "sub_trend": "數據不足",
            "swing_desc": "N/A",
            "trend_strength": 50,
            "market_state": "觀望",
            "structure_break": "無",
            "swing_highs": sh,
            "swing_lows": sl,
        }

    # Compare last two swings
    hh = sh[-1][1] > sh[-2][1]  # Higher High
    hl = sl[-1][1] > sl[-2][1]  # Higher Low
    lh = sh[-1][1] < sh[-2][1]  # Lower High
    ll = sl[-1][1] < sl[-2][1]  # Lower Low

    # Determine trend
    if hh and hl:
        trend = "多頭趨勢"
        sub = "Higher High + Higher Low 結構確認"
        swing_desc = "HH ▲ + HL ▲"
        strength_base = 80
    elif lh and ll:
        trend = "空頭趨勢"
        sub = "Lower High + Lower Low 結構確認"
        swing_desc = "LH ▼ + LL ▼"
        strength_base = 20
    elif hh and ll:
        trend = "趨勢反轉中"
        sub = "結構出現背離，需觀察確認"
        swing_desc = "HH ▲ + LL ▼ (發散)"
        strength_base = 50
    elif lh and hl:
        trend = "橫盤收斂"
        sub = "三角收斂，蓄勢待發"
        swing_desc = "LH ▼ + HL ▲ (收斂)"
        strength_base = 55
    else:
        trend = "橫盤整理"
        sub = "區間震盪"
        swing_desc = "無明確結構"
        strength_base = 45

    # Trend strength from price momentum
    closes = df['Close'].values
    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    current = closes[-1]

    above_ema20 = current > ema20[-1]
    above_ema50 = current > ema50[-1]
    ema_aligned = ema20[-1] > ema50[-1]

    strength = strength_base
    if "多頭" in trend:
        if above_ema20: strength = min(strength + 10, 100)
        if above_ema50: strength = min(strength + 5, 100)
        if ema_aligned: strength = min(strength + 5, 100)
    elif "空頭" in trend:
        if not above_ema20: strength = max(strength - 10, 0)
        if not above_ema50: strength = max(strength - 5, 0)
        if not ema_aligned: strength = max(strength - 5, 0)

    # Structure break detection
    recent_high = max(df['High'].values[-20:])
    recent_low = min(df['Low'].values[-20:])
    last_close = df['Close'].iloc[-1]

    if last_close > recent_high * 0.999:
        struct_break = "突破阻力 ↑"
    elif last_close < recent_low * 1.001:
        struct_break = "跌破支撐 ↓"
    else:
        struct_break = "區間內"

    # Market state
    vol_20 = df['Close'].rolling(20).std().iloc[-1]
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
    if atr > vol_20 * 1.5:
        market_state = "高波動突破"
    elif atr < vol_20 * 0.5:
        market_state = "低波動蓄勢"
    else:
        market_state = "正常波動"

    return {
        "trend": trend,
        "sub_trend": sub,
        "swing_desc": swing_desc,
        "trend_strength": int(strength),
        "market_state": market_state,
        "structure_break": struct_break,
        "swing_highs": sh,
        "swing_lows": sl,
        "ema20": ema20,
        "ema50": ema50,
        "hh": hh, "hl": hl, "lh": lh, "ll": ll,
    }


def _ema(data, period):
    k = 2 / (period + 1)
    ema = np.zeros(len(data))
    ema[0] = data[0]
    for i in range(1, len(data)):
        ema[i] = data[i] * k + ema[i-1] * (1 - k)
    return ema
