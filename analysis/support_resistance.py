"""Support and Resistance Level Detection"""
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema


def find_support_resistance(df: pd.DataFrame, n_levels: int = 5) -> dict:
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    n = len(df)

    # Find local maxima and minima
    order = max(3, n // 20)
    local_max_idx = argrelextrema(highs, np.greater_equal, order=order)[0]
    local_min_idx = argrelextrema(lows, np.less_equal, order=order)[0]

    resistance_prices = highs[local_max_idx].tolist()
    support_prices = lows[local_min_idx].tolist()

    # Cluster nearby levels
    def cluster_levels(prices, tol=0.005):
        if not prices:
            return []
        prices = sorted(prices)
        clusters = []
        cur = [prices[0]]
        for p in prices[1:]:
            if abs(p - cur[-1]) / cur[-1] < tol:
                cur.append(p)
            else:
                clusters.append(np.mean(cur))
                cur = [p]
        clusters.append(np.mean(cur))
        return clusters

    resistances = cluster_levels(resistance_prices)
    supports = cluster_levels(support_prices)

    current = closes[-1]

    # Filter: resistances above current, supports below
    key_res = sorted([r for r in resistances if r > current * 0.98])[:n_levels]
    key_sup = sorted([s for s in supports if s < current * 1.02], reverse=True)[:n_levels]

    # Demand / Supply zones (wider bands)
    demand_zones = [(s * 0.99, s * 1.01) for s in key_sup[:3]]
    supply_zones = [(r * 0.99, r * 1.01) for r in key_res[:3]]

    # Recent high/low
    recent_high = max(highs[-20:])
    recent_low = min(lows[-20:])

    return {
        "resistances": key_res,
        "supports": key_sup,
        "demand_zones": demand_zones,
        "supply_zones": supply_zones,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "current": current,
    }
