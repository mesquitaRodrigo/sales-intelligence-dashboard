"""pages/overview.py — Visão Geral"""

import sys as _sys, os as _os, importlib.util as _ilu
# Caminho absoluto robusto: funciona com importlib, execfile e Streamlit
_THIS = _os.path.abspath(globals().get('__file__', '') or __spec__.origin)
_BASE = _os.path.dirname(_os.path.dirname(_THIS))
if _BASE not in _sys.path:
    _sys.path.insert(0, _BASE)

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import db

# Paleta
C_PRIMARY  = "#6366f1"
C_GREEN    = "#4ade80"
C_RED      = "#f87171"
C_YELLOW   = "#fbbf24"
C_BG       = "#1a1d27"
C_BORDER   = "#2a2d3e"
C_TEXT     = "#e8eaf0"
C_MUTED    = "#8b92a5"

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C_TEXT, family="Inter"),
    xaxis=dict(gridcolor=C_BORDER, showline=False, tickfont=dict(color=C_MUTED, size=11)),
    yaxis=dict(gridcolor=C_BORDER, showline=False, tickfont=dict(color=C_MUTED, size=11)),
    margin=dict(l=0, r=0, t=32, b=0),
)


def fmt_brl(v): return f"R$ {v:,.0f}".replace(",", ".")
def fmt_pct(v): return f"{v:.1f}%"


def kpi_card(label, value, delta_html="", value_class="kpi-value"):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="{value_class}">{value}</div>
        {f'<div class="kpi-delta">{delta_html}</div>' if delta_html else ''}
    </div>"""


def render():
    st.markdown("## Visão Geral")
    st.markdown('<p style="color:#8b92a5;margin-top:-12px;">Performance acumulada · 18 meses</p>',
                unsafe_allow_html=True)

    # ── KPIs do mês atual ──────────────────────────────────────────────────
    cur = db.kpis_current_month()
    tgt_pct = cur["target_pct"] or 0
    tgt_color = C_GREEN if tgt_pct >= 100 else (C_YELLOW if tgt_pct >= 85 else C_RED)
    tgt_icon  = "✅" if tgt_pct >= 100 else ("⚠️" if tgt_pct >= 85 else "🔴")

    c1, c2, c3, c4, c5 = st.columns(5)
    cols = [c1, c2, c3, c4, c5]
    cards = [
        ("Faturamento (mês)", fmt_brl(cur["revenue"]),
         f'<span style="color:{tgt_color}">{tgt_icon} {tgt_pct:.0f}% da meta</span>', "kpi-value-sm"),
        ("Lucro Bruto (mês)", fmt_brl(cur["gross_profit"]), "", "kpi-value-sm"),
        ("Margem Bruta", fmt_pct(cur["margin_pct"]),
         f'<span style="color:{C_MUTED}">vs meta 30%</span>' if cur["margin_pct"] < 30
         else f'<span style="color:{C_GREEN}">✓ acima de 30%</span>', "kpi-value"),
        ("Ticket Médio", fmt_brl(cur["avg_ticket"]), "", "kpi-value"),
        ("Clientes Ativos", str(int(cur["active_customers"])), "", "kpi-value"),
    ]
    for col, (lbl, val, delta, val_class) in zip(cols, cards):
        with col:
            st.markdown(kpi_card(lbl, val, delta, val_class), unsafe_allow_html=True)

    st.markdown("")

    # ── Faturamento vs Meta ────────────────────────────────────────────────
    st.markdown('<div class="section-title">Faturamento Mensal vs Meta</div>', unsafe_allow_html=True)
    df = db.monthly_revenue_vs_target()
    df["label"] = df["year_month"].str[-2:] + "/" + df["year_month"].str[:4]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["label"], y=df["revenue"],
        name="Faturamento",
        marker_color=[C_GREEN if r >= t else C_RED
                      for r, t in zip(df["revenue"], df["target_brl"])],
        opacity=0.85,
    ))
    fig.add_trace(go.Scatter(
        x=df["label"], y=df["target_brl"],
        name="Meta", mode="lines+markers",
        line=dict(color=C_YELLOW, width=2, dash="dot"),
        marker=dict(size=5),
    ))
    fig.add_trace(go.Scatter(
        x=df["label"], y=df["gross_profit"],
        name="Lucro Bruto", mode="lines",
        line=dict(color=C_PRIMARY, width=2),
    ))
    fig.update_layout(
        **PLOT_LAYOUT,
        height=340,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=12, color=C_TEXT)),
        yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
        hovermode="x unified",
    )
    st.plotly_chart(fig, width='stretch')

    # ── Margem e Ticket Médio ──────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Margem Bruta % por Mês</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df["label"], y=df["margin_pct"],
            fill="tozeroy",
            line=dict(color=C_PRIMARY, width=2),
            fillcolor="rgba(99,102,241,0.15)",
            name="Margem %",
        ))
        fig2.add_hline(y=30, line_dash="dot", line_color=C_YELLOW,
                       annotation_text="Target 30%", annotation_font_color=C_YELLOW)
        fig2.update_layout(**PLOT_LAYOUT, height=240,
                           yaxis_ticksuffix="%", showlegend=False)
        st.plotly_chart(fig2, width='stretch')

    with col_r:
        st.markdown('<div class="section-title">Ticket Médio por Mês</div>', unsafe_allow_html=True)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df["label"], y=df["avg_ticket"],
            mode="lines+markers",
            line=dict(color=C_GREEN, width=2),
            marker=dict(size=5, color=C_GREEN),
            name="Ticket Médio",
        ))
        fig3.update_layout(**PLOT_LAYOUT, height=240,
                           yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
                           showlegend=False)
        st.plotly_chart(fig3, width='stretch')

    # ── Faturamento por Segmento ────────────────────────────────────────────
    st.markdown('<div class="section-title">Faturamento por Segmento</div>', unsafe_allow_html=True)
    seg_df = db.revenue_by_segment_monthly()
    fig4 = px.area(
        seg_df, x="year_month", y="revenue", color="segment",
        color_discrete_sequence=["#6366f1", "#4ade80", "#fbbf24", "#f87171"],
    )
    fig4.update_layout(
        **PLOT_LAYOUT, height=280,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=12, color=C_TEXT)),
        yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
        hovermode="x unified",
    )
    st.plotly_chart(fig4, width='stretch')