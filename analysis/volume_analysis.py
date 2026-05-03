"""Volume Analysis - Core of Smart Money Detection"""
import pandas as pd
import numpy as np


def analyze_volume(df: pd.DataFrame) -> dict:
    vol = df['Volume'].values
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values
    open_ = df['Open'].values
    n = len(df)

    avg20 = np.mean(vol[-20:]) if n >= 20 else np.mean(vol)
    avg5 = np.mean(vol[-5:]) if n >= 5 else np.mean(vol)
    last_vol = vol[-1]
    vol_ratio = last_vol / avg20 if avg20 > 0 else 1.0

    # Volume trend
    vol_increasing = np.polyfit(range(min(10, n)), vol[-min(10,n):], 1)[0] > 0

    # Price-volume divergence
    price_up = close[-1] > close[-5] if n >= 5 else False
    vol_up_with_price = price_up and vol_ratio > 1.2
    vol_down_with_price_up = price_up and vol_ratio < 0.8  # divergence

    # Signal classification
    if vol_ratio >= 2.5:
        if close[-1] > open_[-1]:  # bull candle
            if close[-1] > np.mean(close[-20:]):
                vol_signal = "高位爆量陽線 ⚠️"
                interpretation = "高位爆量，需警惕主力派發"
                smart_vol = "疑似主力出貨"
            else:
                vol_signal = "低位爆量陽線 💪"
                interpretation = "低位爆量，主力可能吸籌進場"
                smart_vol = "疑似主力進場"
        else:
            if close[-1] < np.mean(close[-20:]):
                vol_signal = "低位爆量陰線 🔍"
                interpretation = "低位恐慌殺跌，可能為洗盤"
                smart_vol = "恐慌盤殺出 / 主力洗盤"
            else:
                vol_signal = "高位爆量陰線 🚨"
                interpretation = "高位大量下跌，空頭佔優"
                smart_vol = "主力出貨訊號"
    elif vol_ratio >= 1.5:
        if close[-1] > open_[-1]:
            vol_signal = "放量突破"
            interpretation = "成交量配合上漲，買盤積極"
            smart_vol = "多頭動能增強"
        else:
            vol_signal = "放量下跌"
            interpretation = "成交量配合下跌，賣壓沉重"
            smart_vol = "空頭動能增強"
    elif vol_ratio < 0.5:
        vol_signal = "極度縮量"
        interpretation = "市場觀望，方向選擇前蓄勢"
        smart_vol = "等待突破方向"
    elif vol_ratio < 0.8:
        if price_up:
            vol_signal = "縮量回調"
            interpretation = "縮量回調為健康修正"
            smart_vol = "主力未出貨"
        else:
            vol_signal = "縮量整理"
            interpretation = "縮量整理，主力壓貨"
            smart_vol = "籌碼鎖定中"
    else:
        vol_signal = "正常成交量"
        interpretation = "正常市場活動"
        smart_vol = "無明顯異常"

    # Upper shadow volume analysis
    last_upper_shadow = high[-1] - max(close[-1], open_[-1])
    last_body = abs(close[-1] - open_[-1])
    last_range = high[-1] - low[-1]
    upper_shadow_ratio = last_upper_shadow / last_range if last_range > 0 else 0

    if vol_ratio > 2.0 and upper_shadow_ratio > 0.5:
        extra = "爆量長上影：主力誘多後打壓，高風險！"
    elif vol_ratio > 2.0 and (low[-1] - min(close[-1], open_[-1])) / last_range > 0.5 if last_range > 0 else False:
        extra = "爆量長下影：主力掃盤吸籌，注意反彈"
    else:
        extra = ""

    return {
        "vol_ratio": vol_ratio,
        "vol_signal": vol_signal,
        "interpretation": interpretation,
        "smart_vol": smart_vol,
        "vol_increasing": vol_increasing,
        "vol_divergence": vol_down_with_price_up,
        "extra_signal": extra,
        "avg20": avg20,
        "volumes": vol.tolist(),
    }
