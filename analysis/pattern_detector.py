"""
K線型態辨識 - 完整版
單K / 雙K / 三K以上 / 型態學（W底、頭肩底、M頂、頭肩頂、三角收斂）
"""
import numpy as np
import pandas as pd


# ── 基礎工具 ──────────────────────────────────────────────────────────────────
def _body(r):       return abs(r['Close'] - r['Open'])
def _upper(r):      return r['High'] - max(r['Open'], r['Close'])
def _lower(r):      return min(r['Open'], r['Close']) - r['Low']
def _rng(r):        return r['High'] - r['Low']
def _is_bull(r):    return r['Close'] > r['Open']
def _is_bear(r):    return r['Close'] < r['Open']
def _mid(r):        return (r['Open'] + r['Close']) / 2


def detect_all_patterns(df: pd.DataFrame) -> dict:
    detected = []
    n = len(df)

    # ── 1. 單K型態 ─────────────────────────────────────────────────────────
    for i in range(1, n):
        c   = df.iloc[i]
        body = _body(c)
        up   = _upper(c)
        lo   = _lower(c)
        rng  = _rng(c)
        if rng == 0:
            continue
        body_r = body / rng
        up_r   = up / rng
        lo_r   = lo / rng

        price_rank = (c['Close'] - df['Close'].iloc[max(0,i-20):i].min()) / \
                     (df['Close'].iloc[max(0,i-20):i].max() - df['Close'].iloc[max(0,i-20):i].min() + 1e-9)

        # 錘頭線：低位，長下影 > 2×實體，上影 < 0.3×實體
        if lo_r > 0.55 and up_r < 0.15 and body_r > 0.05 and price_rank < 0.35:
            detected.append({"index": i, "name": "錘頭線 🔨", "bias": "bull", "bar": i,
                             "desc": f"低位錘頭，下影長 {lo/rng*100:.0f}%，強力承接訊號"})

        # 上吊線：高位，長下影（高位出現等同看跌）
        if lo_r > 0.55 and up_r < 0.15 and body_r > 0.05 and price_rank > 0.65:
            detected.append({"index": i, "name": "上吊線 🪢", "bias": "bear", "bar": i,
                             "desc": "高位上吊線，下影雖長但高位出現為看跌警告"})

        # 流星線：高位，長上影 > 2×實體，下影 < 0.3×實體
        if up_r > 0.55 and lo_r < 0.15 and body_r > 0.05 and price_rank > 0.60:
            detected.append({"index": i, "name": "流星線 ⭐", "bias": "bear", "bar": i,
                             "desc": "高位流星，上影遭強力壓制，主力誘多後打壓"})

        # 十字線
        if body_r < 0.08:
            detected.append({"index": i, "name": "十字線 ✚", "bias": "neutral", "bar": i,
                             "desc": "多空膠著，動能轉換訊號，需觀察下一根確認方向"})

        # 墓碑線：實體極小，上影極長，下影極短
        if body_r < 0.06 and up_r > 0.80 and lo_r < 0.08:
            detected.append({"index": i, "name": "墓碑線 🪦", "bias": "bear", "bar": i,
                             "desc": "墓碑線：多方拉升後遭空方全面壓制，看跌信號強烈"})

        # 蜻蜓線：實體極小，下影極長，上影極短
        if body_r < 0.06 and lo_r > 0.80 and up_r < 0.08:
            detected.append({"index": i, "name": "蜻蜓線 🌿", "bias": "bull", "bar": i,
                             "desc": "蜻蜓線：空方打壓後被多方強力承接，看漲信號強烈"})

        # 長上影線
        if up_r > 0.45 and body_r > 0.10:
            detected.append({"index": i, "name": "長上影線 ↑", "bias": "bear", "bar": i,
                             "desc": f"長上影（{up/rng*100:.0f}%），上方拋壓明顯"})

        # 長下影線
        if lo_r > 0.45 and body_r > 0.10:
            detected.append({"index": i, "name": "長下影線 ↓", "bias": "bull", "bar": i,
                             "desc": f"長下影（{lo/rng*100:.0f}%），下方強力承接"})

        # 光頭光腳陽線
        if _is_bull(c) and up_r < 0.03 and lo_r < 0.03 and body_r > 0.90:
            detected.append({"index": i, "name": "光頭光腳陽線 ▮", "bias": "bull", "bar": i,
                             "desc": "完美陽線，全程多方主導，無任何賣壓，主力主動拉升"})

        # 光頭光腳陰線
        if _is_bear(c) and up_r < 0.03 and lo_r < 0.03 and body_r > 0.90:
            detected.append({"index": i, "name": "光頭光腳陰線 ▮", "bias": "bear", "bar": i,
                             "desc": "完美陰線，全程空方主導，無任何買盤，拋售強烈"})

    # ── 2. 雙K型態 ─────────────────────────────────────────────────────────
    for i in range(2, n):
        c = df.iloc[i]
        p = df.iloc[i - 1]
        bc, bp = _body(c), _body(p)
        rc, rp = _rng(c), _rng(p)
        if rc == 0 or rp == 0 or bp == 0:
            continue

        # 多頭吞噬
        if (_is_bear(p) and _is_bull(c) and
                c['Open'] <= p['Close'] and c['Close'] >= p['Open'] and bc > bp * 0.8):
            strength = "完全吞噬" if bc > bp else "部分吞噬"
            detected.append({"index": i, "name": f"多頭吞噬 🟢 ({strength})", "bias": "bull", "bar": i,
                             "desc": f"多頭吞噬：陽線實體（{bc:.2f}）吞噬前陰線（{bp:.2f}），空方進攻失敗，多方全面接管"})

        # 空頭吞噬
        if (_is_bull(p) and _is_bear(c) and
                c['Open'] >= p['Close'] and c['Close'] <= p['Open'] and bc > bp * 0.8):
            detected.append({"index": i, "name": "空頭吞噬 🔴", "bias": "bear", "bar": i,
                             "desc": f"空頭吞噬：陰線實體（{bc:.2f}）吞噬前陽線（{bp:.2f}），多方進攻失敗，空方全面接管"})

        # 多頭孕線
        if (_is_bear(p) and _is_bull(c) and
                c['Open'] > p['Close'] and c['Close'] < p['Open'] and bc < bp * 0.6):
            detected.append({"index": i, "name": "多頭孕線", "bias": "bull", "bar": i,
                             "desc": "多頭孕線：小陽線孕於大陰線內，空頭動能衰竭，反轉前置訊號"})

        # 空頭孕線
        if (_is_bull(p) and _is_bear(c) and
                c['Open'] < p['Close'] and c['Close'] > p['Open'] and bc < bp * 0.6):
            detected.append({"index": i, "name": "空頭孕線", "bias": "bear", "bar": i,
                             "desc": "空頭孕線：小陰線孕於大陽線內，多頭動能衰竭，回調前置訊號"})

        # 烏雲蓋頂
        if (_is_bull(p) and _is_bear(c) and
                c['Open'] > p['High'] and c['Close'] < _mid(p) and c['Close'] > p['Open']):
            detected.append({"index": i, "name": "烏雲蓋頂 ☁️", "bias": "bear", "bar": i,
                             "desc": "高位烏雲蓋頂：跳空高開後強力回落過中點，主力誘多出貨，看跌強烈"})

        # 穿刺線
        if (_is_bear(p) and _is_bull(c) and
                c['Open'] < p['Low'] and c['Close'] > _mid(p) and c['Close'] < p['Open']):
            detected.append({"index": i, "name": "穿刺線 💉", "bias": "bull", "bar": i,
                             "desc": "穿刺線：低開後強力上攻過中點，空方進攻失敗，多方反撲有力"})

    # ── 3. 三K以上型態 ──────────────────────────────────────────────────────
    for i in range(3, n):
        c  = df.iloc[i]
        p  = df.iloc[i - 1]
        pp = df.iloc[i - 2]

        # 啟明星 Morning Star
        body_pp = _body(pp)
        body_p  = _body(p)
        body_c  = _body(c)
        if (body_pp > 0 and body_c > 0 and
                _is_bear(pp) and body_pp > _rng(pp) * 0.4 and
                body_p < body_pp * 0.35 and
                _is_bull(c) and c['Close'] > _mid(pp)):
            detected.append({"index": i, "name": "啟明星 🌟", "bias": "bull", "bar": i,
                             "desc": "啟明星：大陰線→小實體過渡→大陽線，底部反轉最強訊號，確認低點成立"})

        # 黃昏星 Evening Star
        if (body_pp > 0 and body_c > 0 and
                _is_bull(pp) and body_pp > _rng(pp) * 0.4 and
                body_p < body_pp * 0.35 and
                _is_bear(c) and c['Close'] < _mid(pp)):
            detected.append({"index": i, "name": "黃昏星 🌙", "bias": "bear", "bar": i,
                             "desc": "黃昏星：大陽線→小實體→大陰線，頂部反轉強訊號，主力出貨完成"})

    # 紅三兵（需要連續 3+ 根）
    for i in range(4, n):
        t1, t2, t3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
        if (all(_is_bull(x) for x in [t1, t2, t3]) and
                t2['Close'] > t1['Close'] and t3['Close'] > t2['Close'] and
                t2['Open'] > t1['Open'] and t3['Open'] > t2['Open'] and
                _body(t1) > _rng(t1) * 0.4 and
                _body(t2) > _rng(t2) * 0.4 and
                _body(t3) > _rng(t3) * 0.4):
            detected.append({"index": i, "name": "紅三兵 🪖", "bias": "bull", "bar": i,
                             "desc": "紅三兵：三連陽且依次遞增，主力資金持續進場，強勢多頭延續確認"})

    # 三隻烏鴉
    for i in range(4, n):
        t1, t2, t3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
        if (all(_is_bear(x) for x in [t1, t2, t3]) and
                t2['Close'] < t1['Close'] and t3['Close'] < t2['Close'] and
                t2['Open'] < t1['Open'] and t3['Open'] < t2['Open'] and
                _body(t1) > _rng(t1) * 0.4 and
                _body(t2) > _rng(t2) * 0.4):
            detected.append({"index": i, "name": "三隻烏鴉 🐦‍⬛", "bias": "bear", "bar": i,
                             "desc": "三隻烏鴉：三連陰且依次遞減，空方全面主導，下跌趨勢加速"})

    # 上升三法
    for i in range(6, n):
        big1 = df.iloc[i-4]
        smalls = [df.iloc[i-3], df.iloc[i-2], df.iloc[i-1]]
        big2 = df.iloc[i]
        if (_is_bull(big1) and _body(big1) > _rng(big1) * 0.5 and
                all(_is_bear(s) for s in smalls) and
                all(s['Close'] > big1['Open'] for s in smalls) and
                all(s['High'] < big1['Close'] for s in smalls) and
                _is_bull(big2) and big2['Close'] > big1['Close']):
            detected.append({"index": i, "name": "上升三法 📶", "bias": "bull", "bar": i,
                             "desc": "上升三法：大陽線後三根小陰線整理，再次大陽突破，主升段延續確認"})

    # 下跌三法
    for i in range(6, n):
        big1 = df.iloc[i-4]
        smalls = [df.iloc[i-3], df.iloc[i-2], df.iloc[i-1]]
        big2 = df.iloc[i]
        if (_is_bear(big1) and _body(big1) > _rng(big1) * 0.5 and
                all(_is_bull(s) for s in smalls) and
                all(s['Close'] < big1['Open'] for s in smalls) and
                all(s['Low'] > big1['Close'] for s in smalls) and
                _is_bear(big2) and big2['Close'] < big1['Close']):
            detected.append({"index": i, "name": "下跌三法 📉", "bias": "bear", "bar": i,
                             "desc": "下跌三法：大陰線後三根小陽線反彈，再次大陰突破，主跌段延續確認"})

    # ── 4. 型態學（Macro Patterns）──────────────────────────────────────────
    macro = _detect_macro_patterns(df)
    detected.extend(macro)

    # 去重
    seen, unique = set(), []
    for p in detected:
        key = (p['bar'], p['name'][:6])
        if key not in seen:
            seen.add(key)
            unique.append(p)

    bull_ct = sum(1 for p in unique if p['bias'] == 'bull')
    bear_ct = sum(1 for p in unique if p['bias'] == 'bear')

    return {
        "detected": unique[-20:],
        "bull_count": bull_ct,
        "bear_count": bear_ct,
        "all": unique,
    }


