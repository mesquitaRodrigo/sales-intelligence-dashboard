"""
generate_data.py
Gera dados sintéticos realistas de vendas e popula um banco SQLite local.
Simula uma empresa de distribuição B2B com ~18 meses de histórico.
"""

import sqlite3
import random
import pandas as pd
from faker import Faker
from datetime import date, timedelta
import os

fake = Faker("pt_BR")
random.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sales.db")

# ── Catálogo de produtos ────────────────────────────────────────────────────
PRODUCTS = [
    # (nome, categoria, custo, preço_base)
    ("Monitor LG 27'' 4K",          "Monitores",    1_200, 1_980),
    ("Monitor Samsung 24'' FHD",    "Monitores",      650, 1_050),
    ("Teclado Mecânico HyperX",     "Periféricos",    180,   349),
    ("Mouse Logitech MX Master",    "Periféricos",    210,   420),
    ("Headset Razer Kraken",        "Periféricos",    160,   289),
    ("Notebook Dell Inspiron i5",   "Notebooks",    3_200, 5_499),
    ("Notebook Lenovo ThinkPad",    "Notebooks",    3_800, 6_200),
    ("Notebook Asus VivoBook",      "Notebooks",    2_400, 3_999),
    ("SSD Kingston 1TB",            "Storage",        180,   349),
    ("SSD WD Black 2TB",            "Storage",        320,   599),
    ("Memória RAM 16GB Corsair",    "Memória",        180,   320),
    ("Memória RAM 32GB Kingston",   "Memória",        340,   599),
    ("Cabo HDMI 4K 2m",             "Cabos",           12,    45),
    ("Hub USB-C 7 em 1",            "Periféricos",     65,   159),
    ("Webcam Logitech C920",        "Periféricos",    230,   480),
    ("Nobreak APC 1500VA",          "Energia",        580, 1_099),
    ("Roteador TP-Link AX3000",     "Redes",          280,   549),
    ("Switch 24 portas D-Link",     "Redes",          420,   799),
    # produto com margem ruim (propositalmente)
    ("Impressora HP LaserJet",      "Impressoras",  1_100,   999),  # margem negativa
    ("Toner HP 85A Original",       "Impressoras",    180,   189),  # quase sem margem
]

# ── Segmentos de clientes ───────────────────────────────────────────────────
SEGMENTS = ["PME", "Enterprise", "Governo", "Varejo"]

# Metas mensais de faturamento (R$)
MONTHLY_TARGETS = {
    1: 280_000, 2: 260_000, 3: 310_000,
    4: 295_000, 5: 320_000, 6: 350_000,
    7: 330_000, 8: 340_000, 9: 380_000,
    10: 420_000, 11: 450_000, 12: 520_000,
}


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_schema(conn):
    conn.executescript("""
    DROP TABLE IF EXISTS sales;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customers;
    DROP TABLE IF EXISTS monthly_targets;

    CREATE TABLE products (
        product_id   INTEGER PRIMARY KEY,
        name         TEXT NOT NULL,
        category     TEXT NOT NULL,
        cost         REAL NOT NULL,
        base_price   REAL NOT NULL
    );

    CREATE TABLE customers (
        customer_id  INTEGER PRIMARY KEY,
        name         TEXT NOT NULL,
        segment      TEXT NOT NULL,
        city         TEXT NOT NULL,
        state        TEXT NOT NULL,
        since        DATE NOT NULL
    );

    CREATE TABLE sales (
        sale_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_date    DATE NOT NULL,
        customer_id  INTEGER REFERENCES customers(customer_id),
        product_id   INTEGER REFERENCES products(product_id),
        quantity     INTEGER NOT NULL,
        unit_price   REAL NOT NULL,
        unit_cost    REAL NOT NULL,
        discount_pct REAL NOT NULL DEFAULT 0
    );

    CREATE TABLE monthly_targets (
        year         INTEGER NOT NULL,
        month        INTEGER NOT NULL,
        target_brl   REAL NOT NULL,
        PRIMARY KEY (year, month)
    );
    """)
    conn.commit()


def seed_products(conn):
    rows = [(i+1, n, c, cost, price) for i, (n, c, cost, price) in enumerate(PRODUCTS)]
    conn.executemany(
        "INSERT INTO products VALUES (?,?,?,?,?)", rows
    )
    conn.commit()
    return rows


