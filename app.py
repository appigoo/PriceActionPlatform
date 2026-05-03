import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
import json
import requests
import hashlib
from typing import Optional

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SMC Pro | Price Action Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── STYLE ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

:root {
  --bg: #0d0f14;
  --bg2: #131720;
  --bg3: #1a2030;
  --card: #1e2535;
  --border: #2a3348;
  --accent: #00d4aa;
  --accent2: #0099ff;
  --bull: #00c896;
  --bear: #ff4560;
  --text: #e2e8f0;
  --text2: #94a3b8;
  --gold: #f5a623;
  --mono: 'IBM Plex Mono', monospace;
  --sans: 'Noto Sans TC', sans-serif;
}

html, body, [class*="css"] {
  font-family: var(--sans);
  background-color: var(--bg);
  color: var(--text);
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--bg2) !important;
  border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Main container */
.main .block-container { padding: 1rem 1.5rem; max-width: 100%; }

/* Metric cards */
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  font-family: var(--mono);
}
.metric-label { font-size: 0.65rem; color: var(--text2); letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 4px; }
.metric-value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
.metric-sub { font-size: 0.75rem; margin-top: 2px; }
.bull-color { color: var(--bull); }
.bear-color { color: var(--bear); }
.gold-color { color: var(--gold); }
.accent-color { color: var(--accent); }

/* Signal box */
.signal-box {
  background: var(--bg2);
  border-radius: 10px;
  border: 1px solid var(--border);
  padding: 1.25rem;
  margin-bottom: 0.75rem;
}
.signal-title { font-size: 0.7rem; color: var(--text2); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }

/* Score bars */
.score-bar-bg {
  background: var(--bg3);
  border-radius: 4px;
  height: 6px;
  margin: 4px 0 10px;
  overflow: hidden;
}
.score-bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease; }

/* Rating badge */
.rating-badge {
  display: inline-block;
  padding: 6px 18px;
  border-radius: 20px;
  font-family: var(--mono);
  font-weight: 700;
  font-size: 0.9rem;
  letter-spacing: 0.05em;
}

/* Analysis text */
.analysis-block {
  background: var(--bg3);
  border-left: 3px solid var(--accent);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.25rem;
  font-size: 0.88rem;
  line-height: 1.8;
  color: var(--text);
  margin: 0.5rem 0;
}

/* Trade suggestion table */
.trade-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-family: var(--mono);
  font-size: 0.82rem;
}
.trade-row:last-child { border-bottom: none; }
.trade-key { color: var(--text2); }
.trade-val { font-weight: 600; }

/* Pattern pills */
.pattern-pill {
  display: inline-block;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 0.72rem;
  margin: 2px;
  font-family: var(--mono);
}
.pattern-bull { border-color: var(--bull); color: var(--bull); }
.pattern-bear { border-color: var(--bear); color: var(--bear); }
.pattern-neutral { border-color: var(--text2); color: var(--text2); }

/* Section headers */
.section-header {
  font-family: var(--mono);
  font-size: 0.65rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text2);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
  margin: 1.25rem 0 0.75rem;
}

/* Plotly container */
.plotly-graph-div { border-radius: 8px; overflow: hidden; }

/* Streamlit elements */
div[data-testid="stSelectbox"] > div, div[data-testid="stTextInput"] > div > div { 
  background: var(--card) !important; border-color: var(--border) !important; color: var(--text) !important; border-radius: 6px !important;
}
.stButton > button {
  background: var(--accent) !important; color: #000 !important; font-family: var(--mono) !important;
  font-weight: 700 !important; border: none !important; border-radius: 6px !important;
  letter-spacing: 0.05em !important; transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }

div[data-testid="stMetric"] { background: var(--card); border-radius: 8px; padding: 12px; border: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)

# ─── IMPORTS ────────────────────────────────────────────────────────────────────
from analysis.data_fetcher import fetch_ohlcv
from analysis.pattern_detector import detect_all_patterns
from analysis.market_structure import analyze_market_structure
from analysis.volume_analysis import analyze_volume
from analysis.support_resistance import find_support_resistance
from analysis.smart_money import analyze_smart_money
from analysis.signals import generate_signals
from analysis.scoring import compute_scores
from analysis.backtest import run_backtest
from analysis.ai_analysis import generate_ai_analysis
from analysis.telegram_bot import send_telegram_alert
from charts.candlestick_chart import build_chart

