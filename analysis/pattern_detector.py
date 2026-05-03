"""Comprehensive candlestick pattern detection - pure Price Action"""
import pandas as pd
import numpy as np


def _body(row): return abs(row['Close'] - row['Open'])
def _upper_shadow(row): return row['High'] - max(row['Open'], row['Close'])
def _lower_shadow(row): return min(row['Open'], row['Close']) - row['Low']
def _total_range(row): return row['High'] - row['Low']
def _is_bull(row): return row['Close'] > row['Open']
def _is_bear(row): return row['Close'] < row['Open']


def detect_all_patterns(df: pd.DataFrame) -> dict:
    detected = []
    n = len(df)

    for i in range(2, n):
        c = df.iloc[i]
        p = df.iloc[i - 1]
        pp = df.iloc[i - 2]

        body_c = _body(c)
        upper_c = _upper_shadow(c)
        lower_c = _lower_shadow(c)
        rng_c = _total_range(c)

        body_p = _body(p)
        rng_p = _total_range(p)

        # ── SINGLE CANDLE ────────────────────────────────────────────────────
        # Hammer
        if (lower_c > 2 * body_c and upper_c < 0.3 * body_c and rng_c > 0 and body_c > 0):
            if c['Close'] < df['Close'].iloc[max(0, i-10):i].mean():
                detected.append({"index": i, "name": "錘頭線 🔨", "bias": "bull", "bar": i})

        # Shooting Star
        if (upper_c > 2 * body_c and lower_c < 0.3 * body_c and rng_c > 0 and body_c > 0):
            if c['Close'] > df['Close'].iloc[max(0, i-10):i].mean():
                detected.append({"index": i, "name": "流星線 ⭐", "bias": "bear", "bar": i})

        # Doji
        if rng_c > 0 and body_c / rng_c < 0.1:
            detected.append({"index": i, "name": "十字線 ✚", "bias": "neutral", "bar": i})

        # Gravestone Doji
        if body_c < 0.05 * rng_c and lower_c < 0.1 * rng_c and upper_c > 0.8 * rng_c:
            detected.append({"index": i, "name": "墓碑線 🪦", "bias": "bear", "bar": i})

        # Dragonfly Doji
        if body_c < 0.05 * rng_c and upper_c < 0.1 * rng_c and lower_c > 0.8 * rng_c:
            detected.append({"index": i, "name": "蜻蜓線 🌿", "bias": "bull", "bar": i})

        # Long upper shadow
        if upper_c > 2 * body_c and body_c > 0:
            detected.append({"index": i, "name": "長上影線", "bias": "bear", "bar": i})

        # Long lower shadow
        if lower_c > 2 * body_c and body_c > 0:
            detected.append({"index": i, "name": "長下影線", "bias": "bull", "bar": i})

        # Full bull candle (Marubozu)
        if _is_bull(c) and upper_c < 0.02 * rng_c and lower_c < 0.02 * rng_c:
            detected.append({"index": i, "name": "光頭光腳陽線 ▮", "bias": "bull", "bar": i})

        # Full bear candle
        if _is_bear(c) and upper_c < 0.02 * rng_c and lower_c < 0.02 * rng_c:
            detected.append({"index": i, "name": "光頭光腳陰線 ▮", "bias": "bear", "bar": i})

        # ── DOUBLE CANDLE ────────────────────────────────────────────────────
        # Bullish Engulfing
        if (_is_bear(p) and _is_bull(c) and
                c['Open'] < p['Close'] and c['Close'] > p['Open'] and body_c > body_p):
            detected.append({"index": i, "name": "多頭吞噬 🟢", "bias": "bull", "bar": i})

        # Bearish Engulfing
        if (_is_bull(p) and _is_bear(c) and
                c['Open'] > p['Close'] and c['Close'] < p['Open'] and body_c > body_p):
            detected.append({"index": i, "name": "空頭吞噬 🔴", "bias": "bear", "bar": i})

        # Harami Bull
        if (_is_bear(p) and _is_bull(c) and
                c['Open'] > p['Close'] and c['Close'] < p['Open'] and body_c < body_p):
            detected.append({"index": i, "name": "多頭孕線", "bias": "bull", "bar": i})

        # Harami Bear
        if (_is_bull(p) and _is_bear(c) and
                c['Open'] < p['Close'] and c['Close'] > p['Open'] and body_c < body_p):
            detected.append({"index": i, "name": "空頭孕線", "bias": "bear", "bar": i})

        # Dark Cloud Cover
        if (_is_bull(p) and _is_bear(c) and
                c['Open'] > p['High'] and c['Close'] < (p['Open'] + p['Close']) / 2):
            detected.append({"index": i, "name": "烏雲蓋頂 ☁️", "bias": "bear", "bar": i})

        # Piercing Line
        if (_is_bear(p) and _is_bull(c) and
                c['Open'] < p['Low'] and c['Close'] > (p['Open'] + p['Close']) / 2):
            detected.append({"index": i, "name": "穿刺線 💉", "bias": "bull", "bar": i})

        # ── TRIPLE CANDLE ────────────────────────────────────────────────────
        # Morning Star
        if (_is_bear(pp) and _body(pp) > 0.5 * _total_range(pp) and
                _body(p) < 0.3 * _body(pp) and _is_bull(c) and
                c['Close'] > (pp['Open'] + pp['Close']) / 2):
            detected.append({"index": i, "name": "啟明星 🌟", "bias": "bull", "bar": i})

        # Evening Star
        if (_is_bull(pp) and _body(pp) > 0.5 * _total_range(pp) and
                _body(p) < 0.3 * _body(pp) and _is_bear(c) and
                c['Close'] < (pp['Open'] + pp['Close']) / 2):
            detected.append({"index": i, "name": "黃昏星 🌙", "bias": "bear", "bar": i})

        # Three White Soldiers
        if i >= 3:
            t1, t2, t3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
            if (all(_is_bull(x) for x in [t1, t2, t3]) and
                    t2['Close'] > t1['Close'] and t3['Close'] > t2['Close'] and
                    t2['Open'] > t1['Open'] and t3['Open'] > t2['Open']):
                detected.append({"index": i, "name": "紅三兵 🪖", "bias": "bull", "bar": i})

        # Three Black Crows
        if i >= 3:
            t1, t2, t3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
            if (all(_is_bear(x) for x in [t1, t2, t3]) and
                    t2['Close'] < t1['Close'] and t3['Close'] < t2['Close'] and
                    t2['Open'] < t1['Open'] and t3['Open'] < t2['Open']):
                detected.append({"index": i, "name": "三隻烏鴉 🐦‍⬛", "bias": "bear", "bar": i})

    # ── MACRO PATTERNS ───────────────────────────────────────────────────────────
    macro = _detect_macro_patterns(df)
    detected.extend(macro)

    # Deduplicate by bar + name
    seen = set()
    unique = []
    for p in detected:
        key = (p['bar'], p['name'])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return {
        "detected": unique[-15:],  # last 15
        "bull_count": sum(1 for p in unique if p['bias'] == 'bull'),
        "bear_count": sum(1 for p in unique if p['bias'] == 'bear'),
    }


