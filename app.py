import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime
import time
import hashlib

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SMC Pro | Price Action Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── WARM CREAM STYLE（附件風格）──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

:root {
  --bg:        #f5f2ed;
  --bg2:       #edeae4;
  --card:      #ffffff;
  --card2:     #f9f7f4;
  --border:    #e0dbd2;
  --border2:   #ccc8be;
  --bull:      #3d8c5f;
  --bull-bg:   #eaf4ee;
  --bear:      #c0392b;
  --bear-bg:   #fdecea;
  --gold:      #b07d2e;
  --gold-bg:   #fdf6e3;
  --text:      #1a1a1a;
  --text2:     #6b6560;
  --text3:     #9e9890;
  --accent:    #4a7c6f;
  --mono:      'IBM Plex Mono', monospace;
  --sans:      'Noto Sans TC', sans-serif;
}

html, body, [class*="css"] {
  font-family: var(--sans);
  background-color: var(--bg) !important;
  color: var(--text);
}
.main { background-color: var(--bg) !important; }
.main .block-container { padding: 1.2rem 2rem 2rem; max-width: 100%; background: var(--bg); }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--card) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Metric card */
.metric-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1rem 1.25rem 0.9rem;
}
.metric-label {
  font-family: var(--sans);
  font-size: 0.72rem;
  color: var(--text2);
  margin-bottom: 6px;
}
.metric-value {
  font-family: var(--mono);
  font-size: 2rem;
  font-weight: 700;
  color: var(--text);
  line-height: 1.1;
}
.metric-sub {
  font-family: var(--sans);
  font-size: 0.75rem;
  margin-top: 4px;
}
.bull  { color: var(--bull); }
.bear  { color: var(--bear); }
.gold  { color: var(--gold); }
.accent { color: var(--accent); }

/* Section heading */
.section-heading {
  font-family: var(--sans);
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
  margin: 1.5rem 0 0.75rem;
}

/* Analysis block */
.analysis-block {
  background: var(--card2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.2rem;
  font-size: 0.88rem;
  line-height: 1.9;
  color: var(--text);
  white-space: pre-wrap;
}

/* White card */
.white-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.9rem 1.2rem;
  margin-bottom: 0.75rem;
}

/* Info row */
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.83rem;
}
.info-row:last-child { border-bottom: none; }
.info-key { color: var(--text2); }
.info-val { font-family: var(--mono); font-weight: 600; color: var(--text); }

/* Score bar */
.score-wrap { margin-bottom: 11px; }
.score-label-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  margin-bottom: 5px;
  color: var(--text2);
}
.score-num { font-family: var(--mono); font-weight: 700; }
.score-bar-bg { background: var(--bg2); border-radius: 3px; height: 5px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 3px; }

/* Rating badge */
.rating-badge {
  display: inline-block;
  padding: 6px 20px;
  border-radius: 20px;
  font-family: var(--mono);
  font-weight: 700;
  font-size: 0.88rem;
}

