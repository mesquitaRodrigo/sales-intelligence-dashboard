"""pages/intelligence.py — Onde Estamos Perdendo Dinheiro"""

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
    st.markdown("## 🔍 Onde Estamos Perdendo Dinheiro")
    st.markdown(
        '<p style="color:#8b92a5;margin-top:-12px;">'
        'Diagnóstico de margem negativa, desconto excessivo e metas não cumpridas</p>',
        unsafe_allow_html=True,
    )

    alerts   = db.margin_alerts()
    disc     = db.discount_impact()
    missed   = db.missed_target_months()
    products = db.product_performance(20)

    # ══════════════════════════════════════════════════════════════════════
    # 1 · PRODUTOS COM MARGEM DESTRUTIVA
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">⚠️ Produtos com Margem Abaixo de 10%</div>',
                unsafe_allow_html=True)

    bad_prod = products[products["margin_pct"] < 10].copy()

    if bad_prod.empty:
        st.success("Nenhum produto com margem crítica encontrado.")
    else:
        # Resumo executivo
        total_revenue_bad = bad_prod["revenue"].sum()
        total_loss        = bad_prod["gross_profit"].sum()
        loss_color        = C_RED if total_loss < 0 else C_YELLOW

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">Produtos em Alerta</div>
                <div class="kpi-value" style="color:{C_RED}">{len(bad_prod)}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">Faturamento Envolvido</div>
                <div class="kpi-value">R$ {total_revenue_bad:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="kpi-card">
                <div class="kpi-label">Resultado Bruto</div>
                <div class="kpi-value" style="color:{loss_color}">R$ {total_loss:,.0f}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("")

        # Gráfico waterfall: quanto cada produto destrói ou gera
        bad_sorted = bad_prod.sort_values("gross_profit")
        colors_bar = [C_RED if v < 0 else C_YELLOW for v in bad_sorted["gross_profit"]]

        fig = go.Figure(go.Bar(
            y=bad_sorted["product_name"],
            x=bad_sorted["gross_profit"],
            orientation="h",
            marker_color=colors_bar,
            text=[f"R$ {v:,.0f}" for v in bad_sorted["gross_profit"]],
            textposition="outside",
            textfont=dict(color=C_TEXT, size=11),
        ))
        fig.add_vline(x=0, line_color=C_MUTED, line_width=1)
        fig.update_layout(
            **PLOT_LAYOUT, height=max(200, len(bad_sorted) * 50),
            title=dict(text="Lucro Bruto por Produto (R$)", font=dict(size=13, color=C_MUTED)),
            xaxis=dict(gridcolor=C_BORDER, tickprefix="R$ ", tickformat=",.0f",
                       tickfont=dict(color=C_MUTED, size=11)),
            yaxis=dict(tickfont=dict(color=C_TEXT, size=11)),
        )
        st.plotly_chart(fig, width='stretch')

        # Tabela de diagnóstico
        diag = bad_prod[["product_name","category","units_sold","revenue",
                          "gross_profit","margin_pct","avg_discount_pct"]].copy()
        diag["revenue"]      = diag["revenue"].map("R$ {:,.0f}".format)
        diag["gross_profit"] = diag["gross_profit"].map("R$ {:,.0f}".format)
        diag["margin_pct"]   = diag["margin_pct"].map("{:.1f}%".format)
        diag["avg_discount_pct"] = diag["avg_discount_pct"].map("{:.1f}%".format)
        diag.columns = ["Produto","Categoria","Unid.","Faturamento","Lucro Bruto","Margem","Desc. Médio"]
        st.dataframe(diag, width='stretch', hide_index=True)

        st.error(
            "**Diagnóstico:** Esses produtos são vendidos abaixo do custo ou com margem "
            "insuficiente para cobrir despesas operacionais. Recomendação: renegociar preço "
            "de compra, reajustar preço de venda ou descontinuar o SKU."
        )

    # ══════════════════════════════════════════════════════════════════════
    # 2 · CUSTO DOS DESCONTOS
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">💸 Impacto dos Descontos por Segmento</div>',
                unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        fig2 = go.Figure(go.Bar(
            x=disc["segment"],
            y=disc["avg_discount_pct"],
            marker_color=[C_RED if d > 12 else (C_YELLOW if d > 7 else C_GREEN)
                          for d in disc["avg_discount_pct"]],
            text=[f"{d:.1f}%" for d in disc["avg_discount_pct"]],
            textposition="outside",
            textfont=dict(color=C_TEXT, size=12),
        ))
        fig2.update_layout(
            **PLOT_LAYOUT, height=260,
            title=dict(text="Desconto Médio % por Segmento", font=dict(size=13, color=C_MUTED)),
            yaxis=dict(gridcolor=C_BORDER, ticksuffix="%",
                       tickfont=dict(color=C_MUTED, size=11)),
            xaxis=dict(tickfont=dict(color=C_TEXT, size=12)),
        )
        st.plotly_chart(fig2, width='stretch')

    with col_r:
        fig3 = go.Figure(go.Bar(
            x=disc["segment"],
            y=disc["approx_discount_lost"],
            marker_color=C_RED,
            opacity=0.8,
            text=[f"R$ {v:,.0f}" for v in disc["approx_discount_lost"]],
            textposition="outside",
            textfont=dict(color=C_TEXT, size=11),
        ))
        fig3.update_layout(
            **PLOT_LAYOUT, height=260,
            title=dict(text="Receita Deixada na Mesa (R$)", font=dict(size=13, color=C_MUTED)),
            yaxis=dict(gridcolor=C_BORDER, tickprefix="R$ ", tickformat=",.0f",
                       tickfont=dict(color=C_MUTED, size=11)),
            xaxis=dict(tickfont=dict(color=C_TEXT, size=12)),
        )
        st.plotly_chart(fig3, width='stretch')

    total_lost = disc["approx_discount_lost"].sum()
    st.warning(
        f"**Total estimado em descontos concedidos:** R$ {total_lost:,.0f}  ·  "
        f"Segmento Governo lidera em desconto médio. Avaliar política de desconto por segmento."
    )

    # ══════════════════════════════════════════════════════════════════════
    # 3 · MESES QUE FICARAM ABAIXO DA META
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🎯 Meses Abaixo da Meta de Faturamento</div>',
                unsafe_allow_html=True)

    if missed.empty:
        st.success("Todos os meses atingiram a meta — parabéns!")
    else:
        total_gap = missed["gap"].sum()
        st.error(
            f"**{len(missed)} meses** ficaram abaixo da meta · "
            f"Gap acumulado: **R$ {total_gap:,.0f}**"
        )

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=missed["year_month"], y=missed["gap"],
            name="Gap vs Meta",
            marker_color=C_RED, opacity=0.8,
            text=[f"R$ {v:,.0f}" for v in missed["gap"]],
            textposition="outside",
            textfont=dict(color=C_TEXT, size=10),
        ))
        fig4.add_trace(go.Scatter(
            x=missed["year_month"], y=missed["target_pct"],
            name="% da Meta", mode="lines+markers",
            line=dict(color=C_YELLOW, width=2),
            marker=dict(size=6),
            yaxis="y2",
        ))
        fig4.update_layout(
            **PLOT_LAYOUT, height=300,
            yaxis=dict(gridcolor=C_BORDER, tickprefix="R$ ", tickformat=",.0f",
                       tickfont=dict(color=C_MUTED, size=11)),
            yaxis2=dict(overlaying="y", side="right", ticksuffix="%",
                        showgrid=False, tickfont=dict(color=C_YELLOW, size=11)),
            xaxis=dict(gridcolor=C_BORDER, tickfont=dict(color=C_MUTED, size=11)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                        font=dict(size=12, color=C_TEXT)),
            hovermode="x unified",
        )
        st.plotly_chart(fig4, width='stretch')

    # ══════════════════════════════════════════════════════════════════════
    # 4 · SCORECARD EXECUTIVO
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📋 Scorecard Executivo · Principais Alertas</div>',
                unsafe_allow_html=True)

    alerts_list = []
    if not bad_prod.empty:
        for _, row in bad_prod.iterrows():
            alerts_list.append({
                "Prioridade": "🔴 Alta" if row["gross_profit"] < 0 else "🟡 Média",
                "Área": "Produto",
                "Problema": f"{row['product_name']} com margem de {row['margin_pct']:.1f}%",
                "Impacto": f"R$ {row['gross_profit']:,.0f} de resultado bruto",
                "Ação Sugerida": "Renegociar custo ou reajustar preço",
            })

    if not missed.empty:
        worst = missed.iloc[0]
        alerts_list.append({
            "Prioridade": "🔴 Alta",
            "Área": "Metas",
            "Problema": f"Pior mês: {worst['year_month']} atingiu apenas {worst['target_pct']:.0f}% da meta",
            "Impacto": f"Gap de R$ {worst['gap']:,.0f}",
            "Ação Sugerida": "Revisar capacidade comercial e mix de vendas nesse período",
        })

    high_disc = disc[disc["avg_discount_pct"] > 12]
    for _, row in high_disc.iterrows():
        alerts_list.append({
            "Prioridade": "🟡 Média",
            "Área": "Desconto",
            "Problema": f"Segmento {row['segment']} com desconto médio de {row['avg_discount_pct']:.1f}%",
            "Impacto": f"R$ {row['approx_discount_lost']:,.0f} em receita perdida",
            "Ação Sugerida": "Revisar política de desconto e autonomia do vendedor",
        })

    if alerts_list:
        import pandas as pd
        df_alerts = pd.DataFrame(alerts_list)
        st.dataframe(df_alerts, width='stretch', hide_index=True)
    else:
        st.success("Nenhum alerta crítico identificado.")