def _detect_macro_patterns(df: pd.DataFrame) -> list:
    patterns = []
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    n = len(df)

    # W Bottom
    if n >= 20:
        seg = closes[-20:]
        mid = len(seg) // 2
        left_min = np.min(seg[:mid])
        right_min = np.min(seg[mid:])
        mid_max = np.max(seg[mid-5:mid+5])
        if (abs(left_min - right_min) / left_min < 0.03 and
                mid_max > left_min * 1.02):
            patterns.append({"index": n-1, "name": "W底型態 📐", "bias": "bull", "bar": n-1})

    # M Top
    if n >= 20:
        seg = closes[-20:]
        mid = len(seg) // 2
        left_max = np.max(seg[:mid])
        right_max = np.max(seg[mid:])
        mid_min = np.min(seg[mid-5:mid+5])
        if (abs(left_max - right_max) / left_max < 0.03 and
                mid_min < left_max * 0.98):
            patterns.append({"index": n-1, "name": "M頂型態 📐", "bias": "bear", "bar": n-1})

    # Triangle
    if n >= 15:
        seg_h = highs[-15:]
        seg_l = lows[-15:]
        h_range = np.max(seg_h) - np.min(seg_h)
        l_range = np.max(seg_l) - np.min(seg_l)
        recent_h_range = np.max(seg_h[-5:]) - np.min(seg_h[-5:])
        if recent_h_range < h_range * 0.5 and recent_h_range < l_range * 0.5:
            patterns.append({"index": n-1, "name": "三角收斂 △", "bias": "neutral", "bar": n-1})

    return patterns
