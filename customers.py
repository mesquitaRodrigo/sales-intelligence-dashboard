"""pages/customers.py — Análise de Clientes"""

import sys as _sys, os as _os, importlib.util as _ilu
# Caminho absoluto robusto: funciona com importlib, execfile e Streamlit
_THIS = _os.path.abspath(globals().get('__file__', '') or __spec__.origin)
_BASE = _os.path.dirname(_os.path.dirname(_THIS))
if _BASE not in _sys.path:
    _sys.path.insert(0, _BASE)

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import db

C_PRIMARY = "#6366f1"
C_GREEN   = "#4ade80"
C_RED     = "#f87171"
C_YELLOW  = "#fbbf24"
C_BORDER  = "#2a2d3e"
C_TEXT    = "#e8eaf0"
C_MUTED   = "#8b92a5"

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C_TEXT, family="Inter"),
    margin=dict(l=0, r=0, t=32, b=0),
)


def render():
    st.markdown("## Análise de Clientes")
    st.markdown('<p style="color:#8b92a5;margin-top:-12px;">Concentração, segmentos e risco de churn</p>',
                unsafe_allow_html=True)

    cust  = db.customer_performance(50)
    seg   = db.segment_summary()
    churn = db.churn_risk()

    # ── KPIs de clientes ────────────────────────────────────────────────────
    top5_pct = cust.head(5)["revenue"].sum() / cust["revenue"].sum() * 100
    avg_disc  = cust["avg_discount_pct"].mean()

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("Total de Clientes", str(len(cust))),
        ("Concentração Top 5", f"{top5_pct:.1f}%"),
        ("Desc. Médio Geral", f"{avg_disc:.1f}%"),
        ("Risco de Churn", str(len(churn))),
    ]
    for col, (lbl, val) in zip([c1,c2,c3,c4], kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{lbl}</div>
                <div class="kpi-value">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Segmentos ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Performance por Segmento</div>',
                unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2])

    with col_l:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Faturamento",
            x=seg["segment"], y=seg["revenue"],
            marker_color=C_PRIMARY, opacity=0.85,
        ))
        fig.add_trace(go.Bar(
            name="Lucro Bruto",
            x=seg["segment"], y=seg["gross_profit"],
            marker_color=C_GREEN, opacity=0.9,
        ))
        fig.update_layout(
            **PLOT_LAYOUT, height=280, barmode="group",
            xaxis=dict(tickfont=dict(color=C_TEXT, size=12)),
            yaxis=dict(gridcolor=C_BORDER, tickprefix="R$ ", tickformat=",.0f",
                       tickfont=dict(color=C_MUTED, size=11)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                        font=dict(size=12, color=C_TEXT)),
        )
        st.plotly_chart(fig, width='stretch')

    with col_r:
        fig2 = go.Figure(go.Bar(
            y=seg["segment"],
            x=seg["margin_pct"],
            orientation="h",
            marker_color=[C_RED if m < 15 else (C_YELLOW if m < 25 else C_GREEN)
                          for m in seg["margin_pct"]],
            text=[f"{m:.1f}%" for m in seg["margin_pct"]],
            textposition="outside",
            textfont=dict(color=C_TEXT, size=12),
        ))
        fig2.update_layout(
            **PLOT_LAYOUT, height=280,
            title=dict(text="Margem % por Segmento", font=dict(size=13, color=C_MUTED)),
            xaxis_ticksuffix="%",
            xaxis=dict(gridcolor=C_BORDER, tickfont=dict(color=C_MUTED, size=11)),
            yaxis=dict(tickfont=dict(color=C_TEXT, size=12)),
        )
        st.plotly_chart(fig2, width='stretch')

    # ── Curva de Pareto ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Curva de Pareto · Concentração de Receita</div>',
                unsafe_allow_html=True)
    st.caption("Quantos clientes respondem por 80% do faturamento?")

    cust_s = cust.sort_values("revenue", ascending=False).reset_index(drop=True)
    cust_s["cum_revenue_pct"] = cust_s["revenue"].cumsum() / cust_s["revenue"].sum() * 100
    cust_s["rank"] = range(1, len(cust_s)+1)

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=cust_s["rank"], y=cust_s["revenue"],
        name="Faturamento",
        marker_color=C_PRIMARY, opacity=0.6,
    ))
    fig3.add_trace(go.Scatter(
        x=cust_s["rank"], y=cust_s["cum_revenue_pct"],
        name="Acumulado %", mode="lines",
        line=dict(color=C_YELLOW, width=2),
        yaxis="y2",
    ))
    fig3.add_hline(y=80, line_dash="dot", line_color=C_RED,
                   annotation_text="80%", annotation_font_color=C_RED,
                   yref="y2")
    fig3.update_layout(
        **PLOT_LAYOUT, height=300,
        yaxis=dict(gridcolor=C_BORDER, tickprefix="R$ ", tickformat=",.0f",
                   tickfont=dict(color=C_MUTED, size=11)),
        yaxis2=dict(overlaying="y", side="right", ticksuffix="%",
                    range=[0, 110], showgrid=False,
                    tickfont=dict(color=C_YELLOW, size=11)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=12, color=C_TEXT)),
        hovermode="x unified",
        xaxis=dict(title="Rank de clientes", gridcolor=C_BORDER,
                   tickfont=dict(color=C_MUTED, size=11)),
    )
    st.plotly_chart(fig3, width='stretch')

    # ── Risco de Churn ──────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🔴 Risco de Churn · Sem compra há +60 dias</div>',
                unsafe_allow_html=True)

    if churn.empty:
        st.success("Nenhum cliente em risco de churn identificado.")
    else:
        total_at_risk = churn["revenue"].sum()
        st.warning(
            f"**{len(churn)} clientes** sem compra há mais de 60 dias · "
            f"Receita em risco: **R$ {total_at_risk:,.0f}**"
        )
        display = churn.copy()
        display["revenue"]      = display["revenue"].map("R$ {:,.0f}".format)
        display["days_since"]   = display["days_since"].map("{} dias".format)
        display = display.rename(columns={
            "customer_name": "Cliente", "segment": "Segmento",
            "revenue": "Receita Total", "last_purchase": "Última Compra",
            "days_since": "Inativo há",
        })
        st.dataframe(display[["Cliente","Segmento","Receita Total","Última Compra","Inativo há"]],
                     width='stretch', hide_index=True)

    # ── Top clientes ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Top 20 Clientes por Faturamento</div>',
                unsafe_allow_html=True)
    display2 = cust.head(20).copy()
    display2["revenue"]      = display2["revenue"].map("R$ {:,.0f}".format)
    display2["gross_profit"] = display2["gross_profit"].map("R$ {:,.0f}".format)
    display2["margin_pct"]   = display2["margin_pct"].map("{:.1f}%".format)
    display2["avg_discount_pct"] = display2["avg_discount_pct"].map("{:.1f}%".format)
    display2 = display2.rename(columns={
        "customer_name": "Cliente", "segment": "Segmento", "state": "UF",
        "num_orders": "Pedidos", "revenue": "Faturamento",
        "gross_profit": "Lucro Bruto", "margin_pct": "Margem",
        "avg_discount_pct": "Desc. Médio", "last_purchase": "Última Compra",
    })
    st.dataframe(
        display2[["Cliente","Segmento","UF","Pedidos","Faturamento","Lucro Bruto","Margem","Desc. Médio"]],
        width='stretch', hide_index=True,
    )