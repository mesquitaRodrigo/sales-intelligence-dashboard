"""
db.py
Camada de acesso a dados — todas as queries SQL ficam aqui.
O dashboard só importa funções deste módulo.
"""

import sqlite3
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sales.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql: str, params=()) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


# ── KPIs gerais ────────────────────────────────────────────────────────────

def kpis_overview(year: int | None = None) -> dict:
    where = "WHERE year = ?" if year else ""
    params = (str(year),) if year else ()
    df = query(f"""
        SELECT
            ROUND(SUM(revenue), 2)       AS revenue,
            ROUND(SUM(gross_profit), 2)  AS gross_profit,
            ROUND(SUM(gross_profit) / NULLIF(SUM(revenue),0)*100, 2) AS margin_pct,
            COUNT(DISTINCT sale_id)      AS orders,
            COUNT(DISTINCT customer_id)  AS customers,
            ROUND(SUM(revenue)/NULLIF(COUNT(DISTINCT sale_id),0), 2) AS avg_ticket
        FROM vw_sales_detail {where}
    """, params)
    return df.iloc[0].to_dict()


def kpis_current_month() -> dict:
    df = query("""
        SELECT
            year_month,
            revenue, gross_profit, margin_pct,
            num_orders, active_customers, avg_ticket,
            target_brl, target_pct
        FROM vw_monthly_performance
        ORDER BY year_month DESC
        LIMIT 1
    """)
    return df.iloc[0].to_dict()


# ── Séries temporais ────────────────────────────────────────────────────────

def monthly_revenue_vs_target() -> pd.DataFrame:
    return query("""
        SELECT year_month, revenue, gross_profit, margin_pct,
               target_brl, target_pct, avg_ticket, active_customers
        FROM vw_monthly_performance
        ORDER BY year_month
    """)


def revenue_by_segment_monthly() -> pd.DataFrame:
    return query("""
        SELECT year_month, segment,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(gross_profit)/NULLIF(SUM(revenue),0)*100,2) AS margin_pct
        FROM vw_sales_detail
        GROUP BY year_month, segment
        ORDER BY year_month, segment
    """)


# ── Produtos ────────────────────────────────────────────────────────────────

def product_performance(limit: int = 20) -> pd.DataFrame:
    return query(f"""
        SELECT * FROM vw_product_performance
        ORDER BY revenue DESC
        LIMIT {limit}
    """)


def product_margin_scatter() -> pd.DataFrame:
    """Todos os produtos: revenue × margin (para scatter)."""
    return query("""
        SELECT product_name, category, revenue, margin_pct,
               units_sold, avg_discount_pct
        FROM vw_product_performance
        ORDER BY revenue DESC
    """)


def category_summary() -> pd.DataFrame:
    return query("""
        SELECT category,
               ROUND(SUM(revenue), 2)     AS revenue,
               ROUND(SUM(gross_profit),2) AS gross_profit,
               ROUND(SUM(gross_profit)/NULLIF(SUM(revenue),0)*100,2) AS margin_pct,
               SUM(units_sold)            AS units_sold
        FROM vw_product_performance
        GROUP BY category
        ORDER BY revenue DESC
    """)


# ── Clientes ────────────────────────────────────────────────────────────────

def customer_performance(limit: int = 50) -> pd.DataFrame:
    return query(f"""
        SELECT * FROM vw_customer_performance
        ORDER BY revenue DESC
        LIMIT {limit}
    """)


def segment_summary() -> pd.DataFrame:
    return query("""
        SELECT segment,
               COUNT(*) AS customers,
               ROUND(SUM(revenue),2)     AS revenue,
               ROUND(SUM(gross_profit),2) AS gross_profit,
               ROUND(SUM(gross_profit)/NULLIF(SUM(revenue),0)*100,2) AS margin_pct,
               ROUND(AVG(avg_discount_pct),2) AS avg_discount_pct
        FROM vw_customer_performance
        GROUP BY segment
        ORDER BY revenue DESC
    """)


def churn_risk() -> pd.DataFrame:
    """Clientes que compraram antes mas não compraram nos últimos 60 dias."""
    return query("""
        SELECT customer_name, segment, revenue,
               last_purchase,
               CAST(julianday('now') - julianday(last_purchase) AS INTEGER) AS days_since
        FROM vw_customer_performance
        WHERE julianday('now') - julianday(last_purchase) > 60
          AND revenue > 1000
        ORDER BY revenue DESC
        LIMIT 30
    """)


# ── Alertas / inteligência ──────────────────────────────────────────────────

def margin_alerts() -> pd.DataFrame:
    return query("""
        SELECT * FROM vw_margin_alerts
        ORDER BY margin_pct ASC
    """)


def discount_impact() -> pd.DataFrame:
    """Quanto o desconto custou em cada segmento."""
    return query("""
        SELECT segment,
               ROUND(AVG(discount_pct)*100, 2)  AS avg_discount_pct,
               ROUND(SUM(revenue), 2)            AS net_revenue,
               ROUND(SUM(quantity * unit_cost * discount_pct / (1 - discount_pct + 0.0001)), 2)
                                                 AS approx_discount_lost
        FROM vw_sales_detail
        GROUP BY segment
        ORDER BY avg_discount_pct DESC
    """)


def missed_target_months() -> pd.DataFrame:
    return query("""
        SELECT year_month, revenue, target_brl,
               ROUND(target_brl - revenue, 2) AS gap,
               target_pct
        FROM vw_monthly_performance
        WHERE target_pct < 100
        ORDER BY gap DESC
    """)
