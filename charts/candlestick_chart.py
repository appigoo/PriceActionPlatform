"""Professional Dark Theme Candlestick Chart with SMC annotations"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd


def build_chart(df, ticker, interval, sr_levels, signals, market_struct, patterns) -> go.Figure:
    dates = df.index
    opens = df['Open'].values
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    vols = df['Volume'].values
    n = len(df)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.72, 0.28],
    )

    # ── CANDLESTICKS ────────────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=dates,
        open=opens, high=highs, low=lows, close=closes,
        name="K線",
        increasing_line_color='#00c896',
        decreasing_line_color='#ff4560',
        increasing_fillcolor='#00c896',
        decreasing_fillcolor='#ff4560',
        line_width=1,
    ), row=1, col=1)

    # ── EMAs ────────────────────────────────────────────────────────────────
    ema20 = market_struct.get('ema20')
    ema50 = market_struct.get('ema50')
    if ema20 is not None:
        fig.add_trace(go.Scatter(
            x=dates, y=ema20, name="EMA20",
            line=dict(color='#0099ff', width=1.5, dash='dot'),
            opacity=0.8,
        ), row=1, col=1)
    if ema50 is not None:
        fig.add_trace(go.Scatter(
            x=dates, y=ema50, name="EMA50",
            line=dict(color='#f5a623', width=1.5, dash='dot'),
            opacity=0.8,
        ), row=1, col=1)

    # ── SUPPORT LEVELS ───────────────────────────────────────────────────────
    supports = sr_levels.get('supports', [])
    for i, s in enumerate(supports[:3]):
        fig.add_hline(
            y=s, row=1, col=1,
            line=dict(color='#00c896', width=1, dash='dash'),
            annotation_text=f"支撐 ${s:.2f}" if i == 0 else f"S${s:.2f}",
            annotation_position="left",
            annotation_font=dict(color='#00c896', size=10),
            opacity=0.7,
        )

    # ── RESISTANCE LEVELS ────────────────────────────────────────────────────
    resistances = sr_levels.get('resistances', [])
    for i, r in enumerate(resistances[:3]):
        fig.add_hline(
            y=r, row=1, col=1,
            line=dict(color='#ff4560', width=1, dash='dash'),
            annotation_text=f"阻力 ${r:.2f}" if i == 0 else f"R${r:.2f}",
            annotation_position="right",
            annotation_font=dict(color='#ff4560', size=10),
            opacity=0.7,
        )

    # ── DEMAND ZONES ─────────────────────────────────────────────────────────
    for (low_z, high_z) in sr_levels.get('demand_zones', [])[:2]:
        fig.add_hrect(
            y0=low_z, y1=high_z, row=1, col=1,
            fillcolor="rgba(0,200,150,0.07)",
            line_width=0,
        )

    # ── SUPPLY ZONES ─────────────────────────────────────────────────────────
    for (low_z, high_z) in sr_levels.get('supply_zones', [])[:2]:
        fig.add_hrect(
            y0=low_z, y1=high_z, row=1, col=1,
            fillcolor="rgba(255,69,96,0.07)",
            line_width=0,
        )

    # ── SWING HIGHS / LOWS ────────────────────────────────────────────────────
    swing_highs = market_struct.get('swing_highs', [])
    swing_lows = market_struct.get('swing_lows', [])
    if swing_highs:
        sh_x = [dates[min(i, n-1)] for i, _ in swing_highs]
        sh_y = [v for _, v in swing_highs]
        fig.add_trace(go.Scatter(
            x=sh_x, y=sh_y, mode='markers',
            marker=dict(symbol='triangle-down', color='#ff4560', size=8),
            name='Swing High', showlegend=False,
        ), row=1, col=1)
    if swing_lows:
        sl_x = [dates[min(i, n-1)] for i, _ in swing_lows]
        sl_y = [v for _, v in swing_lows]
        fig.add_trace(go.Scatter(
            x=sl_x, y=sl_y, mode='markers',
            marker=dict(symbol='triangle-up', color='#00c896', size=8),
            name='Swing Low', showlegend=False,
        ), row=1, col=1)

    # ── BUY / SELL ARROWS ────────────────────────────────────────────────────
    primary = signals.get('primary', 'NEUTRAL')
    if primary == 'BUY':
        fig.add_trace(go.Scatter(
            x=[dates[-1]], y=[lows[-1] * 0.995],
            mode='markers+text',
            marker=dict(symbol='triangle-up', color='#00ff88', size=20, line=dict(width=2, color='#00c896')),
            text=["▲ BUY"],
            textposition="bottom center",
            textfont=dict(color='#00ff88', size=11),
            name='BUY Signal',
        ), row=1, col=1)
    elif primary == 'SELL':
        fig.add_trace(go.Scatter(
            x=[dates[-1]], y=[highs[-1] * 1.005],
            mode='markers+text',
            marker=dict(symbol='triangle-down', color='#ff2244', size=20, line=dict(width=2, color='#ff4560')),
            text=["▼ SELL"],
            textposition="top center",
            textfont=dict(color='#ff2244', size=11),
            name='SELL Signal',
        ), row=1, col=1)

    # ── VOLUME BARS ───────────────────────────────────────────────────────────
    avg_vol = np.mean(vols[-20:]) if n >= 20 else np.mean(vols)
    vol_colors = []
    for i in range(n):
        if closes[i] >= opens[i]:
            vol_colors.append('#00c896' if vols[i] > avg_vol else 'rgba(0,200,150,0.4)')
        else:
            vol_colors.append('#ff4560' if vols[i] > avg_vol else 'rgba(255,69,96,0.4)')

    fig.add_trace(go.Bar(
        x=dates, y=vols,
        name="成交量",
        marker_color=vol_colors,
        opacity=0.85,
    ), row=2, col=1)

    # Volume average line
    fig.add_trace(go.Scatter(
        x=dates, y=[avg_vol] * n,
        name="Vol MA20",
        line=dict(color='#f5a623', width=1, dash='dot'),
        opacity=0.7,
    ), row=2, col=1)

    # ── LAYOUT ───────────────────────────────────────────────────────────────
    trend = market_struct.get('trend', '')
    trend_icon = "📈" if "多頭" in trend else ("📉" if "空頭" in trend else "⟷")

    fig.update_layout(
        title=dict(
            text=f"{ticker} · {interval} · {trend_icon} {trend}",
            font=dict(family="IBM Plex Mono", size=14, color="#e2e8f0"),
            x=0.01,
        ),
        plot_bgcolor='#0d1117',
        paper_bgcolor='#131720',
        height=620,
        margin=dict(l=60, r=80, t=50, b=20),
        font=dict(family="IBM Plex Mono", color="#94a3b8", size=10),
        legend=dict(
            bgcolor='rgba(13,15,20,0.8)',
            bordercolor='#2a3348',
            borderwidth=1,
            font=dict(size=9, color='#94a3b8'),
        ),
        hovermode='x unified',
        xaxis_rangeslider_visible=False,
        dragmode='zoom',
    )

    # Axes styling
    axis_style = dict(
        gridcolor='#1e2535',
        zerolinecolor='#2a3348',
        linecolor='#2a3348',
        tickfont=dict(size=9, color='#94a3b8'),
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    fig.update_yaxes(tickprefix='$', row=1, col=1)

    return fig
