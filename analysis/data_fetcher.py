"""Data fetching with yfinance + fallback"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


INTERVAL_PERIOD_MAP = {
    "1m":  "5d",
    "5m":  "60d",
    "15m": "60d",
    "30m": "60d",
    "1h":  "730d",
    "1d":  "5y",
    "1wk": "10y",
}


def fetch_ohlcv(ticker: str, interval: str, bar_count: int = 120) -> pd.DataFrame | None:
    period = INTERVAL_PERIOD_MAP.get(interval, "1y")
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, interval=interval, auto_adjust=True)
        if df is None or len(df) < 10:
            return None
        df = df.dropna()
        df = df.tail(bar_count)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        return None