/* Pattern pills */
.pattern-pill {
  display: inline-block;
  border-radius: 14px;
  padding: 3px 10px;
  font-size: 0.72rem;
  font-family: var(--mono);
  margin: 2px 3px 2px 0;
  border: 1px solid;
}
.pill-bull { background: var(--bull-bg); border-color: #a8d5b8; color: var(--bull); }
.pill-bear { background: var(--bear-bg); border-color: #f5b8b3; color: var(--bear); }
.pill-neutral { background: var(--bg2); border-color: var(--border2); color: var(--text2); }

/* Streamlit overrides */
.stButton > button {
  background: var(--accent) !important;
  color: #fff !important;
  font-family: var(--mono) !important;
  font-weight: 600 !important;
  border: none !important;
  border-radius: 7px !important;
  padding: 0.5rem 1rem !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] > div > div {
  background: var(--bg2) !important;
  border-color: var(--border) !important;
  border-radius: 7px !important;
}
hr { border-color: var(--border) !important; }
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
if "last_analysis"   not in st.session_state: st.session_state.last_analysis   = None
if "alert_sent_hash" not in st.session_state: st.session_state.alert_sent_hash = set()
# 價位監控
if "monitor_active"  not in st.session_state: st.session_state.monitor_active  = False
if "monitor_levels"  not in st.session_state: st.session_state.monitor_levels  = {}
if "monitor_ticker"  not in st.session_state: st.session_state.monitor_ticker  = ""
if "monitor_triggered" not in st.session_state: st.session_state.monitor_triggered = set()

# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:0.75rem 0 1.25rem;'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:1.05rem;font-weight:700;
                  color:#4a7c6f;letter-spacing:0.08em;'>◈ SMC PRO</div>
      <div style='font-size:0.65rem;color:#9e9890;letter-spacing:0.15em;margin-top:3px;'>
        PRICE ACTION PLATFORM
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**股票代號**")
    ticker_input = st.text_input(
        "", value="TSLA", placeholder="TSLA, NVDA, AAPL...",
        label_visibility="collapsed"
    ).upper().strip()

    st.markdown("**時間週期**")
    interval_map = {
        "1分鐘": "1m", "5分鐘": "5m", "15分鐘": "15m",
        "30分鐘": "30m", "1小時": "1h", "日線": "1d", "週線": "1wk",
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
    st.markdown("**Telegram 通知（選填）**")
    tg_token = st.text_input("Bot Token", type="password", placeholder="留空則不發送")
    tg_chat_id = st.text_input("Chat ID", placeholder="留空則不發送")

    st.markdown("---")
    analyze_btn = st.button("🔍 開始分析", use_container_width=True)

    # 監控狀態指示
    if st.session_state.monitor_active:
        mon_ticker = st.session_state.monitor_ticker
        mon_levels = st.session_state.monitor_levels
        level_lines = "".join([
            f"<div style='display:flex;justify-content:space-between;'>"
            f"<span>{cfg["color"]} {lbl}</span>"
            f"<span style='font-family:IBM Plex Mono,monospace;'>${cfg["price"]:.2f}</span></div>"
            for lbl, cfg in mon_levels.items()
        ])
        triggered_ct = len(st.session_state.monitor_triggered)
        st.markdown(f"""
        <div style='background:#eaf4ee;border:1px solid #a8d5b8;border-radius:8px;
                    padding:0.75rem;margin-bottom:0.75rem;font-size:0.75rem;color:#2d6a4f;'>
          <div style='font-weight:700;margin-bottom:6px;'>🔔 監控中：{mon_ticker}</div>
          {level_lines}
          <div style='margin-top:6px;color:#6b6560;'>已觸發 {triggered_ct} 個提醒</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style='margin-top:1.5rem;font-size:0.62rem;color:#9e9890;line-height:1.7;'>
    ⚠️ 本平台僅供教育研究用途<br>不構成任何投資建議<br>交易有風險，請自行承擔
    </div>
    """, unsafe_allow_html=True)


# ─── HELPERS ────────────────────────────────────────────────────────────────────
def _color_cls(val):
    sv = str(val)
    if any(k in sv for k in ("多頭","突破","吸籌","放量","低位","看多","看漲")): return "bull"
    if any(k in sv for k in ("空頭","派發","高位","跌破","出貨","看空","看跌")): return "bear"
    return ""

def _info_row(key, val, cls=""):
    return (f"<div class='info-row'>"
            f"<span class='info-key'>{key}</span>"
            f"<span class='info-val {cls}'>{val}</span>"
            f"</div>")

def _score_bar(label, val, color):
    return (f"<div class='score-wrap'>"
            f"<div class='score-label-row'><span>{label}</span>"
            f"<span class='score-num' style='color:{color};'>{val}</span></div>"
            f"<div class='score-bar-bg'>"
            f"<div class='score-bar-fill' style='width:{val}%;background:{color};'></div>"
            f"</div></div>")


# ─── MAIN ANALYSIS ───────────────────────────────────────────────────────────────
def run_analysis(ticker, interval, bar_count, tg_token, tg_chat_id):

    with st.spinner("📡 正在獲取市場數據..."):
        df = fetch_ohlcv(ticker, interval, bar_count)

    if df is None or len(df) < 20:
        st.error(f"❌ 無法獲取 {ticker} 的數據，請確認代號是否正確")
        return

    with st.spinner("🧠 分析市場結構中..."):
        patterns        = detect_all_patterns(df)
        market_struct   = analyze_market_structure(df)
        volume_analysis = analyze_volume(df)
        sr_levels       = find_support_resistance(df)
        smart_money     = analyze_smart_money(df, volume_analysis)
        signals         = generate_signals(df, patterns, market_struct, volume_analysis, sr_levels)
        scores          = compute_scores(market_struct, volume_analysis, smart_money, signals)
        ai_text         = generate_ai_analysis(
            ticker, df, patterns, market_struct,
            volume_analysis, sr_levels, smart_money, signals, scores
        )

    # ── 數據快照 ─────────────────────────────────────────────────────────────
    latest    = df.iloc[-1]
    prev      = df.iloc[-2]
    price_chg = latest['Close'] - prev['Close']
    price_pct = price_chg / prev['Close'] * 100
    vol_avg   = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = latest['Volume'] / vol_avg if vol_avg > 0 else 1.0
    trend     = market_struct.get('trend', '橫盤整理')
    sig       = signals.get('primary', 'NEUTRAL')
    overall   = scores.get('overall_rating', '中性 ⟷')

    chg_cls   = "bull" if price_chg >= 0 else "bear"
    chg_icon  = "▲" if price_chg >= 0 else "▼"
    trend_cls = "bull" if "多頭" in trend else ("bear" if "空頭" in trend else "gold")
    sig_icon  = "🟢" if sig == "BUY" else ("🔴" if sig == "SELL" else "🟡")

    # ─── HEADER ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='display:flex;align-items:baseline;gap:12px;padding:0.4rem 0 1rem;'>
      <span style='font-family:IBM Plex Mono,monospace;font-size:1.7rem;font-weight:700;
                   color:#1a1a1a;'>{ticker}</span>
      <span style='font-size:0.72rem;color:#9e9890;letter-spacing:0.06em;'>{interval_label} &nbsp;·&nbsp; SMC + Price Action</span>
      <span style='margin-left:auto;font-size:0.68rem;color:#b8b2aa;font-family:IBM Plex Mono,monospace;'>
        {datetime.now().strftime('%Y-%m-%d  %H:%M')}
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ─── METRIC CARDS ────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>最新收盤</div>
          <div class='metric-value'>${latest['Close']:.2f}</div>
          <div class='metric-sub {chg_cls}'>{chg_icon} {abs(price_chg):.2f} ({abs(price_pct):.2f}%)</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>趨勢結構</div>
          <div class='metric-value {trend_cls}' style='font-size:1.1rem;padding-top:6px;'>{trend}</div>
          <div class='metric-sub' style='color:#9e9890;'>{market_struct.get('swing_desc','')}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        vol_cls = "bull" if vol_ratio > 1.5 else ("bear" if vol_ratio < 0.5 else "gold")
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>成交量比率</div>
          <div class='metric-value {vol_cls}'>{vol_ratio:.1f}x</div>
          <div class='metric-sub' style='color:#9e9890;'>{volume_analysis.get('vol_signal','')}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        sig_cls = "bull" if sig == "BUY" else ("bear" if sig == "SELL" else "gold")
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>主要訊號</div>
          <div class='metric-value {sig_cls}' style='font-size:1.4rem;padding-top:4px;'>
            {sig_icon} {sig}
          </div>
          <div class='metric-sub' style='color:#9e9890;'>{signals.get('strength','')}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        r_col = "#3d8c5f" if "看多" in overall else ("#c0392b" if "看空" in overall else "#b07d2e")
        st.markdown(f"""<div class='metric-card'>
          <div class='metric-label'>綜合評級</div>
          <div class='metric-value' style='font-size:1rem;color:{r_col};padding-top:8px;'>{overall}</div>
          <div class='metric-sub' style='color:#9e9890;'>信心 {scores.get('confidence',0)}%</div>
        </div>""", unsafe_allow_html=True)

    # ─── K LINE CHART ─────────────────────────────────────────────────────────
    st.markdown("<div class='section-heading'>📈 K線圖表 · 市場結構 · 訊號</div>", unsafe_allow_html=True)
    fig = build_chart(df, ticker, interval, sr_levels, signals, market_struct, patterns)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displaylogo": False})

    # ─── ANALYSIS SECTION ────────────────────────────────────────────────────
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown("<div class='section-heading'>🧠 AI 綜合分析</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='analysis-block'>{ai_text}</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-heading'>📐 市場結構詳情</div>", unsafe_allow_html=True)
        st.markdown(f"""<div class='white-card'>
          {_info_row("趨勢方向",  trend,                                    _color_cls(trend))}
          {_info_row("擺動結構",  market_struct.get('swing_desc','-'),      _color_cls(market_struct.get('swing_desc','')))}
          {_info_row("趨勢強度",  f"{market_struct.get('trend_strength',0)}/100")}
          {_info_row("市場狀態",  market_struct.get('market_state','-'))}
          {_info_row("結構突破",  market_struct.get('structure_break','-'), _color_cls(market_struct.get('structure_break','')))}
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='section-heading'>💰 Smart Money 主力行為</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='analysis-block' style='border-left-color:#b07d2e;'>{smart_money.get('description','')}</div>",
                    unsafe_allow_html=True)
        st.markdown(f"""<div class='white-card'>
          {_info_row("主力行為",   smart_money.get('behavior','-'),          _color_cls(smart_money.get('behavior','')))}
          {_info_row("吸籌概率",   f"{smart_money.get('accumulation_prob',0)}%")}
          {_info_row("派發風險",   f"{smart_money.get('distribution_risk',0)}%")}
          {_info_row("流動性獵殺", smart_money.get('liquidity_grab','-'))}
          {_info_row("假突破風險", smart_money.get('fakeout_risk','-'))}
        </div>""", unsafe_allow_html=True)

    with col_r:
        # Scores
        st.markdown("<div class='section-heading'>📊 評分系統</div>", unsafe_allow_html=True)
        r_bg  = "#eaf4ee" if "看多" in overall else ("#fdecea" if "看空" in overall else "#fdf6e3")
        score_html = (
            _score_bar("趨勢強度",     scores.get('trend_strength',0),     "#4a7c6f") +
            _score_bar("主力吸籌概率", scores.get('accumulation_score',0), "#3d8c5f") +
            _score_bar("主力出貨風險", scores.get('distribution_score',0), "#c0392b") +
            _score_bar("突破成功率",   scores.get('breakout_score',0),     "#b07d2e") +
            _score_bar("假突破風險",   scores.get('fakeout_score',0),      "#c0706a") +
            f"<div style='text-align:center;margin-top:1.1rem;'>"
            f"<div class='rating-badge' style='background:{r_bg};"
            f"border:1.5px solid {r_col};color:{r_col};'>{overall}</div></div>"
        )
        st.markdown(f"<div class='white-card'>{score_html}</div>", unsafe_allow_html=True)

        # Trade setup
        st.markdown("<div class='section-heading'>📋 交易建議</div>", unsafe_allow_html=True)
        trade = signals.get('trade_setup', {})
        st.markdown(f"""<div class='white-card'>
          {_info_row("短線方向", trade.get('short_term','-'),           _color_cls(trade.get('short_term','')))}
          {_info_row("中線方向", trade.get('mid_term','-'),             _color_cls(trade.get('mid_term','')))}
          {_info_row("關鍵支撐", f"${trade.get('key_support',0):.2f}")}
          {_info_row("關鍵阻力", f"${trade.get('key_resistance',0):.2f}")}
          {_info_row("突破價位", f"${trade.get('breakout_level',0):.2f}")}
          {_info_row("止損位",   f"${trade.get('stop_loss',0):.2f}",   "bear")}
          {_info_row("風報比",   trade.get('rrr','-'))}
        </div>""", unsafe_allow_html=True)

        # ── 一鍵監控按鈕 ─────────────────────────────────────────────────────
        _ks  = trade.get('key_support', 0)
        _kr  = trade.get('key_resistance', 0)
        _bp  = trade.get('breakout_level', 0)
        _sl  = trade.get('stop_loss', 0)

        # 監控狀態顯示
        monitor_is_on = (st.session_state.monitor_active and
                         st.session_state.monitor_ticker == ticker)

        if monitor_is_on:
            st.markdown(f"""
            <div style='background:#eaf4ee;border:1.5px solid #3d8c5f;border-radius:8px;
                        padding:0.7rem 1rem;margin-bottom:0.6rem;font-size:0.8rem;'>
              <span style='color:#3d8c5f;font-weight:700;'>🔔 價位監控中</span>
              <span style='color:#6b6560;margin-left:8px;font-family:IBM Plex Mono,monospace;'>
                {ticker} · 支撐 ${_ks:.2f} / 阻力 ${_kr:.2f} / 突破 ${_bp:.2f} / 止損 ${_sl:.2f}
              </span>
            </div>""", unsafe_allow_html=True)
            if st.button("⏹ 停止監控", use_container_width=True, key="stop_monitor"):
                st.session_state.monitor_active    = False
                st.session_state.monitor_levels    = {}
                st.session_state.monitor_ticker    = ""
                st.session_state.monitor_triggered = set()
                st.rerun()
        else:
            btn_disabled = not (tg_token and tg_chat_id)
            if st.button(
                "🔔 一鍵監控價位" + ("（請先填 Telegram）" if btn_disabled else ""),
                use_container_width=True,
                key="start_monitor",
                disabled=btn_disabled,
            ):
                st.session_state.monitor_active  = True
                st.session_state.monitor_ticker  = ticker
                st.session_state.monitor_triggered = set()
                st.session_state.monitor_levels  = {
                    "關鍵支撐":  {"price": _ks,  "direction": "below", "color": "🟢"},
                    "關鍵阻力":  {"price": _kr,  "direction": "above", "color": "🔴"},
                    "突破價位":  {"price": _bp,  "direction": "above", "color": "🚀"},
                    "止損位":    {"price": _sl,  "direction": "below", "color": "🛑"},
                }
                st.success(f"✅ 已啟動監控！觸及價位將即時發送 Telegram 通知")
                st.rerun()

        # Patterns
        st.markdown("<div class='section-heading'>🕯️ 辨識K線型態</div>", unsafe_allow_html=True)
        pills = ""
        for p in patterns.get('detected', []):
            cls = ("pill-bull" if p['bias'] == 'bull'
                   else "pill-bear" if p['bias'] == 'bear' else "pill-neutral")
            pills += f"<span class='pattern-pill {cls}'>{p['name']}</span>"
        if not pills:
            pills = "<span style='color:#9e9890;font-size:0.8rem;'>未偵測到明顯型態</span>"
        st.markdown(f"<div class='white-card' style='line-height:2.2;'>{pills}</div>",
                    unsafe_allow_html=True)

        # Volume
        st.markdown("<div class='section-heading'>📦 成交量分析（最新5根）</div>", unsafe_allow_html=True)
        r5 = volume_analysis.get('recent5_ratio', 1.0)
        vbias = volume_analysis.get('vol_bias', '')
        vdiv  = volume_analysis.get('vol_divergence', '') or '無'
        st.markdown(f"""<div class='white-card'>
          {_info_row("最新1根訊號", volume_analysis.get('vol_signal','-'),      _color_cls(volume_analysis.get('vol_signal','')))}
          {_info_row("最新1根量比", f"{vol_ratio:.1f}x 均量")}
          {_info_row("近5根量比",   f"{r5:.1f}x · {vbias}",
                     "bull" if "多頭" in vbias else ("bear" if "空頭" in vbias else ""))}
          {_info_row("成交量解讀", volume_analysis.get('interpretation','-'))}
          {_info_row("主力動向",   volume_analysis.get('smart_vol','-'),        _color_cls(volume_analysis.get('smart_vol','')))}
          {_info_row("量價背離",   vdiv)}
        </div>""", unsafe_allow_html=True)

    # ─── BACKTEST ─────────────────────────────────────────────────────────────
    st.markdown("<div class='section-heading'>📉 回測系統</div>", unsafe_allow_html=True)
    bt = run_backtest(df, signals.get('signal_history', []))
    bt_cols = st.columns(5)
    bt_data = [
        ("勝率",     f"{bt.get('win_rate',0):.1f}%",    bt.get('win_rate',0) > 50),
        ("盈虧比",   f"{bt.get('profit_factor',0):.2f}", bt.get('profit_factor',0) > 1.5),
        ("最大回撤", f"{bt.get('max_dd',0):.1f}%",       bt.get('max_dd',0) < 15),
        ("交易次數", str(bt.get('total_trades',0)),       True),
        ("淨收益率", f"{bt.get('net_return',0):.1f}%",   bt.get('net_return',0) > 0),
    ]
    for col, (label, val, good) in zip(bt_cols, bt_data):
        color = "#3d8c5f" if good else "#c0392b"
        with col:
            st.markdown(f"""<div class='metric-card' style='text-align:center;'>
              <div class='metric-label'>{label}</div>
              <div class='metric-value' style='color:{color};font-size:1.4rem;'>{val}</div>
            </div>""", unsafe_allow_html=True)

    # Equity curve（附件風格：白底，柔和線條）
    if bt.get('equity_curve') and len(bt['equity_curve']) > 2:
        eq = bt['equity_curve']
        eq_color = "#3d8c5f" if eq[-1] >= eq[0] else "#c0392b"
        eq_fill  = "rgba(61,140,95,0.08)" if eq[-1] >= eq[0] else "rgba(192,57,43,0.08)"
        eq_fig = go.Figure()
        eq_fig.add_trace(go.Scatter(
            y=eq, mode='lines',
            line=dict(color=eq_color, width=2),
            fill='tozeroy', fillcolor=eq_fill,
        ))
        eq_fig.update_layout(
            plot_bgcolor='#ffffff',
            paper_bgcolor='#f9f7f4',
            height=180,
            margin=dict(l=50, r=20, t=32, b=30),
            title=dict(text='Equity Curve', font=dict(family='Noto Sans TC', size=12, color='#6b6560'), x=0.01),
            xaxis=dict(showgrid=False, color='#b8b2aa', tickfont=dict(size=9, color='#9e9890')),
            yaxis=dict(gridcolor='#ede9e3', color='#b8b2aa', tickfont=dict(size=9, color='#9e9890')),
            font=dict(family='IBM Plex Mono', color='#9e9890', size=10),
            showlegend=False,
        )
        st.plotly_chart(eq_fig, use_container_width=True)

    # ─── 儲存 Telegram 憑據到 session state（供背景監控使用）────────────────
    if tg_token:
        st.session_state["_tg_token"] = tg_token
    if tg_chat_id:
        st.session_state["_tg_chat"] = tg_chat_id

    # ─── TELEGRAM ────────────────────────────────────────────────────────────
    if tg_token and tg_chat_id and sig in ('BUY', 'SELL'):
        msg_hash = hashlib.md5(
            f"{ticker}{interval}{sig}{datetime.now().strftime('%Y%m%d%H')}".encode()
        ).hexdigest()
        if msg_hash not in st.session_state.alert_sent_hash:
            detected_names = ', '.join([p['name'] for p in patterns.get('detected', [])[:3]])
            tg_msg = (
                f"🚨 *{ticker} 交易訊號*\n\n"
                f"訊號：{'🟢 BUY 做多' if sig == 'BUY' else '🔴 SELL 做空'}\n"
                f"趨勢：{trend}\n"
                f"型態：{detected_names or '無'}\n"
                f"成交量：{volume_analysis.get('vol_signal','-')}\n"
                f"評級：{overall}\n\n"
                f"{ai_text[:300]}..."
            )
            if send_telegram_alert(tg_token, tg_chat_id, tg_msg):
                st.session_state.alert_sent_hash.add(msg_hash)
                st.success("📱 Telegram 通知已發送")

    st.session_state.last_analysis = {"ticker": ticker, "time": datetime.now()}


# ─── 背景價位監控（每次 rerun 都執行）────────────────────────────────────────────
def _run_price_monitor():
    """檢查當前價格是否觸及監控價位，觸及則發 Telegram"""
    if not st.session_state.monitor_active:
        return
    if not st.session_state.monitor_levels:
        return

    ticker_m = st.session_state.monitor_ticker
    tg_t = st.session_state.get("_tg_token", "")
    tg_c = st.session_state.get("_tg_chat", "")
    if not tg_t or not tg_c:
        return

    try:
        import yfinance as yf
        tk   = yf.Ticker(ticker_m)
        info = tk.fast_info
        cur  = float(info.last_price)
    except Exception:
        return

    triggered_now = []
    for label, cfg in st.session_state.monitor_levels.items():
        level     = cfg["price"]
        direction = cfg["direction"]   # "above" or "below"
        icon      = cfg["color"]
        key       = f"{label}_{level:.2f}"

        if key in st.session_state.monitor_triggered:
            continue   # 已通知過，不重複

        hit = (direction == "above" and cur >= level) or               (direction == "below" and cur <= level)

        if hit:
            st.session_state.monitor_triggered.add(key)
            triggered_now.append((label, level, cur, icon, direction))

    if triggered_now:
        from analysis.telegram_bot import send_telegram_alert
        for label, level, cur_price, icon, direction in triggered_now:
            arrow = "突破上方 ↑" if direction == "above" else "跌破下方 ↓"
            msg = (
                f"{icon} *{ticker_m} 價位觸及提醒*\n\n"
                f"觸發：*{label}*\n"
                f"監控價：${level:.2f}\n"
                f"當前價：${cur_price:.2f}\n"
                f"方向：{arrow}\n"
                f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_telegram_alert(tg_t, tg_c, msg)

        # 在頁面顯示觸發提示
        for label, level, cur_price, icon, direction in triggered_now:
            st.toast(f"{icon} {ticker_m} {label} ${level:.2f} 已觸及！Telegram 已發送", icon="🔔")

_run_price_monitor()

# ─── ENTRY POINT ────────────────────────────────────────────────────────────────
if analyze_btn:
    run_analysis(ticker_input, interval, bar_count, tg_token, tg_chat_id)

elif refresh_sec > 0 and st.session_state.last_analysis:
    time.sleep(refresh_sec)
    run_analysis(ticker_input, interval, bar_count, tg_token, tg_chat_id)
    st.rerun()

elif st.session_state.monitor_active:
    # 監控模式：即使沒有自動刷新，也每 30 秒輪詢一次價格
    time.sleep(30)
    st.rerun()

else:
    st.markdown("""
    <div style='text-align:center;padding:6rem 2rem;color:#b8b2aa;'>
      <div style='font-size:2.5rem;margin-bottom:1rem;color:#ccc8be;'>◈</div>
      <div style='font-family:Noto Sans TC,sans-serif;font-size:1rem;color:#9e9890;'>
        在左側輸入股票代號，點擊「開始分析」
      </div>
      <div style='font-size:0.75rem;margin-top:0.5rem;color:#b8b2aa;'>
        支援美股 · ETF · 7 個時間週期
      </div>
    </div>
    """, unsafe_allow_html=True)