def _detect_macro_patterns(df: pd.DataFrame) -> list:
    """W底、M頂、頭肩底、頭肩頂、三角收斂"""
    patterns = []
    closes = df['Close'].values
    highs  = df['High'].values
    lows   = df['Low'].values
    n = len(df)

    # ── W 底（Double Bottom）────────────────────────────────────────────────
    if n >= 30:
        for window in [30, 40, 50, 60]:
            if n < window:
                continue
            seg_c = closes[-window:]
            seg_l = lows[-window:]
            mid   = window // 2

            left_low_idx  = np.argmin(seg_l[:mid])
            right_low_idx = np.argmin(seg_l[mid:]) + mid
            left_low      = seg_l[left_low_idx]
            right_low     = seg_l[right_low_idx]
            neckline      = np.max(seg_c[left_low_idx:right_low_idx]) if right_low_idx > left_low_idx else seg_c[mid]
            current       = closes[-1]

            # 條件：兩個低點相近（差距<6%），頸線高於兩低點，當前價靠近或突破頸線
            lows_similar  = abs(left_low - right_low) / (left_low + 1e-9) < 0.06
            neck_above    = neckline > left_low * 1.02
            price_near    = current > (left_low + right_low) / 2

            if lows_similar and neck_above and price_near:
                height = neckline - min(left_low, right_low)
                target = neckline + height
                # 判斷是否已突破頸線
                breakout = "已突破頸線 ✅" if current > neckline else f"接近頸線 ${neckline:.2f}"
                patterns.append({
                    "index": n - 1, "bar": n - 1,
                    "name": "W底型態 📐",
                    "bias": "bull",
                    "desc": (f"W底確認：左低 ${left_low:.2f} / 右低 ${right_low:.2f}，"
                             f"頸線 ${neckline:.2f}，{breakout}。"
                             f"型態目標 ${target:.2f}（高度 ${height:.2f} 上投）"),
                    "neckline": neckline,
                    "target": target,
                })
                break  # 只報告一次

    # ── M 頂（Double Top）───────────────────────────────────────────────────
    if n >= 30:
        for window in [30, 40, 50, 60]:
            if n < window:
                continue
            seg_c = closes[-window:]
            seg_h = highs[-window:]
            mid   = window // 2

            left_high_idx  = np.argmax(seg_h[:mid])
            right_high_idx = np.argmax(seg_h[mid:]) + mid
            left_high      = seg_h[left_high_idx]
            right_high     = seg_h[right_high_idx]
            neckline       = np.min(seg_c[left_high_idx:right_high_idx]) if right_high_idx > left_high_idx else seg_c[mid]
            current        = closes[-1]

            highs_similar = abs(left_high - right_high) / (left_high + 1e-9) < 0.06
            neck_below    = neckline < left_high * 0.98
            price_near    = current < (left_high + right_high) / 2

            if highs_similar and neck_below and price_near:
                height = max(left_high, right_high) - neckline
                target = neckline - height
                breakdown = "已跌破頸線 ⚠️" if current < neckline else f"接近頸線 ${neckline:.2f}"
                patterns.append({
                    "index": n - 1, "bar": n - 1,
                    "name": "M頂型態 📐",
                    "bias": "bear",
                    "desc": (f"M頂確認：左高 ${left_high:.2f} / 右高 ${right_high:.2f}，"
                             f"頸線 ${neckline:.2f}，{breakdown}。"
                             f"型態目標 ${target:.2f}"),
                    "neckline": neckline,
                    "target": target,
                })
                break

    # ── 頭肩底（Inverse Head & Shoulders）──────────────────────────────────
    if n >= 40:
        for window in [40, 55, 70]:
            if n < window:
                continue
            seg_l = lows[-window:]
            seg_c = closes[-window:]
            w3 = window // 3

            ls_low = np.min(seg_l[:w3])           # 左肩低點
            hd_low = np.min(seg_l[w3:2*w3])       # 頭部低點（最低）
            rs_low = np.min(seg_l[2*w3:])          # 右肩低點
            neckline = np.mean([
                np.max(seg_c[:w3]),
                np.max(seg_c[w3:2*w3]),
            ])
            current = closes[-1]

            head_lower   = hd_low < ls_low * 0.97 and hd_low < rs_low * 0.97
            shoulders_similar = abs(ls_low - rs_low) / (ls_low + 1e-9) < 0.08
            rs_higher    = rs_low > hd_low  # 右肩高於頭部

            if head_lower and shoulders_similar and rs_higher:
                height = neckline - hd_low
                target = neckline + height
                breakout = "頸線已突破 🚀" if current > neckline else f"等待突破頸線 ${neckline:.2f}"
                patterns.append({
                    "index": n - 1, "bar": n - 1,
                    "name": "頭肩底 🔔",
                    "bias": "bull",
                    "desc": (f"頭肩底確認：左肩 ${ls_low:.2f} / 頭部 ${hd_low:.2f} / 右肩 ${rs_low:.2f}，"
                             f"頸線 ${neckline:.2f}，{breakout}。"
                             f"突破後目標 ${target:.2f}"),
                    "neckline": neckline,
                    "target": target,
                })
                break

    # ── 頭肩頂（Head & Shoulders Top）───────────────────────────────────────
    if n >= 40:
        for window in [40, 55, 70]:
            if n < window:
                continue
            seg_h = highs[-window:]
            seg_c = closes[-window:]
            w3 = window // 3

            ls_high = np.max(seg_h[:w3])
            hd_high = np.max(seg_h[w3:2*w3])
            rs_high = np.max(seg_h[2*w3:])
            neckline = np.mean([
                np.min(seg_c[:w3]),
                np.min(seg_c[w3:2*w3]),
            ])
            current = closes[-1]

            head_higher      = hd_high > ls_high * 1.02 and hd_high > rs_high * 1.02
            shoulders_similar = abs(ls_high - rs_high) / (ls_high + 1e-9) < 0.08
            rs_lower         = rs_high < hd_high

            if head_higher and shoulders_similar and rs_lower:
                height = hd_high - neckline
                target = neckline - height
                breakdown = "頸線已跌破 💀" if current < neckline else f"警戒頸線 ${neckline:.2f}"
                patterns.append({
                    "index": n - 1, "bar": n - 1,
                    "name": "頭肩頂 🔔",
                    "bias": "bear",
                    "desc": (f"頭肩頂確認：左肩 ${ls_high:.2f} / 頭部 ${hd_high:.2f} / 右肩 ${rs_high:.2f}，"
                             f"頸線 ${neckline:.2f}，{breakdown}。"
                             f"目標 ${target:.2f}"),
                    "neckline": neckline,
                    "target": target,
                })
                break

    # ── 三角收斂 ────────────────────────────────────────────────────────────
    if n >= 20:
        seg_h = highs[-20:]
        seg_l = lows[-20:]
        # 線性回歸判斷收斂
        x = np.arange(20)
        slope_h = np.polyfit(x, seg_h, 1)[0]
        slope_l = np.polyfit(x, seg_l, 1)[0]
        converging = slope_h < 0 and slope_l > 0

        # 對稱三角
        if converging and abs(slope_h + slope_l) < abs(slope_h) * 0.4:
            patterns.append({
                "index": n - 1, "bar": n - 1,
                "name": "對稱三角收斂 △",
                "bias": "neutral",
                "desc": "對稱三角收斂：高點依次下降，低點依次上升，蓄勢待發，突破方向決定下一波主浪",
            })
        # 上升三角（阻力水平，支撐上升）
        elif abs(slope_h) < abs(slope_l) * 0.3 and slope_l > 0:
            patterns.append({
                "index": n - 1, "bar": n - 1,
                "name": "上升三角 △↑",
                "bias": "bull",
                "desc": "上升三角：阻力位持平，支撐依次抬高，多方積極，偏向向上突破",
            })
        # 下降三角
        elif abs(slope_l) < abs(slope_h) * 0.3 and slope_h < 0:
            patterns.append({
                "index": n - 1, "bar": n - 1,
                "name": "下降三角 △↓",
                "bias": "bear",
                "desc": "下降三角：支撐位持平，阻力依次下移，空方積極，偏向向下突破",
            })

    return patterns