# ─── SESSION STATE ──────────────────────────────────────────────────────────────
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None
if "alert_sent_hash" not in st.session_state:
    st.session_state.alert_sent_hash = set()

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 1.5rem;'>
      <div style='font-family:IBM Plex Mono,monospace; font-size:1.1rem; font-weight:700; color:#00d4aa; letter-spacing:0.1em;'>◈ SMC PRO</div>
      <div style='font-size:0.65rem; color:#94a3b8; letter-spacing:0.2em; margin-top:4px;'>PRICE ACTION PLATFORM</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**股票代號**")
    ticker_input = st.text_input("", value="TSLA", placeholder="TSLA, NVDA, AAPL...", label_visibility="collapsed").upper().strip()

    st.markdown("**時間週期**")
    interval_map = {
        "1分鐘 (1m)": "1m",
        "5分鐘 (5m)": "5m",
        "15分鐘 (15m)": "15m",
        "30分鐘 (30m)": "30m",
        "1小時 (1h)": "1h",
        "日線 (1d)": "1d",
        "週線 (1wk)": "1wk",
    }
    interval_label = st.selectbox("", list(interval_map.keys()), index=5, label_visibility="collapsed")
    interval = interval_map[interval_label]

    st.markdown("**K線數量**")
    bar_count = st.slider("", 50, 500, 120, 10, label_visibility="collapsed")

    st.markdown("**自動刷新**")
    refresh_map = {"關閉": 0, "30秒": 30, "1分鐘": 60, "2分鐘": 120, "5分鐘": 300, "15分鐘": 900}
    refresh_label = st.selectbox("", list(refresh_map.keys()), index=0, label_visibility="collapsed")
    refresh_sec = refresh_map[refresh_label]

    st.markdown("---")
    st.markdown("**Telegram 通知**")
    tg_token = st.text_input("Bot Token", type="password", placeholder="可選")
    tg_chat_id = st.text_input("Chat ID", placeholder="可選")

    st.markdown("---")
    analyze_btn = st.button("🔍 開始分析", use_container_width=True)
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.62rem; color:#475569; line-height:1.6;'>
    ⚠️ 本平台僅供教育研究<br>不構成投資建議<br>交易有風險，自行負責
    </div>
    """, unsafe_allow_html=True)

# ─── HEADER ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"""
    <div style='padding: 0.5rem 0;'>
      <span style='font-family:IBM Plex Mono,monospace; font-size:1.8rem; font-weight:700; color:#e2e8f0;'>{ticker_input}</span>
      <span style='font-family:IBM Plex Mono,monospace; font-size:0.75rem; color:#94a3b8; margin-left:12px; letter-spacing:0.1em;'>{interval_label} · SMC + Price Action</span>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.markdown(f"""
    <div style='text-align:right; padding:0.5rem 0; font-family:IBM Plex Mono,monospace; font-size:0.65rem; color:#475569;'>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN LOGIC ─────────────────────────────────────────────────────────────────
def run_analysis(ticker, interval, bar_count, tg_token, tg_chat_id):
    with st.spinner("📡 正在獲取市場數據..."):
        df = fetch_ohlcv(ticker, interval, bar_count)
    
    if df is None or len(df) < 20:
        st.error(f"❌ 無法獲取 {ticker} 的數據，請確認代號是否正確")
        return

    with st.spinner("🧠 AI 正在分析市場結構..."):
        patterns = detect_all_patterns(df)
        market_struct = analyze_market_structure(df)
        volume_analysis = analyze_volume(df)
        sr_levels = find_support_resistance(df)
        smart_money = analyze_smart_money(df, volume_analysis)
        signals = generate_signals(df, patterns, market_struct, volume_analysis, sr_levels)
        scores = compute_scores(market_struct, volume_analysis, smart_money, signals)
        ai_text = generate_ai_analysis(ticker, df, patterns, market_struct, volume_analysis, sr_levels, smart_money, signals, scores)

    # ── METRIC CARDS ────────────────────────────────────────────────────────────
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    price_chg = latest['Close'] - prev['Close']
    price_pct = price_chg / prev['Close'] * 100
    chg_color = "bull-color" if price_chg >= 0 else "bear-color"
    chg_arrow = "▲" if price_chg >= 0 else "▼"

    vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = latest['Volume'] / vol_avg if vol_avg > 0 else 1.0
    
    trend_label = market_struct.get('trend', '橫盤')
    trend_color = "bull-color" if "多頭" in trend_label else ("bear-color" if "空頭" in trend_label else "gold-color")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>最新收盤</div>
          <div class='metric-value'>${latest['Close']:.2f}</div>
          <div class='metric-sub {chg_color}'>{chg_arrow} {abs(price_chg):.2f} ({abs(price_pct):.2f}%)</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>趨勢結構</div>
          <div class='metric-value {trend_color}' style='font-size:1.1rem;'>{trend_label}</div>
          <div class='metric-sub' style='color:#94a3b8;'>{market_struct.get('sub_trend','')}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        vol_color = "bull-color" if vol_ratio > 1.5 else ("bear-color" if vol_ratio < 0.5 else "gold-color")
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>成交量比率</div>
          <div class='metric-value {vol_color}'>{vol_ratio:.1f}x</div>
          <div class='metric-sub' style='color:#94a3b8;'>{volume_analysis.get('vol_signal','')}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        sig = signals.get('primary', 'NEUTRAL')
        sig_color = "bull-color" if sig == "BUY" else ("bear-color" if sig == "SELL" else "gold-color")
        sig_icon = "🟢" if sig == "BUY" else ("🔴" if sig == "SELL" else "🟡")
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>主要訊號</div>
          <div class='metric-value {sig_color}' style='font-size:1.4rem;'>{sig_icon} {sig}</div>
          <div class='metric-sub' style='color:#94a3b8;'>{signals.get('strength','')}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        overall = scores.get('overall_rating', '中性')
        r_color = "#00c896" if "看多" in overall else ("#ff4560" if "看空" in overall else "#f5a623")
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>綜合評級</div>
          <div class='metric-value' style='font-size:1rem; color:{r_color};'>{overall}</div>
          <div class='metric-sub' style='color:#94a3b8;'>信心: {scores.get('confidence',0)}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── CHART ───────────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📈 K線圖表 · 市場結構 · 訊號</div>", unsafe_allow_html=True)
    fig = build_chart(df, ticker, interval, sr_levels, signals, market_struct, patterns)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displaylogo": False})

    # ── ANALYSIS + PATTERNS ──────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<div class='section-header'>🧠 AI 綜合分析</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='analysis-block'>{ai_text}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>📐 市場結構詳情</div>", unsafe_allow_html=True)
        struct_items = [
            ("趨勢方向", market_struct.get('trend', '-')),
            ("HH/HL/LH/LL", market_struct.get('swing_desc', '-')),
            ("趨勢強度", f"{market_struct.get('trend_strength', 0)}/100"),
            ("市場狀態", market_struct.get('market_state', '-')),
            ("結構突破", market_struct.get('structure_break', '-')),
        ]
        for k, v in struct_items:
            color = "#00c896" if "多" in str(v) or "突破" in str(v) else ("#ff4560" if "空" in str(v) else "#e2e8f0")
            st.markdown(f"""
            <div class='trade-row'>
              <span class='trade-key'>{k}</span>
              <span class='trade-val' style='color:{color};'>{v}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>💰 主力行為分析 (SMC)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='analysis-block' style='border-color:#f5a623;'>{smart_money.get('description','')}</div>", unsafe_allow_html=True)

        sm_items = [
            ("主力行為", smart_money.get('behavior', '-')),
            ("吸籌概率", f"{smart_money.get('accumulation_prob', 0)}%"),
            ("派發風險", f"{smart_money.get('distribution_risk', 0)}%"),
            ("流動性獵殺", smart_money.get('liquidity_grab', '-')),
            ("假突破風險", smart_money.get('fakeout_risk', '-')),
        ]
        for k, v in sm_items:
            color = "#00c896" if "吸" in str(v) or "低" in str(v) else ("#ff4560" if "派" in str(v) or "高" in str(v) else "#e2e8f0")
            st.markdown(f"""
            <div class='trade-row'>
              <span class='trade-key'>{k}</span>
              <span class='trade-val' style='color:{color};'>{v}</span>
            </div>""", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='section-header'>📊 評分系統</div>", unsafe_allow_html=True)
        score_items = [
            ("趨勢強度", scores.get('trend_strength', 0), "#0099ff"),
            ("主力吸籌概率", scores.get('accumulation_score', 0), "#00c896"),
            ("主力出貨風險", scores.get('distribution_score', 0), "#ff4560"),
            ("突破成功率", scores.get('breakout_score', 0), "#f5a623"),
            ("假突破風險", scores.get('fakeout_score', 0), "#ff6b6b"),
        ]
        score_html = ""
        for label, val, color in score_items:
            score_html += f"""
            <div style='margin-bottom:10px;'>
              <div style='display:flex;justify-content:space-between;font-family:IBM Plex Mono,monospace;font-size:0.75rem;'>
                <span style='color:#94a3b8;'>{label}</span>
                <span style='color:{color};font-weight:700;'>{val}</span>
              </div>
              <div class='score-bar-bg'>
                <div class='score-bar-fill' style='width:{val}%;background:{color};'></div>
              </div>
            </div>"""
        overall = scores.get('overall_rating', '中性')
        r_bg = "#00c896" if "強烈看多" in overall else ("#4ade80" if "偏多" in overall else ("#ff4560" if "強烈看空" in overall else ("#f87171" if "偏空" in overall else "#f5a623")))
        score_html += f"""
        <div style='text-align:center;margin-top:1rem;'>
          <div class='rating-badge' style='background:{r_bg}22;border:2px solid {r_bg};color:{r_bg};font-size:1.1rem;padding:10px 28px;'>
            {overall}
          </div>
        </div>"""
        st.markdown(f"<div class='signal-box'>{score_html}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>📋 交易建議</div>", unsafe_allow_html=True)
        trade = signals.get('trade_setup', {})
        trade_items = [
            ("短線方向", trade.get('short_term', '-')),
            ("中線方向", trade.get('mid_term', '-')),
            ("關鍵支撐", f"${trade.get('key_support', 0):.2f}"),
            ("關鍵阻力", f"${trade.get('key_resistance', 0):.2f}"),
            ("突破價位", f"${trade.get('breakout_level', 0):.2f}"),
            ("止損位", f"${trade.get('stop_loss', 0):.2f}"),
            ("風報比", trade.get('rrr', '-')),
        ]
        trade_html = ""
        for k, v in trade_items:
            color = "#00c896" if "多" in str(v) or "看漲" in str(v) else ("#ff4560" if "空" in str(v) or "看跌" in str(v) else "#e2e8f0")
            trade_html += f"""
            <div class='trade-row'>
              <span class='trade-key'>{k}</span>
              <span class='trade-val' style='color:{color};'>{v}</span>
            </div>"""
        st.markdown(f"<div class='signal-box'>{trade_html}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>🕯️ 辨識到的K線型態</div>", unsafe_allow_html=True)
        pattern_html = ""
        for p in patterns.get('detected', []):
            cls = "pattern-bull" if p['bias'] == 'bull' else ("pattern-bear" if p['bias'] == 'bear' else "pattern-neutral")
            pattern_html += f"<span class='pattern-pill {cls}'>{p['name']}</span>"
        if not pattern_html:
            pattern_html = "<span style='color:#475569;font-size:0.8rem;'>未偵測到明顯型態</span>"
        st.markdown(f"<div class='signal-box'>{pattern_html}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>📦 成交量分析</div>", unsafe_allow_html=True)
        vol_items = [
            ("成交量狀態", volume_analysis.get('vol_signal', '-')),
            ("比均量", f"{vol_ratio:.1f}x"),
            ("成交量解讀", volume_analysis.get('interpretation', '-')),
            ("主力動向", volume_analysis.get('smart_vol', '-')),
        ]
        vol_html = ""
        for k, v in vol_items:
            color = "#00c896" if any(w in str(v) for w in ["放量", "進場", "吸"]) else ("#ff4560" if any(w in str(v) for w in ["出貨", "派", "恐慌"]) else "#e2e8f0")
            vol_html += f"""
            <div class='trade-row'>
              <span class='trade-key'>{k}</span>
              <span class='trade-val' style='color:{color};'>{v}</span>
            </div>"""
        st.markdown(f"<div class='signal-box'>{vol_html}</div>", unsafe_allow_html=True)

    # ── BACKTEST ─────────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📉 回測系統</div>", unsafe_allow_html=True)
    bt = run_backtest(df, signals.get('signal_history', []))
    bt_cols = st.columns(5)
    bt_metrics = [
        ("勝率", f"{bt.get('win_rate', 0):.1f}%", bt.get('win_rate', 0) > 50),
        ("盈虧比", f"{bt.get('profit_factor', 0):.2f}", bt.get('profit_factor', 0) > 1.5),
        ("最大回撤", f"{bt.get('max_dd', 0):.1f}%", bt.get('max_dd', 0) < 15),
        ("總交易次數", str(bt.get('total_trades', 0)), True),
        ("淨收益率", f"{bt.get('net_return', 0):.1f}%", bt.get('net_return', 0) > 0),
    ]
    for col, (label, val, good) in zip(bt_cols, bt_metrics):
        color = "#00c896" if good else "#ff4560"
        with col:
            st.markdown(f"""
            <div class='metric-card' style='text-align:center;'>
              <div class='metric-label'>{label}</div>
              <div class='metric-value' style='color:{color};font-size:1.3rem;'>{val}</div>
            </div>""", unsafe_allow_html=True)

    # Equity curve
    if bt.get('equity_curve'):
        eq_fig = go.Figure()
        eq_fig.add_trace(go.Scatter(
            y=bt['equity_curve'], mode='lines',
            line=dict(color='#00d4aa', width=2),
            fill='tozeroy', fillcolor='rgba(0,212,170,0.08)'
        ))
        eq_fig.update_layout(
            plot_bgcolor='#1a2030', paper_bgcolor='#1e2535',
            height=180, margin=dict(l=40, r=20, t=20, b=30),
            xaxis=dict(showgrid=False, color='#475569'),
            yaxis=dict(gridcolor='#2a3348', color='#94a3b8'),
            font=dict(family='IBM Plex Mono', color='#94a3b8', size=10),
            title=dict(text='Equity Curve', font=dict(size=11, color='#94a3b8'), x=0.02)
        )
        st.plotly_chart(eq_fig, use_container_width=True)

    # ── TELEGRAM ─────────────────────────────────────────────────────────────────
    if tg_token and tg_chat_id:
        sig_primary = signals.get('primary', 'NEUTRAL')
        if sig_primary in ('BUY', 'SELL'):
            msg_hash = hashlib.md5(f"{ticker}{interval}{sig_primary}{datetime.now().strftime('%Y%m%d%H')}".encode()).hexdigest()
            if msg_hash not in st.session_state.alert_sent_hash:
                tg_msg = f"""🚨 *{ticker} 交易訊號*

訊號：{'🟢 BUY 做多' if sig_primary == 'BUY' else '🔴 SELL 做空'}
趨勢：{market_struct.get('trend','-')}
型態：{', '.join([p['name'] for p in patterns.get('detected', [])[:3]])}
成交量：{volume_analysis.get('vol_signal','-')}
評級：{scores.get('overall_rating','-')}

{ai_text[:300]}..."""
                if send_telegram_alert(tg_token, tg_chat_id, tg_msg):
                    st.session_state.alert_sent_hash.add(msg_hash)
                    st.success("📱 Telegram 通知已發送")

    st.session_state.last_analysis = {"ticker": ticker, "time": datetime.now()}

# ─── TRIGGER ────────────────────────────────────────────────────────────────────
if analyze_btn:
    run_analysis(ticker_input, interval, bar_count, tg_token, tg_chat_id)
elif refresh_sec > 0 and st.session_state.last_analysis:
    st.markdown(f"""
    <div style='text-align:center; color:#475569; font-family:IBM Plex Mono,monospace; font-size:0.7rem; padding:2rem;'>
    自動刷新每 {refresh_sec} 秒 · 下次刷新中...
    </div>""", unsafe_allow_html=True)
    time.sleep(refresh_sec)
    run_analysis(ticker_input, interval, bar_count, tg_token, tg_chat_id)
    st.rerun()
else:
    st.markdown("""
    <div style='text-align:center; padding: 5rem 2rem; color:#475569;'>
      <div style='font-size:3rem; margin-bottom:1rem;'>◈</div>
      <div style='font-family:IBM Plex Mono,monospace; font-size:1rem; color:#64748b;'>在左側輸入股票代號，點擊「開始分析」</div>
      <div style='font-size:0.75rem; margin-top:0.5rem; color:#475569;'>支援 US 股票 · ETF · 支援多個時間週期</div>
    </div>
    """, unsafe_allow_html=True)
