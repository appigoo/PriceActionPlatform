"""
市場結構分析
Higher High / Higher Low / Lower High / Lower Low
+ 趨勢反轉偵測（大趨勢空頭但局部轉多）
"""
import numpy as np
import pandas as pd


def _ema(data, period):
    k = 2 / (period + 1)
    ema = np.zeros(len(data))
    ema[0] = data[0]
    for i in range(1, len(data)):
        ema[i] = data[i] * k + ema[i-1] * (1 - k)
    return ema


def find_swing_points(df: pd.DataFrame, window: int = 5) -> dict:
    highs = df['High'].values
    lows  = df['Low'].values
    n = len(df)
    sh, sl = [], []
    for i in range(window, n - window):
        if highs[i] == max(highs[i-window:i+window+1]):
            sh.append((i, highs[i]))
        if lows[i] == min(lows[i-window:i+window+1]):
            sl.append((i, lows[i]))
    return {"swing_highs": sh[-10:], "swing_lows": sl[-10:]}


def analyze_market_structure(df: pd.DataFrame) -> dict:
    swings = find_swing_points(df)
    sh = swings['swing_highs']
    sl = swings['swing_lows']

    closes = df['Close'].values
    highs  = df['High'].values
    lows   = df['Low'].values
    n = len(df)

    ema20 = _ema(closes, 20)
    ema50 = _ema(closes, 50)
    current = closes[-1]

    if len(sh) < 2 or len(sl) < 2:
        return _default_struct(ema20, ema50, current, highs, lows, n)

    # 最近兩個擺動高低點
    hh = sh[-1][1] > sh[-2][1]   # Higher High
    hl = sl[-1][1] > sl[-2][1]   # Higher Low
    lh = sh[-1][1] < sh[-2][1]   # Lower High
    ll = sl[-1][1] < sl[-2][1]   # Lower Low

    # ── 全局趨勢（用較長期EMA判斷）──────────────────────────────────────────
    ema50_slope = (ema50[-1] - ema50[-10]) / (ema50[-10] + 1e-9) * 100
    ema20_slope = (ema20[-1] - ema20[-5])  / (ema20[-5]  + 1e-9) * 100
    global_bull = ema50_slope > 0.5
    global_bear = ema50_slope < -0.5
    local_bull  = ema20_slope > 0.3
    local_bear  = ema20_slope < -0.3

    # ── 趨勢判斷 ────────────────────────────────────────────────────────────
    if hh and hl:
        if global_bull:
            trend = "多頭趨勢"
            sub   = "Higher High + Higher Low，主趨勢多頭延續"
        else:
            trend = "局部多頭反彈"
            sub   = "Higher High + Higher Low，但大趨勢仍偏空，注意阻力"
        swing_desc = "HH ▲ + HL ▲"
        strength_base = 80 if global_bull else 60

    elif lh and ll:
        trend = "空頭趨勢"
        sub   = "Lower High + Lower Low，空頭結構完整"
        swing_desc = "LH ▼ + LL ▼"
        strength_base = 20

    elif lh and hl:
        trend = "橫盤收斂"
        sub   = "Lower High + Higher Low，三角收斂蓄勢，突破前方向不明"
        swing_desc = "LH ▼ + HL ▲（收斂）"
        strength_base = 50

    elif hh and ll:
        trend = "趨勢發散"
        sub   = "Higher High + Lower Low，多空均有力，震盪擴大"
        swing_desc = "HH ▲ + LL ▼（發散）"
        strength_base = 45

    else:
        trend = "橫盤整理"
        sub   = "無明確擺動結構，區間震盪"
        swing_desc = "無明確 HH/HL/LH/LL"
        strength_base = 45

    # ── 趨勢反轉偵測（核心邏輯）────────────────────────────────────────────
    reversal_signal = ""
    # 大趨勢空頭但局部多頭結構成立
    if global_bear and hh and hl:
        reversal_signal = "⚠️ 大趨勢空頭中出現局部多頭結構，疑似底部反轉初期"
    # 大趨勢多頭但局部空頭結構成立
    elif global_bull and lh and ll:
        reversal_signal = "⚠️ 大趨勢多頭中出現局部空頭結構，疑似頂部反轉初期"

    # ── 趨勢強度 ─────────────────────────────────────────────────────────────
    strength = strength_base
    above_ema20 = current > ema20[-1]
    above_ema50 = current > ema50[-1]
    ema_aligned = ema20[-1] > ema50[-1]

    if "多頭" in trend:
        if above_ema20:  strength = min(strength + 8, 100)
        if above_ema50:  strength = min(strength + 7, 100)
        if ema_aligned:  strength = min(strength + 5, 100)
    elif "空頭" in trend:
        if not above_ema20: strength = max(strength - 8, 0)
        if not above_ema50: strength = max(strength - 7, 0)
        if not ema_aligned: strength = max(strength - 5, 0)

    # ── 結構突破 ──────────────────────────────────────────────────────────────
    recent_high = max(highs[-20:])
    recent_low  = min(lows[-20:])
    if current > recent_high * 0.999:
        struct_break = "突破阻力 ↑"
    elif current < recent_low * 1.001:
        struct_break = "跌破支撐 ↓"
    else:
        struct_break = "區間內整理"

    # ── 市場狀態 ──────────────────────────────────────────────────────────────
    atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
    vol_std = float(df['Close'].rolling(20).std().iloc[-1])
    if atr > vol_std * 1.6:
        market_state = "高波動擴張"
    elif atr < vol_std * 0.6:
        market_state = "低波動蓄勢"
    else:
        market_state = "正常波動"

    return {
        "trend":           trend,
        "sub_trend":       sub,
        "swing_desc":      swing_desc,
        "trend_strength":  int(strength),
        "market_state":    market_state,
        "structure_break": struct_break,
        "reversal_signal": reversal_signal,
        "swing_highs":     sh,
        "swing_lows":      sl,
        "ema20":           ema20,
        "ema50":           ema50,
        "global_bull":     global_bull,
        "global_bear":     global_bear,
        "local_bull":      local_bull,
        "hh": hh, "hl": hl, "lh": lh, "ll": ll,
        "above_ema20":     above_ema20,
        "above_ema50":     above_ema50,
        "ema_aligned":     ema_aligned,
        "ema20_slope":     ema20_slope,
        "ema50_slope":     ema50_slope,
        "recent_high":     recent_high,
        "recent_low":      recent_low,
    }


def _default_struct(ema20, ema50, current, highs, lows, n):
    return {
        "trend": "橫盤整理", "sub_trend": "數據不足",
        "swing_desc": "N/A", "trend_strength": 45,
        "market_state": "觀望", "structure_break": "無",
        "reversal_signal": "", "swing_highs": [], "swing_lows": [],
        "ema20": ema20, "ema50": ema50,
        "global_bull": False, "global_bear": False, "local_bull": False,
        "hh": False, "hl": False, "lh": False, "ll": False,
        "above_ema20": current > ema20[-1], "above_ema50": current > ema50[-1],
        "ema_aligned": ema20[-1] > ema50[-1],
        "ema20_slope": 0.0, "ema50_slope": 0.0,
        "recent_high": max(highs[-20:]) if n >= 20 else highs[-1],
        "recent_low":  min(lows[-20:])  if n >= 20 else lows[-1],
    }