def seed_customers(conn, n=120):
    states = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "PE"]
    rows = []
    for i in range(1, n+1):
        seg = random.choices(SEGMENTS, weights=[50, 20, 15, 15])[0]
        state = random.choice(states)
        since = fake.date_between(start_date="-3y", end_date="-6m")
        rows.append((i, fake.company(), seg, fake.city(), state, str(since)))
    conn.executemany(
        "INSERT INTO customers VALUES (?,?,?,?,?,?)", rows
    )
    conn.commit()
    return rows


def seed_sales(conn, customers, products_raw, months=18):
    end = date.today().replace(day=1) - timedelta(days=1)
    start = (end - timedelta(days=months * 30)).replace(day=1)

    # Clientes "inativos" nos últimos 3 meses (simula churn)
    churned_customers = random.sample([c[0] for c in customers], k=15)

    sales = []
    current = start
    while current <= end:
        # Volume diário: mais alto em dias úteis, pico no final do mês
        is_weekday = current.weekday() < 5
        is_month_end = current.day >= 20
        base_orders = random.randint(3, 8) if is_weekday else random.randint(0, 2)
        if is_month_end:
            base_orders = int(base_orders * 1.4)

        for _ in range(base_orders):
            # Evitar clientes churned nos últimos 3 meses
            cutoff = end - timedelta(days=90)
            if current > cutoff:
                eligible = [c[0] for c in customers if c[0] not in churned_customers]
            else:
                eligible = [c[0] for c in customers]

            cid = random.choice(eligible)
            pid, _name, _cat, cost, base_price = random.choice(products_raw)

            # Impressoras têm volume alto para evidenciar o problema
            if _cat == "Impressoras":
                qty = random.randint(3, 12)
            elif _cat == "Notebooks":
                qty = random.randint(1, 4)
            else:
                qty = random.randint(1, 10)

            # Desconto: governo e enterprise conseguem mais desconto
            seg = next(c[2] for c in customers if c[0] == cid)
            max_disc = {"Governo": 0.20, "Enterprise": 0.15, "PME": 0.08, "Varejo": 0.05}[seg]
            disc = round(random.uniform(0, max_disc), 4)

            # Variação leve no preço unitário
            unit_price = round(base_price * (1 + random.uniform(-0.03, 0.05)), 2)
            unit_price = round(unit_price * (1 - disc), 2)

            sales.append((
                str(current), cid, pid, qty,
                unit_price, cost, round(disc, 4)
            ))

        current += timedelta(days=1)

    conn.executemany(
        """INSERT INTO sales
           (sale_date, customer_id, product_id, quantity, unit_price, unit_cost, discount_pct)
           VALUES (?,?,?,?,?,?,?)""",
        sales,
    )
    conn.commit()
    print(f"  {len(sales):,} vendas geradas.")


def seed_targets(conn, months=18):
    end = date.today().replace(day=1) - timedelta(days=1)
    start = (end - timedelta(days=months * 30)).replace(day=1)
    rows = []
    current = start
    while current <= end:
        base = MONTHLY_TARGETS.get(current.month, 320_000)
        # Crescimento YoY de ~8%
        factor = 1 + 0.08 * (current.year - start.year)
        rows.append((current.year, current.month, round(base * factor, 2)))
        # avança um mês
        if current.month == 12:
            current = current.replace(year=current.year+1, month=1)
        else:
            current = current.replace(month=current.month+1)
    conn.executemany(
        "INSERT INTO monthly_targets VALUES (?,?,?)", rows
    )
    conn.commit()


