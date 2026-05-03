"""
K線型態辨識 - 精確位置版
單K   = 只分析最新第 -1 根
雙K   = 只分析最新第 -2, -1 根
三K以上 = 只分析最新第 -5 ~ -1 根（最多5根）
型態學  = 用全部數據做長期結構判斷（W底/頭肩底等）
"""
import numpy as np
import pandas as pd


# ── 基礎工具 ──────────────────────────────────────────────────────────────────
def _body(r):    return abs(r['Close'] - r['Open'])
def _upper(r):   return r['High'] - max(r['Open'], r['Close'])
def _lower(r):   return min(r['Open'], r['Close']) - r['Low']
def _rng(r):     return r['High'] - r['Low']
def _is_bull(r): return r['Close'] > r['Open']
def _is_bear(r): return r['Close'] < r['Open']
def _mid(r):     return (r['Open'] + r['Close']) / 2


def detect_all_patterns(df: pd.DataFrame) -> dict:
    n = len(df)
    if n < 5:
        return {"detected": [], "single_k": [], "double_k": [],
                "triple_k": [], "macro": [], "bull_count": 0, "bear_count": 0}

    single_k = []
    double_k = []
    triple_k = []
    macro    = []

    # ══════════════════════════════════════════════════════════════════════════
    # 1. 單K型態 ── 只看最新第 -1 根（bar index = n-1）
    # ══════════════════════════════════════════════════════════════════════════
    c   = df.iloc[-1]          # 最新一根
    rng = _rng(c)

    if rng > 0:
        body   = _body(c)
        up     = _upper(c)
        lo     = _lower(c)
        body_r = body / rng
        up_r   = up / rng
        lo_r   = lo / rng

        # 價格在近20日的相對位置（0=最低，1=最高）
        window_c = df['Close'].iloc[max(0, n-21):n-1]
        lo20 = window_c.min()
        hi20 = window_c.max()
        price_rank = (c['Close'] - lo20) / (hi20 - lo20 + 1e-9)

        # 錘頭線
        if lo_r > 0.55 and up_r < 0.15 and body_r > 0.05 and price_rank < 0.40:
            single_k.append({
                "name": "錘頭線 🔨", "bias": "bull", "bar": n-1, "category": "single",
                "desc": f"低位錘頭：下影 {lo/rng*100:.0f}%，強力承接，主力掃盤後護盤"
            })

        # 上吊線
        if lo_r > 0.55 and up_r < 0.15 and body_r > 0.05 and price_rank > 0.65:
            single_k.append({
                "name": "上吊線 🪢", "bias": "bear", "bar": n-1, "category": "single",
                "desc": "高位上吊線：下影雖長但高位出現，警惕主力洗出後反向"
            })

        # 流星線
        if up_r > 0.55 and lo_r < 0.15 and body_r > 0.05 and price_rank > 0.60:
            single_k.append({
                "name": "流星線 ⭐", "bias": "bear", "bar": n-1, "category": "single",
                "desc": f"高位流星：上影 {up/rng*100:.0f}%，主力誘多後強力打壓"
            })

        # 十字線
        if body_r < 0.08:
            single_k.append({
                "name": "十字線 ✚", "bias": "neutral", "bar": n-1, "category": "single",
                "desc": "多空膠著十字線：開收幾乎同價，動能轉換訊號，下一根確認方向"
            })

        # 墓碑線
        if body_r < 0.06 and up_r > 0.80 and lo_r < 0.08:
            single_k.append({
                "name": "墓碑線 🪦", "bias": "bear", "bar": n-1, "category": "single",
                "desc": "墓碑線：多方拉升後被空方全面壓回，看跌信號強烈"
            })

        # 蜻蜓線
        if body_r < 0.06 and lo_r > 0.80 and up_r < 0.08:
            single_k.append({
                "name": "蜻蜓線 🌿", "bias": "bull", "bar": n-1, "category": "single",
                "desc": "蜻蜓線：空方打壓後被多方完全承接，看漲信號強烈"
            })

        # 長上影線（有實體）
        if up_r > 0.45 and body_r > 0.10:
            single_k.append({
                "name": "長上影線 ↑", "bias": "bear", "bar": n-1, "category": "single",
                "desc": f"長上影線：上影佔 {up/rng*100:.0f}%，上方拋壓明顯，高位賣盤沉重"
            })

        # 長下影線（有實體）
        if lo_r > 0.45 and body_r > 0.10:
            single_k.append({
                "name": "長下影線 ↓", "bias": "bull", "bar": n-1, "category": "single",
                "desc": f"長下影線：下影佔 {lo/rng*100:.0f}%，下方強力承接，低位買盤積極"
            })

        # 光頭光腳陽線
        if _is_bull(c) and up_r < 0.03 and lo_r < 0.03 and body_r > 0.88:
            single_k.append({
                "name": "光頭光腳陽線 ▮", "bias": "bull", "bar": n-1, "category": "single",
                "desc": "完美陽線：全程多方主導，無任何賣壓，主力主動拉升"
            })

        # 光頭光腳陰線
        if _is_bear(c) and up_r < 0.03 and lo_r < 0.03 and body_r > 0.88:
            single_k.append({
                "name": "光頭光腳陰線 ▮", "bias": "bear", "bar": n-1, "category": "single",
                "desc": "完美陰線：全程空方主導，無任何買盤，主力主動打壓"
            })

    # ══════════════════════════════════════════════════════════════════════════
    # 2. 雙K型態 ── 只看最新第 -2（prev）和 -1（curr）兩根
    # ══════════════════════════════════════════════════════════════════════════
    if n >= 2:
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        bc, bp = _body(curr), _body(prev)
        rc, rp = _rng(curr), _rng(prev)

        if rc > 0 and rp > 0 and bp > 0:
            # 多頭吞噬
            if (_is_bear(prev) and _is_bull(curr) and
                    curr['Open'] <= prev['Close'] and curr['Close'] >= prev['Open'] and
                    bc >= bp * 0.8):
                tag = "完全吞噬" if bc > bp else "部分吞噬"
                double_k.append({
                    "name": f"多頭吞噬 🟢", "bias": "bull", "bar": n-1, "category": "double",
                    "desc": (f"多頭吞噬（{tag}）：今日陽線（{bc:.2f}）完全覆蓋昨日陰線（{bp:.2f}），"
                             f"空方進攻失敗，多方全面接管")
                })

            # 空頭吞噬
            if (_is_bull(prev) and _is_bear(curr) and
                    curr['Open'] >= prev['Close'] and curr['Close'] <= prev['Open'] and
                    bc >= bp * 0.8):
                double_k.append({
                    "name": "空頭吞噬 🔴", "bias": "bear", "bar": n-1, "category": "double",
                    "desc": (f"空頭吞噬：今日陰線（{bc:.2f}）完全覆蓋昨日陽線（{bp:.2f}），"
                             f"多方進攻失敗，空方全面接管")
                })

            # 多頭孕線
            if (_is_bear(prev) and _is_bull(curr) and
                    curr['Open'] > prev['Close'] and curr['Close'] < prev['Open'] and
                    bc < bp * 0.6):
                double_k.append({
                    "name": "多頭孕線", "bias": "bull", "bar": n-1, "category": "double",
                    "desc": "多頭孕線：小陽線孕於昨日大陰線內，空頭動能耗盡，反轉前置訊號"
                })

            # 空頭孕線
            if (_is_bull(prev) and _is_bear(curr) and
                    curr['Open'] < prev['Close'] and curr['Close'] > prev['Open'] and
                    bc < bp * 0.6):
                double_k.append({
                    "name": "空頭孕線", "bias": "bear", "bar": n-1, "category": "double",
                    "desc": "空頭孕線：小陰線孕於昨日大陽線內，多頭動能衰竭，回調前置訊號"
                })

            # 烏雲蓋頂
            if (_is_bull(prev) and _is_bear(curr) and
                    curr['Open'] > prev['High'] and
                    curr['Close'] < _mid(prev) and curr['Close'] > prev['Open']):
                double_k.append({
                    "name": "烏雲蓋頂 ☁️", "bias": "bear", "bar": n-1, "category": "double",
                    "desc": "烏雲蓋頂：今日跳空高開後強力回落過前日中點，主力高位誘多後出貨"
                })

            # 穿刺線
            if (_is_bear(prev) and _is_bull(curr) and
                    curr['Open'] < prev['Low'] and
                    curr['Close'] > _mid(prev) and curr['Close'] < prev['Open']):
                double_k.append({
                    "name": "穿刺線 💉", "bias": "bull", "bar": n-1, "category": "double",
                    "desc": "穿刺線：今日低開後強力上攻過前日中點，空方進攻失敗，多方反撲有力"
                })

    # ══════════════════════════════════════════════════════════════════════════
    # 3. 三K以上型態 ── 只看最新 5 根（index -5 到 -1）
    # ══════════════════════════════════════════════════════════════════════════
    if n >= 3:
        c0 = df.iloc[-3]   # 三根前
        c1 = df.iloc[-2]   # 兩根前
        c2 = df.iloc[-1]   # 最新

        # 啟明星 Morning Star
        if (_is_bear(c0) and _body(c0) > _rng(c0) * 0.4 and
                _body(c1) < _body(c0) * 0.35 and
                _is_bull(c2) and c2['Close'] > _mid(c0)):
            triple_k.append({
                "name": "啟明星 🌟", "bias": "bull", "bar": n-1, "category": "triple",
                "desc": ("啟明星（最近3根）：大陰線→小實體過渡→大陽線，"
                         f"今日收盤 ${c2['Close']:.2f} 超越三日前陰線中點，底部反轉最強訊號")
            })

        # 黃昏星 Evening Star
        if (_is_bull(c0) and _body(c0) > _rng(c0) * 0.4 and
                _body(c1) < _body(c0) * 0.35 and
                _is_bear(c2) and c2['Close'] < _mid(c0)):
            triple_k.append({
                "name": "黃昏星 🌙", "bias": "bear", "bar": n-1, "category": "triple",
                "desc": ("黃昏星（最近3根）：大陽線→小實體→大陰線，"
                         "頂部反轉強訊號，主力出貨完成")
            })

    # 紅三兵 ── 最近3根全陽，依次遞增
    if n >= 3:
        t1, t2, t3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        if (all(_is_bull(x) for x in [t1, t2, t3]) and
                t2['Close'] > t1['Close'] and t3['Close'] > t2['Close'] and
                t2['Open'] > t1['Open'] and t3['Open'] > t2['Open'] and
                _body(t1) > _rng(t1) * 0.35 and
                _body(t2) > _rng(t2) * 0.35 and
                _body(t3) > _rng(t3) * 0.35):
            triple_k.append({
                "name": "紅三兵 🪖", "bias": "bull", "bar": n-1, "category": "triple",
                "desc": (f"紅三兵（最近3根）：三連陽且依次遞增，"
                         f"${t1['Close']:.2f}→${t2['Close']:.2f}→${t3['Close']:.2f}，"
                         f"主力資金連續進場，強勢多頭延續確認")
            })

    # 三隻烏鴉 ── 最近3根全陰，依次遞減
    if n >= 3:
        t1, t2, t3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
        if (all(_is_bear(x) for x in [t1, t2, t3]) and
                t2['Close'] < t1['Close'] and t3['Close'] < t2['Close'] and
                t2['Open'] < t1['Open'] and t3['Open'] < t2['Open'] and
                _body(t1) > _rng(t1) * 0.35 and
                _body(t2) > _rng(t2) * 0.35):
            triple_k.append({
                "name": "三隻烏鴉 🐦‍⬛", "bias": "bear", "bar": n-1, "category": "triple",
                "desc": (f"三隻烏鴉（最近3根）：三連陰且依次遞減，"
                         f"${t1['Close']:.2f}→${t2['Close']:.2f}→${t3['Close']:.2f}，"
                         f"空方全面主導，下跌趨勢加速")
            })

    # 上升三法 ── 最近5根（大陽→3小陰整理→大陽突破）
    if n >= 5:
        big1   = df.iloc[-5]
        smalls = [df.iloc[-4], df.iloc[-3], df.iloc[-2]]
        big2   = df.iloc[-1]
        if (_is_bull(big1) and _body(big1) > _rng(big1) * 0.5 and
                all(_is_bear(s) for s in smalls) and
                all(s['Close'] > big1['Open'] for s in smalls) and
                all(s['High'] < big1['Close'] for s in smalls) and
                _is_bull(big2) and big2['Close'] > big1['Close']):
            triple_k.append({
                "name": "上升三法 📶", "bias": "bull", "bar": n-1, "category": "triple",
                "desc": ("上升三法（最近5根）：大陽線→三根小陰線整理（均在前陽線實體內）→今日大陽突破，"
                         "主升段延續確認，做多訊號明確")
            })

    # 下跌三法 ── 最近5根
    if n >= 5:
        big1   = df.iloc[-5]
        smalls = [df.iloc[-4], df.iloc[-3], df.iloc[-2]]
        big2   = df.iloc[-1]
        if (_is_bear(big1) and _body(big1) > _rng(big1) * 0.5 and
                all(_is_bull(s) for s in smalls) and
                all(s['Close'] < big1['Open'] for s in smalls) and
                all(s['Low'] > big1['Close'] for s in smalls) and
                _is_bear(big2) and big2['Close'] < big1['Close']):
            triple_k.append({
                "name": "下跌三法 📉", "bias": "bear", "bar": n-1, "category": "triple",
                "desc": ("下跌三法（最近5根）：大陰線→三根小陽線反彈（均在前陰線實體內）→今日大陰突破，"
                         "主跌段延續確認，做空訊號明確")
            })

    # ══════════════════════════════════════════════════════════════════════════
    # 4. 型態學 ── 全期數據做長期結構分析
    # ══════════════════════════════════════════════════════════════════════════
    macro = _detect_macro_patterns(df)

    # ── 彙總所有型態 ─────────────────────────────────────────────────────────
    all_patterns = single_k + double_k + triple_k + macro

    bull_ct = sum(1 for p in all_patterns if p['bias'] == 'bull')
    bear_ct = sum(1 for p in all_patterns if p['bias'] == 'bear')

    return {
        "detected":  all_patterns,       # 全部（給 signals 和圖表用）
        "single_k":  single_k,           # 單K（給 ai_analysis 分段顯示用）
        "double_k":  double_k,           # 雙K
        "triple_k":  triple_k,           # 三K以上
        "macro":     macro,              # 型態學
        "bull_count": bull_ct,
        "bear_count": bear_ct,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 型態學：W底、M頂、頭肩底、頭肩頂、三角收斂（全期數據）
# ══════════════════════════════════════════════════════════════════════════════
def _detect_macro_patterns(df: pd.DataFrame) -> list:
    patterns = []
    closes = df['Close'].values
    highs  = df['High'].values
    lows   = df['Low'].values
    n      = len(df)
    current = closes[-1]

    # ── W 底 ─────────────────────────────────────────────────────────────────
    if n >= 30:
        for window in [30, 45, 60, 80]:
            if n < window:
                continue
            seg_c = closes[-window:]
            seg_l = lows[-window:]
            mid   = window // 2

            l_idx = np.argmin(seg_l[:mid])
            r_idx = np.argmin(seg_l[mid:]) + mid
            l_low, r_low = seg_l[l_idx], seg_l[r_idx]
            neckline = np.max(seg_c[l_idx:r_idx]) if r_idx > l_idx else seg_c[mid]

            if (abs(l_low - r_low) / (l_low + 1e-9) < 0.06 and
                    neckline > min(l_low, r_low) * 1.02):
                height   = neckline - min(l_low, r_low)
                target   = neckline + height
                status   = "已突破頸線 ✅" if current > neckline else f"頸線 ${neckline:.2f} 待突破"
                patterns.append({
                    "name": "W底型態 📐", "bias": "bull", "bar": n-1, "category": "macro",
                    "neckline": neckline, "target": target,
                    "desc": (f"W底：左低 ${l_low:.2f} / 右低 ${r_low:.2f}，{status}，"
                             f"突破後目標 ${target:.2f}（+{height/current*100:.1f}%）")
                })
                break

    # ── M 頂 ─────────────────────────────────────────────────────────────────
    if n >= 30:
        for window in [30, 45, 60, 80]:
            if n < window:
                continue
            seg_c = closes[-window:]
            seg_h = highs[-window:]
            mid   = window // 2

            l_idx = np.argmax(seg_h[:mid])
            r_idx = np.argmax(seg_h[mid:]) + mid
            l_high, r_high = seg_h[l_idx], seg_h[r_idx]
            neckline = np.min(seg_c[l_idx:r_idx]) if r_idx > l_idx else seg_c[mid]

            if (abs(l_high - r_high) / (l_high + 1e-9) < 0.06 and
                    neckline < max(l_high, r_high) * 0.98):
                height = max(l_high, r_high) - neckline
                target = neckline - height
                status = "已跌破頸線 ⚠️" if current < neckline else f"頸線 ${neckline:.2f} 警戒"
                patterns.append({
                    "name": "M頂型態 📐", "bias": "bear", "bar": n-1, "category": "macro",
                    "neckline": neckline, "target": target,
                    "desc": (f"M頂：左高 ${l_high:.2f} / 右高 ${r_high:.2f}，{status}，"
                             f"目標 ${target:.2f}")
                })
                break

    # ── 頭肩底 ───────────────────────────────────────────────────────────────
    if n >= 40:
        for window in [40, 60, 80]:
            if n < window:
                continue
            seg_l = lows[-window:]
            seg_c = closes[-window:]
            w3    = window // 3

            ls = np.min(seg_l[:w3])
            hd = np.min(seg_l[w3:2*w3])
            rs = np.min(seg_l[2*w3:])
            neckline = np.mean([np.max(seg_c[:w3]), np.max(seg_c[w3:2*w3])])

            if (hd < ls * 0.97 and hd < rs * 0.97 and
                    abs(ls - rs) / (ls + 1e-9) < 0.08 and rs > hd):
                height = neckline - hd
                target = neckline + height
                status = "頸線已突破 🚀" if current > neckline else f"等待突破頸線 ${neckline:.2f}"
                patterns.append({
                    "name": "頭肩底 🔔", "bias": "bull", "bar": n-1, "category": "macro",
                    "neckline": neckline, "target": target,
                    "desc": (f"頭肩底：左肩 ${ls:.2f} / 頭 ${hd:.2f} / 右肩 ${rs:.2f}，"
                             f"{status}，目標 ${target:.2f}")
                })
                break

    # ── 頭肩頂 ───────────────────────────────────────────────────────────────
    if n >= 40:
        for window in [40, 60, 80]:
            if n < window:
                continue
            seg_h = highs[-window:]
            seg_c = closes[-window:]
            w3    = window // 3

            ls = np.max(seg_h[:w3])
            hd = np.max(seg_h[w3:2*w3])
            rs = np.max(seg_h[2*w3:])
            neckline = np.mean([np.min(seg_c[:w3]), np.min(seg_c[w3:2*w3])])

            if (hd > ls * 1.02 and hd > rs * 1.02 and
                    abs(ls - rs) / (ls + 1e-9) < 0.08 and rs < hd):
                height = hd - neckline
                target = neckline - height
                status = "頸線已跌破 💀" if current < neckline else f"警戒頸線 ${neckline:.2f}"
                patterns.append({
                    "name": "頭肩頂 🔔", "bias": "bear", "bar": n-1, "category": "macro",
                    "neckline": neckline, "target": target,
                    "desc": (f"頭肩頂：左肩 ${ls:.2f} / 頭 ${hd:.2f} / 右肩 ${rs:.2f}，"
                             f"{status}，目標 ${target:.2f}")
                })
                break

    # ── 三角收斂（最近20根趨勢）─────────────────────────────────────────────
    if n >= 20:
        seg_h = highs[-20:]
        seg_l = lows[-20:]
        x     = np.arange(20)
        sh    = np.polyfit(x, seg_h, 1)[0]
        sl    = np.polyfit(x, seg_l, 1)[0]

        if sh < 0 and sl > 0:
            if abs(sh + sl) < abs(sh) * 0.4:
                patterns.append({
                    "name": "對稱三角收斂 △", "bias": "neutral",
                    "bar": n-1, "category": "macro",
                    "desc": "近20根對稱三角收斂：高點下降+低點上升，突破方向決定下一波主浪"
                })
            elif abs(sl) < abs(sh) * 0.25 and sh < 0:
                patterns.append({
                    "name": "下降三角 △↓", "bias": "bear",
                    "bar": n-1, "category": "macro",
                    "desc": "近20根下降三角：支撐持平，阻力依次下移，偏向向下突破"
                })
            elif abs(sh) < abs(sl) * 0.25 and sl > 0:
                patterns.append({
                    "name": "上升三角 △↑", "bias": "bull",
                    "bar": n-1, "category": "macro",
                    "desc": "近20根上升三角：阻力持平，支撐依次抬高，偏向向上突破"
                })

    return patterns
