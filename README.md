# 📊 Sales Intelligence Dashboard

> Dashboard de inteligência de negócios construído com Python, Pandas, SQL e Streamlit — focado em **mostrar onde a empresa ganha e perde dinheiro**, não apenas em gráficos bonitos.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=flat&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.20+-3F4F75?style=flat&logo=plotly&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)

---

## ✨ Funcionalidades

### 🏠 Visão Geral
- KPIs do mês atual: faturamento, lucro bruto, margem bruta, ticket médio e clientes ativos
- Gráfico mensal de **faturamento vs meta** (barra verde = bateu, vermelha = não bateu)
- Evolução de margem bruta e ticket médio ao longo do tempo
- Faturamento por segmento (PME, Enterprise, Governo, Varejo)

### 📦 Produtos
- Top 10 produtos: faturamento vs lucro bruto sobrepostos
- **Scatter de rentabilidade**: faturamento × margem com tamanho proporcional ao volume
- Mix de faturamento e ranking de margem por categoria
- Tabela completa com desconto médio por SKU

### 👥 Clientes
- **Curva de Pareto**: quantos clientes respondem por 80% da receita
- Performance por segmento: faturamento, lucro bruto e margem comparados
- **Radar de churn**: clientes sem compra há +60 dias com receita em risco em R$
- Top 20 clientes com margem individual

### 🔍 Onde Perdemos Dinheiro *(diferencial)*
- Produtos com **margem negativa ou abaixo de 10%** com diagnóstico visual
- **Custo real dos descontos** por segmento: receita deixada na mesa em R$
- Meses que ficaram abaixo da meta com gap acumulado
- **Scorecard executivo**: tabela de alertas priorizados com ação sugerida

---

## 🏗️ Arquitetura

```
sales_intelligence_dashboard/
├── app.py               # Entrada Streamlit + roteamento por importlib
├── db.py                # Camada de acesso a dados (todas as queries SQL)
├── generate_data.py     # Gerador de dados sintéticos (18 meses, B2B)
├── requirements.txt
├── data/
│   └── sales.db         # Gerado automaticamente no primeiro run (gitignored)
└── pages/
    ├── overview.py      # Visão Geral
    ├── products.py      # Produtos
    ├── customers.py     # Clientes
    └── intelligence.py  # Onde Perdemos Dinheiro
```

### Pipeline de dados

```
generate_data.py
    └── Faker (pt_BR) → 120 clientes, 20 produtos, ~40k vendas, 18 meses
    └── SQLite: products, customers, sales, monthly_targets

SQL Views (analytics layer)
    ├── vw_sales_detail          → margem calculada por venda
    ├── vw_monthly_performance   → faturamento mensal vs meta
    ├── vw_product_performance   → rentabilidade por produto
    ├── vw_customer_performance  → performance + signal de churn
    └── vw_margin_alerts         → produtos/clientes com margem < 10%

db.py  →  funções que executam SQL e retornam DataFrames pandas

pages/  →  apenas visualização (Streamlit + Plotly)
```

### Decisões técnicas

| Decisão | Motivo |
|---|---|
| **SQLite** em vez de PostgreSQL | Portabilidade — `git clone` + `pip install` já funciona |
| **Views SQL** para métricas | Cálculo no banco, não no Python — mais próximo de dbt/Redshift real |
| **db.py isolado** | Troca de banco sem tocar na UI; facilita testes |
| **importlib** para carregar pages | Resolve conflito do Streamlit com a pasta `pages/` reservada |
| **Dados propositalmente imperfeitos** | 2 produtos com margem negativa + 15 clientes em churn = dashboard analiticamente interessante |

---

## ⚙️ Como rodar

```bash
# 1. Clone
git clone https://github.com/mesquitaRodrigo/sales-intelligence-dashboard.git
cd sales-intelligence-dashboard

# 2. Ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Dependências
pip install -r requirements.txt

# 4. Rodar
streamlit run app.py
```

O banco SQLite é gerado automaticamente na primeira execução. Nenhuma configuração adicional necessária.

---

## 🛠️ Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Dashboard | Streamlit |
| Visualização | Plotly |
| Dados | Pandas + SQLite |
| Geração de dados | Faker (pt_BR) |

---

## 📁 Outros projetos no portfólio

- **[Rio Compras Pipeline](https://github.com/mesquitaRodrigo/rio-compras-pipeline)** — pipeline Airflow + dbt + PostgreSQL com dados abertos do governo RJ
- **[Copa Analytics](https://github.com/mesquitaRodrigo/copa-analytics)** — pipeline em tempo real de audiência da Copa 2026 com YouTube API + Metabase