def create_views(conn):
    conn.executescript("""
    DROP VIEW IF EXISTS vw_sales_detail;
    DROP VIEW IF EXISTS vw_monthly_performance;
    DROP VIEW IF EXISTS vw_product_performance;
    DROP VIEW IF EXISTS vw_customer_performance;
    DROP VIEW IF EXISTS vw_margin_alerts;

    -- Detalhe de cada venda com métricas calculadas
    CREATE VIEW vw_sales_detail AS
    SELECT
        s.sale_id,
        s.sale_date,
        strftime('%Y', s.sale_date)       AS year,
        CAST(strftime('%m', s.sale_date) AS INTEGER) AS month,
        strftime('%Y-%m', s.sale_date)    AS year_month,
        c.customer_id,
        c.name                            AS customer_name,
        c.segment,
        c.state,
        p.product_id,
        p.name                            AS product_name,
        p.category,
        s.quantity,
        s.unit_price,
        s.unit_cost,
        s.discount_pct,
        ROUND(s.quantity * s.unit_price, 2)                         AS revenue,
        ROUND(s.quantity * s.unit_cost, 2)                          AS total_cost,
        ROUND(s.quantity * (s.unit_price - s.unit_cost), 2)         AS gross_profit,
        ROUND((s.unit_price - s.unit_cost) / NULLIF(s.unit_price, 0) * 100, 2) AS margin_pct
    FROM sales s
    JOIN customers c ON c.customer_id = s.customer_id
    JOIN products  p ON p.product_id  = s.product_id;

    -- Performance mensal vs meta
    CREATE VIEW vw_monthly_performance AS
    SELECT
        d.year,
        d.month,
        d.year_month,
        ROUND(SUM(d.revenue), 2)      AS revenue,
        ROUND(SUM(d.gross_profit), 2) AS gross_profit,
        ROUND(SUM(d.gross_profit) / NULLIF(SUM(d.revenue), 0) * 100, 2) AS margin_pct,
        COUNT(DISTINCT d.sale_id)     AS num_orders,
        COUNT(DISTINCT d.customer_id) AS active_customers,
        ROUND(SUM(d.revenue) / NULLIF(COUNT(DISTINCT d.sale_id), 0), 2) AS avg_ticket,
        t.target_brl,
        ROUND(SUM(d.revenue) / NULLIF(t.target_brl, 0) * 100, 2) AS target_pct
    FROM vw_sales_detail d
    LEFT JOIN monthly_targets t
           ON t.year = CAST(d.year AS INTEGER) AND t.month = d.month
    GROUP BY d.year, d.month, d.year_month, t.target_brl;

    -- Performance por produto (acumulada)
    CREATE VIEW vw_product_performance AS
    SELECT
        product_id,
        product_name,
        category,
        SUM(quantity)                 AS units_sold,
        ROUND(SUM(revenue), 2)        AS revenue,
        ROUND(SUM(gross_profit), 2)   AS gross_profit,
        ROUND(SUM(gross_profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS margin_pct,
        COUNT(DISTINCT sale_id)       AS num_orders,
        ROUND(AVG(discount_pct) * 100, 2) AS avg_discount_pct
    FROM vw_sales_detail
    GROUP BY product_id, product_name, category;

    -- Performance por cliente
    CREATE VIEW vw_customer_performance AS
    SELECT
        customer_id,
        customer_name,
        segment,
        state,
        COUNT(DISTINCT sale_id)       AS num_orders,
        SUM(quantity)                 AS units_bought,
        ROUND(SUM(revenue), 2)        AS revenue,
        ROUND(SUM(gross_profit), 2)   AS gross_profit,
        ROUND(SUM(gross_profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS margin_pct,
        ROUND(AVG(discount_pct) * 100, 2) AS avg_discount_pct,
        MIN(sale_date)                AS first_purchase,
        MAX(sale_date)                AS last_purchase
    FROM vw_sales_detail
    GROUP BY customer_id, customer_name, segment, state;

    -- Alertas de margem: produtos ou clientes com margem abaixo de 10%
    CREATE VIEW vw_margin_alerts AS
    SELECT 'produto' AS tipo, product_name AS nome, category AS detalhe,
           margin_pct, revenue
    FROM vw_product_performance
    WHERE margin_pct < 10
    UNION ALL
    SELECT 'cliente', customer_name, segment, margin_pct, revenue
    FROM vw_customer_performance
    WHERE margin_pct < 10 AND revenue > 5000;
    """)
    conn.commit()


def main():
    print("🔧 Gerando banco de dados de vendas...")
    conn = get_conn()
    create_schema(conn)
    print("  Schema criado.")
    products_raw = seed_products(conn)
    print(f"  {len(products_raw)} produtos inseridos.")
    customers = seed_customers(conn, n=120)
    print(f"  {len(customers)} clientes inseridos.")
    seed_sales(conn, customers, products_raw, months=18)
    seed_targets(conn)
    print("  Metas inseridas.")
    create_views(conn)
    print("  Views analíticas criadas.")
    conn.close()
    print(f"\n✅ Banco salvo em: {DB_PATH}")


if __name__ == "__main__":
    main()
