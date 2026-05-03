"""
AI 綜合分析文字生成
完全對齊專業交易員報告格式：
單K型態 / 雙K型態 / 三K以上 / 型態學 / SMC / 成交量 / 綜合結論
"""


def generate_ai_analysis(ticker, df, patterns, market_struct, volume_analysis,
                          sr_levels, smart_money, signals, scores) -> str:

    current    = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    trend      = market_struct.get('trend', '橫盤')
    sub_trend  = market_struct.get('sub_trend', '')
    swing_desc = market_struct.get('swing_desc', '')
    trend_str  = market_struct.get('trend_strength', 50)
    struct_break = market_struct.get('structure_break', '')
    reversal   = market_struct.get('reversal_signal', '')
    global_bear = market_struct.get('global_bear', False)
    global_bull = market_struct.get('global_bull', False)

    vol_sig    = volume_analysis.get('vol_signal', '')
    vol_ratio  = volume_analysis.get('vol_ratio', 1.0)
    interp     = volume_analysis.get('interpretation', '')
    smart_vol  = volume_analysis.get('smart_vol', '')

    behavior   = smart_money.get('behavior', '')
    accum      = smart_money.get('accumulation_prob', 0)
    dist       = smart_money.get('distribution_risk', 0)
    lg         = smart_money.get('liquidity_grab', '無')
    stop_hunt  = smart_money.get('stop_hunt', '否')
    sm_desc    = smart_money.get('description', '')
    lg_desc    = smart_money.get('lg_desc', '')
    sh_desc    = smart_money.get('stop_hunt_desc', '')

    sig        = signals.get('primary', 'NEUTRAL')
    strength   = signals.get('strength', '')
    buy_r      = signals.get('buy_reasons', [])
    sell_r     = signals.get('sell_reasons', [])
    conditional = signals.get('conditional_bull', False)
    macro_targets = signals.get('macro_targets', [])
    trade      = signals.get('trade_setup', {})

    overall    = scores.get('overall_rating', '中性 ⟷')
    confidence = scores.get('confidence', 0)

    supports    = sr_levels.get('supports', [])
    resistances = sr_levels.get('resistances', [])

    # 直接從分類結構取，不需要再過濾
    single_k_pat = patterns.get('single_k', [])
    double_k_pat = patterns.get('double_k', [])
    triple_k_pat = patterns.get('triple_k', [])
    macro_pat    = patterns.get('macro', [])
    detected     = patterns.get('detected', [])

    sections = []

    # ── Section 1：市場結構 ───────────────────────────────────────────────
    if "多頭趨勢" == trend and not global_bear:
        s1 = (f"{ticker} 目前確立 {swing_desc} 多頭結構，趨勢強度 {trend_str}/100。"
              f"{sub_trend}。EMA20 / EMA50 呈多頭排列，價格運行於均線之上，趨勢動能強勁。")
    elif "局部多頭反彈" == trend:
        s1 = (f"⚠️ {ticker} 大趨勢仍處於空頭格局（EMA50 向下），但局部已出現 {swing_desc} 多頭結構。"
              f"此為空頭趨勢中的底部反彈甚至趨勢反轉初期最典型形態。"
              f"做多比做空勝率更高，但需設置嚴格止損。")
    elif "空頭趨勢" == trend:
        s1 = (f"{ticker} 維持 {swing_desc} 空頭結構，趨勢強度僅 {trend_str}/100。"
              f"{sub_trend}。價格運行於下降 EMA 之下，空方主導市場。")
    elif "橫盤收斂" == trend:
        s1 = (f"{ticker} 進入 {swing_desc} 收斂整理格局，{sub_trend}。"
              f"價格區間收窄，突破方向將決定下一波主浪走向。")
    else:
        s1 = (f"{ticker} 目前 {trend}，{sub_trend}。"
              f"趨勢強度 {trend_str}/100，市場方向性不強。")

    if reversal:
        s1 += f"\n\n{reversal}"
    sections.append(s1)

    # ── Section 2：單K型態（最新第-1根）────────────────────────────────────
    if single_k_pat:
        descs = [f"【{p['name']}】{p.get('desc','')}" for p in single_k_pat]
        sections.append("**〔單K型態〕**（最新1根）\n" + "\n".join(descs))

    # ── Section 3：雙K型態（最新第-2、-1根）─────────────────────────────────
    if double_k_pat:
        descs = [f"【{p['name']}】{p.get('desc','')}" for p in double_k_pat]
        sections.append("**〔雙K型態〕**（最新2根）\n" + "\n".join(descs))

    # ── Section 4：三K以上型態（最新3-5根）──────────────────────────────────
    if triple_k_pat:
        descs = [f"【{p['name']}】{p.get('desc','')}" for p in triple_k_pat]
        sections.append("**〔三K以上型態〕**（最新3-5根）\n" + "\n".join(descs))

    # ── Section 5：型態學（全期數據長期結構）────────────────────────────────
    if macro_pat:
        macro_descs = []
        for p in macro_pat:
            d = p.get('desc', '')
            macro_descs.append(f"【{p['name']}】{d}")
        sections.append("**〔型態學〕**（長期結構）\n" + "\n".join(macro_descs))

    # ── Section 6：成交量分析（集中最新5根）────────────────────────────────
    r5        = volume_analysis.get('recent5_ratio', 1.0)
    vbias     = volume_analysis.get('vol_bias', '')
    vdiv      = volume_analysis.get('vol_divergence', '')

    if vol_ratio >= 2.0:
        vol_txt = (f"最新一根爆量至均量 {vol_ratio:.1f} 倍——{interp}，{smart_vol}。"
                   f"近5根整體量比 {r5:.1f}x，{vbias}，主力資金大量介入。")
    elif vol_ratio >= 1.3:
        vol_txt = (f"最新一根成交量放大（{vol_ratio:.1f}x均量），{vol_sig}。"
                   f"近5根量比 {r5:.1f}x，{vbias}，量價配合良好，訊號可信度高。")
    elif vol_ratio < 0.7:
        vol_txt = (f"最新一根縮量（{vol_ratio:.1f}x均量），{interp}。"
                   f"近5根量比 {r5:.1f}x，{vbias}，主力未大量離場。")
    else:
        vol_txt = (f"最新一根成交量正常（{vol_ratio:.1f}x均量），{interp}。"
                   f"近5根量比 {r5:.1f}x，{vbias}。")

    if vdiv:
        vol_txt += f" {vdiv}"

    sections.append(f"**〔成交量分析（最新5根）〕**\n{vol_txt}")

    # ── Section 7：SMC 主力行為 ──────────────────────────────────────────
    if sm_desc:
        sections.append(f"**〔Smart Money 主力行為〕**\n{sm_desc}")

    # ── Section 8：支撐阻力 ──────────────────────────────────────────────
    if supports and resistances:
        sup_str = " / ".join([f"${s:.2f}" for s in supports[:3]])
        res_str = " / ".join([f"${r:.2f}" for r in resistances[:3]])
        sr_txt = (f"關鍵支撐：{sup_str}，關鍵阻力：{res_str}。"
                  f"當前價格 ${current:.2f} 位於支撐上方 "
                  f"{(current-supports[0])/supports[0]*100:.1f}%，"
                  f"距阻力 {(resistances[0]-current)/current*100:.1f}%。")
        if struct_break == "突破阻力 ↑":
            sr_txt += " 價格已突破近期阻力，強勢訊號。"
        elif struct_break == "跌破支撐 ↓":
            sr_txt += " ⚠️ 價格已跌破近期支撐，警示。"
        sections.append(f"**〔支撐與阻力〕**\n{sr_txt}")

    # ── Section 9：型態目標位 ───────────────────────────────────────────
    if macro_targets:
        tgt_lines = []
        for mt in macro_targets:
            tgt_lines.append(
                f"{mt['pattern'].split()[0]} 頸線 ${mt['neckline']:.2f}，"
                f"測量目標 ${mt['target']:.2f}"
                f"（潛在空間 {abs(mt['target']-current)/current*100:.1f}%）"
            )
        sections.append("**〔型態目標位〕**\n" + "\n".join(tgt_lines))

    # ── Section 10：綜合結論 ─────────────────────────────────────────────
    reasons = buy_r if sig == "BUY" else sell_r
    reason_txt = " + ".join(reasons[:5]) if reasons else "多空平衡"

    if "強烈看多" in overall:
        conclusion = (f"綜合評估：{ticker} 多頭訊號強烈，{reason_txt} 三重共振，"
                      f"評級【{overall}】，信心 {confidence}%。積極做多，嚴守止損 ${trade.get('stop_loss',0):.2f}。")
    elif "偏多" in overall and conditional:
        conclusion = (f"綜合評估：{ticker} 雖大趨勢偏空，但局部多頭訊號明確——"
                      f"{reason_txt}。評級【{overall}】，信心 {confidence}%。"
                      f"可輕倉做多，止損嚴格設於 ${trade.get('stop_loss',0):.2f}，"
                      f"若不能守住支撐立即出場。")
    elif "偏多" in overall:
        conclusion = (f"綜合評估：{ticker} 偏向多方，{reason_txt}，"
                      f"評級【{overall}】，信心 {confidence}%。"
                      f"可輕倉試多，止損 ${trade.get('stop_loss',0):.2f}，風報比 {trade.get('rrr','N/A')}。")
    elif "強烈看空" in overall:
        conclusion = (f"綜合評估：{ticker} 空頭訊號強烈，{reason_txt}，"
                      f"評級【{overall}】，信心 {confidence}%。不宜追多，空頭機會為主。")
    elif "偏空" in overall:
        conclusion = (f"綜合評估：{ticker} 偏向空方，{reason_txt}，"
                      f"評級【{overall}】，信心 {confidence}%。持股謹慎，考慮減倉。")
    else:
        conclusion = (f"綜合評估：{ticker} 多空暫時平衡（買方 {signals.get('buy_score',0)} 分 vs 賣方 {signals.get('sell_score',0)} 分），"
                      f"評級【{overall}】。觀望等待明確突破後再行動。"
                      f"上行突破 ${resistances[0]:.2f} 看多，下行跌破 ${supports[0]:.2f} 看空。"
                      if supports and resistances else
                      f"評級【{overall}】，等待方向確認。")

    sections.append(f"**〔綜合結論〕**\n{conclusion}")

    return "\n\n".join(sections)
