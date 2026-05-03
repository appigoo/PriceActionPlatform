"""AI Analysis Text Generation - Professional Trading Analysis"""


def generate_ai_analysis(ticker, df, patterns, market_struct, volume_analysis, sr_levels, smart_money, signals, scores) -> str:
    current = df['Close'].iloc[-1]
    trend = market_struct.get('trend', '橫盤')
    sub_trend = market_struct.get('sub_trend', '')
    trend_str = market_struct.get('trend_strength', 50)
    struct_break = market_struct.get('structure_break', '')
    vol_sig = volume_analysis.get('vol_signal', '')
    vol_ratio = volume_analysis.get('vol_ratio', 1.0)
    interpretation = volume_analysis.get('interpretation', '')
    behavior = smart_money.get('behavior', '')
    sm_desc = smart_money.get('description', '')
    primary_signal = signals.get('primary', 'NEUTRAL')
    overall_rating = scores.get('overall_rating', '中性')
    detected_patterns = patterns.get('detected', [])
    supports = sr_levels.get('supports', [])
    resistances = sr_levels.get('resistances', [])

    # Build analysis
    parts = []

    # 1. Trend
    if "多頭" in trend:
        parts.append(f"{ticker} 目前維持 {market_struct.get('swing_desc','HH+HL')} 結構，整體屬於強勢多頭趨勢，趨勢強度達 {trend_str} 分。")
    elif "空頭" in trend:
        parts.append(f"{ticker} 目前確立 {market_struct.get('swing_desc','LH+LL')} 結構，整體處於空頭格局，趨勢強度僅 {trend_str} 分，賣壓主導市場。")
    elif "反轉" in trend:
        parts.append(f"{ticker} 趨勢結構出現反轉訊號，{sub_trend}，多空力量正在重新博弈。")
    elif "收斂" in trend:
        parts.append(f"{ticker} 市場進入三角收斂格局，{sub_trend}，突破方向將決定下一波主升或主跌浪。")
    else:
        parts.append(f"{ticker} 目前處於橫盤整理區間，${supports[0]:.2f} 至 ${resistances[0]:.2f} 之間形成明確箱體。" if supports and resistances else f"{ticker} 目前橫盤震盪，方向不明。")

    # 2. Pattern
    bull_patterns = [p['name'] for p in detected_patterns if p['bias'] == 'bull']
    bear_patterns = [p['name'] for p in detected_patterns if p['bias'] == 'bear']
    if bull_patterns:
        parts.append(f"近期出現 {', '.join(bull_patterns[:3])} 等多頭型態，顯示低位買盤承接積極。")
    if bear_patterns:
        parts.append(f"近期出現 {', '.join(bear_patterns[:3])} 等空頭型態，上方拋壓明顯。")

    # 3. Volume
    if vol_ratio >= 2.0:
        parts.append(f"成交量爆量至均量 {vol_ratio:.1f} 倍，{interpretation}，{volume_analysis.get('smart_vol','')}。")
    elif vol_ratio >= 1.3:
        parts.append(f"成交量放大至均量 {vol_ratio:.1f} 倍，{vol_sig}，動能配合良好。")
    else:
        parts.append(f"成交量維持縮量（{vol_ratio:.1f}x均量），{interpretation}。")

    # 4. Support/Resistance
    if supports and resistances:
        parts.append(f"關鍵支撐位於 ${supports[0]:.2f}，阻力位於 ${resistances[0]:.2f}，當前價格 ${current:.2f}。")

    # 5. Smart Money
    if behavior != "正常波動":
        parts.append(sm_desc)

    # 6. Structure Break
    if "突破阻力" in struct_break:
        parts.append(f"價格突破阻力，若後續放量維持，確認進入主升段，強勢多頭信號成立。")
    elif "跌破支撐" in struct_break:
        parts.append(f"價格跌破支撐，若不能快速收回，下方空間將進一步打開，空頭格局加劇。")

    # 7. Conclusion
    if "強烈看多" in overall_rating:
        conclusion = f"綜合評估：{ticker} 多頭信號強烈，Price Action + 成交量 + 市場結構三重共振，評級「{overall_rating}」，積極做多。"
    elif "偏多" in overall_rating:
        conclusion = f"綜合評估：{ticker} 偏向多方，評級「{overall_rating}」，可輕倉試多，注意設置止損。"
    elif "強烈看空" in overall_rating:
        conclusion = f"綜合評估：{ticker} 空頭訊號顯著，評級「{overall_rating}」，不宜追多，關注做空機會。"
    elif "偏空" in overall_rating:
        conclusion = f"綜合評估：{ticker} 偏向空方，評級「{overall_rating}」，持股謹慎，可考慮減倉。"
    else:
        conclusion = f"綜合評估：{ticker} 多空暫時平衡，評級「{overall_rating}」，觀望等待明確突破方向後再行動。"
    
    parts.append(conclusion)

    return "\n\n".join(parts)
