import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time, hashlib

st.set_page_config(page_title="SMC Pro | Multi-Stock", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
:root{--bg:#f5f2ed;--bg2:#edeae4;--card:#ffffff;--card2:#f9f7f4;--border:#e0dbd2;
  --border2:#ccc8be;--bull:#3d8c5f;--bull-bg:#eaf4ee;--bear:#c0392b;--bear-bg:#fdecea;
  --gold:#b07d2e;--gold-bg:#fdf6e3;--text:#1a1a1a;--text2:#6b6560;--text3:#9e9890;
  --accent:#4a7c6f;--mono:'IBM Plex Mono',monospace;--sans:'Noto Sans TC',sans-serif;}
html,body,[class*="css"]{font-family:var(--sans);background-color:var(--bg)!important;color:var(--text);}
.main{background-color:var(--bg)!important;}
.main .block-container{padding:1rem 1.5rem 2rem;max-width:100%;background:var(--bg);}
section[data-testid="stSidebar"]{background:var(--card)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] *{color:var(--text)!important;}
.metric-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:.9rem 1.1rem .8rem;}
.metric-label{font-size:.7rem;color:var(--text2);margin-bottom:5px;}
.metric-value{font-family:var(--mono);font-size:1.7rem;font-weight:700;color:var(--text);line-height:1.1;}
.metric-sub{font-size:.73rem;margin-top:3px;}
.bull{color:var(--bull);} .bear{color:var(--bear);} .gold{color:var(--gold);}
.section-heading{font-size:.95rem;font-weight:700;color:var(--text);margin:1.3rem 0 .65rem;}
.analysis-block{background:var(--card2);border:1px solid var(--border);border-left:3px solid var(--accent);
  border-radius:0 8px 8px 0;padding:.9rem 1.1rem;font-size:.86rem;line-height:1.9;white-space:pre-wrap;}
.white-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:.85rem 1.1rem;margin-bottom:.65rem;}
.info-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid var(--border);font-size:.82rem;}
.info-row:last-child{border-bottom:none;}
.info-key{color:var(--text2);}
.info-val{font-family:var(--mono);font-weight:600;color:var(--text);}
.score-wrap{margin-bottom:10px;}
.score-label-row{display:flex;justify-content:space-between;font-size:.77rem;margin-bottom:4px;color:var(--text2);}
.score-num{font-family:var(--mono);font-weight:700;}
.score-bar-bg{background:var(--bg2);border-radius:3px;height:5px;overflow:hidden;}
.score-bar-fill{height:100%;border-radius:3px;}
.rating-badge{display:inline-block;padding:6px 20px;border-radius:20px;font-family:var(--mono);font-weight:700;font-size:.87rem;}
.pattern-pill{display:inline-block;border-radius:14px;padding:3px 10px;font-size:.71rem;font-family:var(--mono);margin:2px 3px 2px 0;border:1px solid;}
.pill-bull{background:var(--bull-bg);border-color:#a8d5b8;color:var(--bull);}
.pill-bear{background:var(--bear-bg);border-color:#f5b8b3;color:var(--bear);}
.pill-neutral{background:var(--bg2);border-color:var(--border2);color:var(--text2);}
/* monitor badge */
.mon-badge{display:inline-flex;align-items:center;gap:5px;background:var(--bull-bg);
  border:1px solid #a8d5b8;border-radius:20px;padding:2px 10px;font-size:.7rem;color:var(--bull);font-family:var(--mono);}
.mon-badge-off{background:var(--bg2);border-color:var(--border2);color:var(--text3);}
/* stock tab pills */
.stTabs [data-baseweb="tab"]{font-family:var(--mono);font-size:.82rem;padding:6px 14px;}
.stButton>button{background:var(--accent)!important;color:#fff!important;font-family:var(--mono)!important;
  font-weight:600!important;border:none!important;border-radius:7px!important;}
.stButton>button:hover{opacity:.88!important;}
div[data-testid="stSelectbox"]>div>div,div[data-testid="stTextInput"]>div>div{
  background:var(--bg2)!important;border-color:var(--border)!important;border-radius:7px!important;}
hr{border-color:var(--border)!important;}
</style>
""", unsafe_allow_html=True)

# ── imports ───────────────────────────────────────────────────────────────────
from analysis.data_fetcher       import fetch_ohlcv
from analysis.pattern_detector   import detect_all_patterns
from analysis.market_structure   import analyze_market_structure
from analysis.volume_analysis    import analyze_volume
from analysis.support_resistance import find_support_resistance
from analysis.smart_money        import analyze_smart_money
from analysis.signals            import generate_signals
from analysis.scoring            import compute_scores
from analysis.backtest           import run_backtest
from analysis.ai_analysis        import generate_ai_analysis
from analysis.telegram_bot       import send_telegram_alert
from charts.candlestick_chart    import build_chart

# ── session state ─────────────────────────────────────────────────────────────
def _ss(key, val):
    if key not in st.session_state: st.session_state[key] = val

_ss("stock_list",    ["TSLA", "NVDA", "META", "AAPL"])
_ss("cached",        {})      # {ticker: result_dict}
_ss("monitors",      {})      # {ticker: {levels, triggered, active}}
_ss("alert_hashes",  set())
_ss("active_tab",    0)

# ── helpers ───────────────────────────────────────────────────────────────────
def _cc(val):
    sv = str(val)
    if any(k in sv for k in ("多頭","突破","吸籌","放量","低位","看多","看漲")): return "bull"
    if any(k in sv for k in ("空頭","派發","高位","跌破","出貨","看空","看跌")): return "bear"
    return ""

def _row(k, v, cls=""):
    return (f"<div class='info-row'><span class='info-key'>{k}</span>"
            f"<span class='info-val {cls}'>{v}</span></div>")

def _bar(label, val, color):
    return (f"<div class='score-wrap'><div class='score-label-row'><span>{label}</span>"
            f"<span class='score-num' style='color:{color}'>{val}</span></div>"
            f"<div class='score-bar-bg'><div class='score-bar-fill' "
            f"style='width:{val}%;background:{color}'></div></div></div>")

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""<div style='padding:.6rem 0 1rem'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:1.05rem;font-weight:700;
                  color:#4a7c6f;letter-spacing:.08em'>◈ SMC PRO</div>
      <div style='font-size:.62rem;color:#9e9890;letter-spacing:.15em;margin-top:3px'>
        MULTI-STOCK PLATFORM</div></div>""", unsafe_allow_html=True)

    # ── 股票池管理 ────────────────────────────────────────────────────────────
    st.markdown("**股票池**")
    new_tk = st.text_input("新增股票代號", placeholder="輸入代號按 Enter",
                           label_visibility="visible", key="new_tk_input").upper().strip()
    if new_tk and new_tk not in st.session_state.stock_list:
        if st.button("➕ 加入股票池", use_container_width=True, key="add_tk"):
            st.session_state.stock_list.append(new_tk)
            st.rerun()

    # 顯示股票池 + 刪除按鈕
    for tk in list(st.session_state.stock_list):
        mon_on = st.session_state.monitors.get(tk, {}).get("active", False)
        badge  = "🔔" if mon_on else "○"
        cached = "✓" if tk in st.session_state.cached else " "
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"<div style='font-family:IBM Plex Mono,monospace;font-size:.8rem;"
                f"padding:3px 0;color:{'#3d8c5f' if mon_on else '#1a1a1a'}'>"
                f"{badge} {tk} <span style='color:#9e9890;font-size:.68rem'>[{cached}]</span></div>",
                unsafe_allow_html=True)
        with col2:
            if st.button("✕", key=f"del_{tk}", help=f"移除 {tk}"):
                st.session_state.stock_list.remove(tk)
                st.session_state.cached.pop(tk, None)
                st.session_state.monitors.pop(tk, None)
                st.rerun()

    st.markdown("---")

    # ── 全局設定 ──────────────────────────────────────────────────────────────
    st.markdown("**時間週期**")
    interval_map = {"1分鐘":"1m","5分鐘":"5m","15分鐘":"15m",
                    "30分鐘":"30m","1小時":"1h","日線":"1d","週線":"1wk"}
    interval_lbl = st.selectbox("", list(interval_map.keys()), index=5, label_visibility="collapsed")
    interval = interval_map[interval_lbl]

    st.markdown("**K線數量**")
    bar_count = st.slider("", 50, 500, 120, 10, label_visibility="collapsed")

    st.markdown("**自動刷新**")
    refresh_map = {"關閉":0,"30秒":30,"1分鐘":60,"2分鐘":120,"5分鐘":300,"15分鐘":900}
    refresh_lbl = st.selectbox("", list(refresh_map.keys()), index=0, label_visibility="collapsed")
    refresh_sec = refresh_map[refresh_lbl]

    st.markdown("---")
    st.markdown("**Telegram 通知（選填）**")
    tg_token   = st.text_input("Bot Token",  type="password", placeholder="留空則不發送")
    tg_chat_id = st.text_input("Chat ID",    placeholder="留空則不發送")
    if tg_token:   st.session_state["_tg_token"] = tg_token
    if tg_chat_id: st.session_state["_tg_chat"]  = tg_chat_id

    st.markdown("---")
    # 全部分析按鈕
    analyze_all = st.button("🔍 分析全部股票", use_container_width=True, key="analyze_all")

    # 監控總覽
    active_mons = [tk for tk, m in st.session_state.monitors.items() if m.get("active")]
    if active_mons:
        st.markdown(f"**🔔 監控中 ({len(active_mons)} 支)**")
        for tk in active_mons:
            m = st.session_state.monitors[tk]
            trig = len(m.get("triggered", set()))
            st.markdown(
                f"<div style='font-size:.75rem;font-family:IBM Plex Mono,monospace;"
                f"color:#3d8c5f;padding:2px 0'>{tk} · 已觸發 {trig} 次</div>",
                unsafe_allow_html=True)

    st.markdown("""<div style='margin-top:1rem;font-size:.6rem;color:#9e9890;line-height:1.7'>
    ⚠️ 本平台僅供教育研究用途<br>不構成投資建議<br>交易有風險，請自行承擔
    </div>""", unsafe_allow_html=True)


# ── 計算單支股票 ───────────────────────────────────────────────────────────────
def compute_ticker(ticker: str) -> dict | None:
    df = fetch_ohlcv(ticker, interval, bar_count)
    if df is None or len(df) < 20:
        return None
    patterns        = detect_all_patterns(df)
    market_struct   = analyze_market_structure(df)
    volume_analysis = analyze_volume(df)
    sr_levels       = find_support_resistance(df)
    smart_money     = analyze_smart_money(df, volume_analysis)
    signals         = generate_signals(df, patterns, market_struct, volume_analysis, sr_levels)
    scores          = compute_scores(market_struct, volume_analysis, smart_money, signals)
    ai_text         = generate_ai_analysis(ticker, df, patterns, market_struct,
                                           volume_analysis, sr_levels, smart_money, signals, scores)
    return dict(ticker=ticker, interval=interval, interval_lbl=interval_lbl,
                df=df, patterns=patterns, market_struct=market_struct,
                volume_analysis=volume_analysis, sr_levels=sr_levels,
                smart_money=smart_money, signals=signals, scores=scores,
                ai_text=ai_text, tg_token=tg_token, tg_chat_id=tg_chat_id,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'))


# ── 渲染單支股票分析 ───────────────────────────────────────────────────────────
def render_ticker(ctx: dict):
    ticker          = ctx["ticker"]
    interval_label  = ctx["interval_lbl"]
    df              = ctx["df"]
    patterns        = ctx["patterns"]
    market_struct   = ctx["market_struct"]
    volume_analysis = ctx["volume_analysis"]
    sr_levels       = ctx["sr_levels"]
    smart_money     = ctx["smart_money"]
    signals         = ctx["signals"]
    scores          = ctx["scores"]
    ai_text         = ctx["ai_text"]
    tg_token        = ctx["tg_token"]
    tg_chat_id      = ctx["tg_chat_id"]

    latest    = df.iloc[-1];  prev = df.iloc[-2]
    price_chg = latest['Close'] - prev['Close']
    price_pct = price_chg / prev['Close'] * 100
    vol_avg   = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = latest['Volume'] / vol_avg if vol_avg > 0 else 1.0
    trend     = market_struct.get('trend','橫盤整理')
    sig       = signals.get('primary','NEUTRAL')
    overall   = scores.get('overall_rating','中性 ⟷')

    chg_cls  = "bull" if price_chg >= 0 else "bear"
    chg_icon = "▲" if price_chg >= 0 else "▼"
    sig_icon = "🟢" if sig=="BUY" else ("🔴" if sig=="SELL" else "🟡")
    r_col    = "#3d8c5f" if "看多" in overall else ("#c0392b" if "看空" in overall else "#b07d2e")
    mon_on   = st.session_state.monitors.get(ticker, {}).get("active", False)

    # header
    st.markdown(f"""<div style='display:flex;align-items:baseline;gap:10px;padding:.3rem 0 .8rem'>
      <span style='font-family:IBM Plex Mono,monospace;font-size:1.6rem;font-weight:700'>{ticker}</span>
      <span style='font-size:.7rem;color:#9e9890'>{interval_label} · SMC + Price Action</span>
      {'<span class="mon-badge">🔔 監控中</span>' if mon_on else ''}
      <span style='margin-left:auto;font-size:.66rem;color:#b8b2aa;font-family:IBM Plex Mono,monospace'>{ctx["timestamp"]}</span>
    </div>""", unsafe_allow_html=True)

    # metric cards
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>最新收盤</div>
          <div class='metric-value'>${latest['Close']:.2f}</div>
          <div class='metric-sub {chg_cls}'>{chg_icon} {abs(price_chg):.2f} ({abs(price_pct):.2f}%)</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        tc = "bull" if "多頭" in trend else ("bear" if "空頭" in trend else "gold")
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>趨勢結構</div>
          <div class='metric-value {tc}' style='font-size:1.05rem;padding-top:5px'>{trend}</div>
          <div class='metric-sub' style='color:#9e9890'>{market_struct.get('swing_desc','')}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        vc = "bull" if vol_ratio>1.5 else ("bear" if vol_ratio<0.5 else "gold")
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>成交量比率</div>
          <div class='metric-value {vc}'>{vol_ratio:.1f}x</div>
          <div class='metric-sub' style='color:#9e9890'>{volume_analysis.get('vol_signal','')}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        sc2 = "bull" if sig=="BUY" else ("bear" if sig=="SELL" else "gold")
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>主要訊號</div>
          <div class='metric-value {sc2}' style='font-size:1.35rem;padding-top:4px'>{sig_icon} {sig}</div>
          <div class='metric-sub' style='color:#9e9890'>{signals.get('strength','')}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>綜合評級</div>
          <div class='metric-value' style='font-size:.95rem;color:{r_col};padding-top:7px'>{overall}</div>
          <div class='metric-sub' style='color:#9e9890'>信心 {scores.get('confidence',0)}%</div>
        </div>""", unsafe_allow_html=True)

    # chart
    st.markdown("<div class='section-heading'>📈 K線圖表 · 市場結構 · 訊號</div>", unsafe_allow_html=True)
    fig = build_chart(df, ticker, interval, sr_levels, signals, market_struct, patterns)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom":True,"displaylogo":False})

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown("<div class='section-heading'>🧠 AI 綜合分析</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='analysis-block'>{ai_text}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-heading'>📐 市場結構</div>", unsafe_allow_html=True)
        st.markdown(f"""<div class='white-card'>
          {_row("趨勢方向",  trend,                                       _cc(trend))}
          {_row("擺動結構",  market_struct.get('swing_desc','-'),         _cc(market_struct.get('swing_desc','')))}
          {_row("趨勢強度",  f"{market_struct.get('trend_strength',0)}/100")}
          {_row("市場狀態",  market_struct.get('market_state','-'))}
          {_row("結構突破",  market_struct.get('structure_break','-'),    _cc(market_struct.get('structure_break','')))}
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='section-heading'>💰 Smart Money 主力行為</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='analysis-block' style='border-left-color:#b07d2e'>{smart_money.get('description','')}</div>", unsafe_allow_html=True)
        st.markdown(f"""<div class='white-card'>
          {_row("主力行為",   smart_money.get('behavior','-'),            _cc(smart_money.get('behavior','')))}
          {_row("吸籌概率",   f"{smart_money.get('accumulation_prob',0)}%")}
          {_row("派發風險",   f"{smart_money.get('distribution_risk',0)}%")}
          {_row("流動性獵殺", smart_money.get('liquidity_grab','-'))}
          {_row("假突破風險", smart_money.get('fakeout_risk','-'))}
        </div>""", unsafe_allow_html=True)

    with col_r:
        # scores
        st.markdown("<div class='section-heading'>📊 評分系統</div>", unsafe_allow_html=True)
        r_bg = "#eaf4ee" if "看多" in overall else ("#fdecea" if "看空" in overall else "#fdf6e3")
        sh = (_bar("趨勢強度",     scores.get('trend_strength',0),     "#4a7c6f") +
              _bar("主力吸籌概率", scores.get('accumulation_score',0), "#3d8c5f") +
              _bar("主力出貨風險", scores.get('distribution_score',0), "#c0392b") +
              _bar("突破成功率",   scores.get('breakout_score',0),     "#b07d2e") +
              _bar("假突破風險",   scores.get('fakeout_score',0),      "#c0706a") +
              f"<div style='text-align:center;margin-top:1rem'>"
              f"<div class='rating-badge' style='background:{r_bg};border:1.5px solid {r_col};color:{r_col}'>"
              f"{overall}</div></div>")
        st.markdown(f"<div class='white-card'>{sh}</div>", unsafe_allow_html=True)

        # trade setup + monitor button
        st.markdown("<div class='section-heading'>📋 交易建議</div>", unsafe_allow_html=True)
        trade = signals.get('trade_setup', {})
        _ks = trade.get('key_support',0)
        _kr = trade.get('key_resistance',0)
        _bp = trade.get('breakout_level',0)
        _sl = trade.get('stop_loss',0)
        st.markdown(f"""<div class='white-card'>
          {_row("短線方向", trade.get('short_term','-'),  _cc(trade.get('short_term','')))}
          {_row("中線方向", trade.get('mid_term','-'),    _cc(trade.get('mid_term','')))}
          {_row("關鍵支撐", f"${_ks:.2f}")}
          {_row("關鍵阻力", f"${_kr:.2f}")}
          {_row("突破價位", f"${_bp:.2f}")}
          {_row("止損位",   f"${_sl:.2f}", "bear")}
          {_row("風報比",   trade.get('rrr','-'))}
        </div>""", unsafe_allow_html=True)

        # ── 監控按鈕（該股票獨立）────────────────────────────────────────────
        mon = st.session_state.monitors.get(ticker, {})
        mon_active = mon.get("active", False)
        has_tg = bool(st.session_state.get("_tg_token") and st.session_state.get("_tg_chat"))

        if mon_active:
            trig_ct = len(mon.get("triggered", set()))
            st.markdown(f"""<div style='background:#eaf4ee;border:1.5px solid #3d8c5f;
                border-radius:8px;padding:.65rem 1rem;margin-bottom:.5rem;font-size:.78rem'>
              <span style='color:#3d8c5f;font-weight:700'>🔔 監控中</span>
              <span style='color:#6b6560;margin-left:8px;font-family:IBM Plex Mono,monospace;font-size:.72rem'>
                支撐${_ks:.2f} / 阻力${_kr:.2f} / 突破${_bp:.2f} / 止損${_sl:.2f}</span>
              <span style='float:right;color:#9e9890;font-size:.68rem'>已觸發 {trig_ct} 次</span>
            </div>""", unsafe_allow_html=True)
            if st.button(f"⏹ 停止監控 {ticker}", use_container_width=True, key=f"stop_{ticker}"):
                st.session_state.monitors.pop(ticker, None)
                st.rerun()
        else:
            btn_lbl = f"🔔 一鍵監控 {ticker}" if has_tg else f"🔔 監控 {ticker}（請先填 Telegram）"
            if st.button(btn_lbl, use_container_width=True,
                         key=f"start_{ticker}", disabled=not has_tg):
                st.session_state.monitors[ticker] = {
                    "active": True,
                    "triggered": set(),
                    "levels": {
                        "關鍵支撐": {"price":_ks, "direction":"below", "icon":"🟢"},
                        "關鍵阻力": {"price":_kr, "direction":"above", "icon":"🔴"},
                        "突破價位": {"price":_bp, "direction":"above", "icon":"🚀"},
                        "止損位":   {"price":_sl, "direction":"below", "icon":"🛑"},
                    }
                }
                st.rerun()

        # patterns
        st.markdown("<div class='section-heading'>🕯️ K線型態</div>", unsafe_allow_html=True)
        all_pats = (patterns.get('single_k',[]) + patterns.get('double_k',[]) +
                    patterns.get('triple_k',[]) + patterns.get('macro',[]))
        pills = ""
        for p in all_pats:
            cls = "pill-bull" if p['bias']=='bull' else ("pill-bear" if p['bias']=='bear' else "pill-neutral")
            pills += f"<span class='pattern-pill {cls}'>{p['name']}</span>"
        if not pills:
            pills = "<span style='color:#9e9890;font-size:.78rem'>未偵測到明顯型態</span>"
        st.markdown(f"<div class='white-card' style='line-height:2.2'>{pills}</div>", unsafe_allow_html=True)

        # volume
        st.markdown("<div class='section-heading'>📦 成交量（最新5根）</div>", unsafe_allow_html=True)
        r5    = volume_analysis.get('recent5_ratio',1.0)
        vbias = volume_analysis.get('vol_bias','')
        vdiv  = volume_analysis.get('vol_divergence','') or '無'
        st.markdown(f"""<div class='white-card'>
          {_row("最新1根訊號", volume_analysis.get('vol_signal','-'),  _cc(volume_analysis.get('vol_signal','')))}
          {_row("最新1根量比", f"{vol_ratio:.1f}x 均量")}
          {_row("近5根量比",   f"{r5:.1f}x · {vbias}",
                "bull" if "多頭" in vbias else ("bear" if "空頭" in vbias else ""))}
          {_row("主力動向",   volume_analysis.get('smart_vol','-'),   _cc(volume_analysis.get('smart_vol','')))}
          {_row("量價背離",   vdiv)}
        </div>""", unsafe_allow_html=True)

    # backtest
    st.markdown("<div class='section-heading'>📉 回測系統</div>", unsafe_allow_html=True)
    bt = run_backtest(df, signals.get('signal_history',[]))
    bc = st.columns(5)
    for col,(lbl,val,good) in zip(bc,[
        ("勝率",     f"{bt.get('win_rate',0):.1f}%",    bt.get('win_rate',0)>50),
        ("盈虧比",   f"{bt.get('profit_factor',0):.2f}", bt.get('profit_factor',0)>1.5),
        ("最大回撤", f"{bt.get('max_dd',0):.1f}%",       bt.get('max_dd',0)<15),
        ("交易次數", str(bt.get('total_trades',0)),       True),
        ("淨收益率", f"{bt.get('net_return',0):.1f}%",   bt.get('net_return',0)>0),
    ]):
        color = "#3d8c5f" if good else "#c0392b"
        with col:
            st.markdown(f"""<div class='metric-card' style='text-align:center'>
              <div class='metric-label'>{lbl}</div>
              <div class='metric-value' style='color:{color};font-size:1.3rem'>{val}</div>
            </div>""", unsafe_allow_html=True)

    # equity curve
    eq = bt.get('equity_curve',[])
    if len(eq) > 2:
        ec = "#3d8c5f" if eq[-1]>=eq[0] else "#c0392b"
        ef = "rgba(61,140,95,.08)" if eq[-1]>=eq[0] else "rgba(192,57,43,.08)"
        efig = go.Figure()
        efig.add_trace(go.Scatter(y=eq,mode='lines',line=dict(color=ec,width=2),
                                  fill='tozeroy',fillcolor=ef))
        efig.update_layout(plot_bgcolor='#fff',paper_bgcolor='#f9f7f4',height=160,
            margin=dict(l=45,r=15,t=28,b=25),showlegend=False,
            title=dict(text='Equity Curve',font=dict(family='Noto Sans TC',size=11,color='#6b6560'),x=.01),
            xaxis=dict(showgrid=False,tickfont=dict(size=8,color='#9e9890')),
            yaxis=dict(gridcolor='#ede9e3',tickfont=dict(size=8,color='#9e9890')))
        st.plotly_chart(efig, use_container_width=True)

    # Telegram signal alert (BUY/SELL)
    if tg_token and tg_chat_id and sig in ('BUY','SELL'):
        h = hashlib.md5(f"{ticker}{interval}{sig}{datetime.now().strftime('%Y%m%d%H')}".encode()).hexdigest()
        if h not in st.session_state.alert_hashes:
            names = ', '.join([p['name'] for p in all_pats[:3]]) or '無'
            msg = (f"🚨 *{ticker} 交易訊號*\n\n"
                   f"訊號：{'🟢 BUY' if sig=='BUY' else '🔴 SELL'}\n"
                   f"趨勢：{trend}\n型態：{names}\n評級：{overall}\n\n{ai_text[:300]}...")
            if send_telegram_alert(tg_token, tg_chat_id, msg):
                st.session_state.alert_hashes.add(h)
                st.success(f"📱 {ticker} Telegram 訊號已發送")


# ── 背景監控（所有股票）────────────────────────────────────────────────────────
def run_all_monitors():
    active = {tk: m for tk, m in st.session_state.monitors.items() if m.get("active")}
    if not active: return
    tg_t = st.session_state.get("_tg_token","")
    tg_c = st.session_state.get("_tg_chat","")
    if not tg_t or not tg_c: return

    import yfinance as yf
    for ticker, mon in active.items():
        try:
            cur = float(yf.Ticker(ticker).fast_info.last_price)
        except Exception:
            continue
        for label, cfg in mon["levels"].items():
            key = f"{ticker}_{label}_{cfg['price']:.2f}"
            if key in mon["triggered"]: continue
            hit = ((cfg["direction"]=="above" and cur >= cfg["price"]) or
                   (cfg["direction"]=="below" and cur <= cfg["price"]))
            if hit:
                mon["triggered"].add(key)
                arrow = "突破 ↑" if cfg["direction"]=="above" else "跌破 ↓"
                msg = (f"{cfg['icon']} *{ticker} 價位觸及*\n\n"
                       f"觸發：*{label}*\n監控價：${cfg['price']:.2f}\n"
                       f"當前價：${cur:.2f}\n方向：{arrow}\n"
                       f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                send_telegram_alert(tg_t, tg_c, msg)
                st.toast(f"{cfg['icon']} {ticker} {label} ${cfg['price']:.2f} 已觸及！", icon="🔔")

run_all_monitors()


# ── 主介面：多股票 Tabs ────────────────────────────────────────────────────────
stock_list = st.session_state.stock_list
if not stock_list:
    st.info("請在左側股票池新增股票代號")
    st.stop()

# 「分析全部」按鈕
if analyze_all:
    progress = st.progress(0, text="分析中...")
    for i, tk in enumerate(stock_list):
        progress.progress((i+1)/len(stock_list), text=f"正在分析 {tk}...")
        result = compute_ticker(tk)
        if result:
            st.session_state.cached[tk] = result
        else:
            st.warning(f"⚠️ {tk} 數據獲取失敗")
    progress.empty()
    st.rerun()

# 個別分析按鈕行
btn_cols = st.columns(min(len(stock_list), 6))
for i, tk in enumerate(stock_list[:6]):
    with btn_cols[i]:
        cached_ok = tk in st.session_state.cached
        mon_on    = st.session_state.monitors.get(tk,{}).get("active",False)
        label     = f"{'🔔 ' if mon_on else ''}{'✓ ' if cached_ok else ''}{tk}"
        if st.button(label, use_container_width=True, key=f"single_{tk}"):
            with st.spinner(f"分析 {tk}..."):
                result = compute_ticker(tk)
            if result:
                st.session_state.cached[tk] = result
            else:
                st.error(f"❌ {tk} 數據獲取失敗")
            st.rerun()

# Tabs
tab_labels = []
for tk in stock_list:
    cached_ok = tk in st.session_state.cached
    mon_on    = st.session_state.monitors.get(tk,{}).get("active",False)
    prefix    = "🔔 " if mon_on else ("✓ " if cached_ok else "○ ")
    tab_labels.append(f"{prefix}{tk}")

tabs = st.tabs(tab_labels)
for tab, tk in zip(tabs, stock_list):
    with tab:
        if tk in st.session_state.cached:
            render_ticker(st.session_state.cached[tk])
        else:
            st.markdown(f"""<div style='text-align:center;padding:4rem 2rem;color:#b8b2aa'>
              <div style='font-size:2rem;margin-bottom:.8rem;color:#ccc8be'>◈</div>
              <div style='font-size:.9rem;color:#9e9890'>{tk} 尚未分析</div>
              <div style='font-size:.75rem;margin-top:.4rem;color:#b8b2aa'>
                點擊上方「{tk}」按鈕 或 「🔍 分析全部股票」</div>
            </div>""", unsafe_allow_html=True)

# 自動刷新
if refresh_sec > 0 and st.session_state.cached:
    time.sleep(refresh_sec)
    for tk in list(st.session_state.cached.keys()):
        result = compute_ticker(tk)
        if result: st.session_state.cached[tk] = result
    st.rerun()
elif st.session_state.monitors and any(m.get("active") for m in st.session_state.monitors.values()):
    time.sleep(30)
    st.rerun()
