"""pages/products.py — Análise de Produtos"""

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
C_BG      = "#1a1d27"
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
    st.markdown("## Análise de Produtos")
    st.markdown('<p style="color:#8b92a5;margin-top:-12px;">Rentabilidade, volume e mix de vendas</p>',
                unsafe_allow_html=True)

    df   = db.product_performance(20)
    cat  = db.category_summary()
    scat = db.product_margin_scatter()

    # ── Top produtos por faturamento ────────────────────────────────────────
    st.markdown('<div class="section-title">Top 10 Produtos · Faturamento vs Lucro Bruto</div>',
                unsafe_allow_html=True)

    top = df.head(10).sort_values("revenue")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["product_name"], x=top["revenue"],
        name="Faturamento", orientation="h",
        marker_color=C_PRIMARY, opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        y=top["product_name"], x=top["gross_profit"],
        name="Lucro Bruto", orientation="h",
        marker_color=C_GREEN, opacity=0.9,
    ))
    fig.update_layout(
        **PLOT_LAYOUT, height=380,
        barmode="overlay",
        xaxis_tickprefix="R$ ", xaxis_tickformat=",.0f",
        xaxis=dict(gridcolor=C_BORDER, tickfont=dict(color=C_MUTED, size=11)),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=C_TEXT, size=11)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=12, color=C_TEXT)),
    )
    st.plotly_chart(fig, width='stretch')

    # ── Scatter: Faturamento × Margem ──────────────────────────────────────
    st.markdown('<div class="section-title">Mapa de Rentabilidade · Faturamento × Margem</div>',
                unsafe_allow_html=True)
    st.caption("Quadrante ideal: alto faturamento + alta margem (direita e acima da linha)")

    fig2 = px.scatter(
        scat,
        x="revenue", y="margin_pct",
        size="units_sold", color="category",
        hover_name="product_name",
        hover_data={"revenue": ":,.0f", "margin_pct": ":.1f",
                    "units_sold": True, "avg_discount_pct": ":.1f"},
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"revenue": "Faturamento (R$)", "margin_pct": "Margem (%)"},
    )
    fig2.add_hline(y=20, line_dash="dot", line_color=C_YELLOW,
                   annotation_text="Margem mínima 20%",
                   annotation_font_color=C_YELLOW)
    fig2.add_vline(x=scat["revenue"].median(), line_dash="dot", line_color=C_MUTED,
                   annotation_text="Mediana", annotation_font_color=C_MUTED)
    fig2.update_layout(
        **PLOT_LAYOUT, height=400,
        xaxis_tickprefix="R$ ", xaxis_tickformat=",.0f",
        xaxis=dict(gridcolor=C_BORDER, tickfont=dict(color=C_MUTED, size=11)),
        yaxis=dict(gridcolor=C_BORDER, tickfont=dict(color=C_MUTED, size=11),
                   ticksuffix="%"),
        legend=dict(font=dict(size=11, color=C_TEXT)),
    )
    st.plotly_chart(fig2, width='stretch')

    # ── Por categoria ────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-title">Mix de Faturamento por Categoria</div>',
                    unsafe_allow_html=True)
        fig3 = px.pie(
            cat, values="revenue", names="category",
            hole=0.55,
            color_discrete_sequence=["#6366f1","#4ade80","#fbbf24","#f87171",
                                      "#60a5fa","#c084fc","#fb7185","#34d399"],
        )
        fig3.update_traces(textposition="outside", textfont_size=11,
                           textfont_color=C_TEXT)
        fig3.update_layout(
            **PLOT_LAYOUT, height=300,
            legend=dict(font=dict(size=11, color=C_TEXT)),
            showlegend=True,
        )
        st.plotly_chart(fig3, width='stretch')

    with col_r:
        st.markdown('<div class="section-title">Margem % por Categoria</div>',
                    unsafe_allow_html=True)
        cat_s = cat.sort_values("margin_pct")
        colors = [C_RED if m < 10 else (C_YELLOW if m < 20 else C_GREEN)
                  for m in cat_s["margin_pct"]]
        fig4 = go.Figure(go.Bar(
            y=cat_s["category"], x=cat_s["margin_pct"],
            orientation="h",
            marker_color=colors,
            text=[f"{m:.1f}%" for m in cat_s["margin_pct"]],
            textposition="outside",
            textfont=dict(color=C_TEXT, size=11),
        ))
        fig4.update_layout(
            **PLOT_LAYOUT, height=300,
            xaxis_ticksuffix="%",
            xaxis=dict(gridcolor=C_BORDER, tickfont=dict(color=C_MUTED, size=11)),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=C_TEXT, size=11)),
            showlegend=False,
        )
        st.plotly_chart(fig4, width='stretch')

    # ── Tabela completa ───────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Tabela de Produtos</div>', unsafe_allow_html=True)
    display = df.copy()
    display["revenue"]       = display["revenue"].map("R$ {:,.0f}".format)
    display["gross_profit"]  = display["gross_profit"].map("R$ {:,.0f}".format)
    display["margin_pct"]    = display["margin_pct"].map("{:.1f}%".format)
    display["avg_discount_pct"] = display["avg_discount_pct"].map("{:.1f}%".format)
    display = display.rename(columns={
        "product_name": "Produto", "category": "Categoria",
        "units_sold": "Unid.", "revenue": "Faturamento",
        "gross_profit": "Lucro Bruto", "margin_pct": "Margem",
        "num_orders": "Pedidos", "avg_discount_pct": "Desc. Médio",
    })
    st.dataframe(display[["Produto","Categoria","Unid.","Faturamento","Lucro Bruto","Margem","Desc. Médio"]],
                 width='stretch', hide_index=True)