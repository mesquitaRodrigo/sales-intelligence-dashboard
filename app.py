"""
app.py  ·  Sales Intelligence Dashboard
"""

import os, sys, importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import streamlit as st

# ── Gerar dados se o banco não existir ──────────────────────────────────────
DB_PATH = os.path.join(BASE_DIR, "data", "sales.db")
if not os.path.exists(DB_PATH):
    with st.spinner("Gerando base de dados de demonstração…"):
        spec = importlib.util.spec_from_file_location(
            "generate_data", os.path.join(BASE_DIR, "generate_data.py")
        )
        gen_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen_mod)
        gen_mod.main()

# ── Config da página ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sales Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS global ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f1117; }
.kpi-card {
    background: #1a1d27; border: 1px solid #2a2d3e;
    border-radius: 12px; padding: 20px 24px; text-align: center;
}
.kpi-label {
    color: #8b92a5; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
}
.kpi-value {
    color: #e8eaf0; font-size: 28px; font-weight: 700;
    font-family: 'JetBrains Mono', monospace; line-height: 1;
}
.kpi-value-sm {
    color: #e8eaf0; font-size: 22px; font-weight: 700;
    font-family: 'JetBrains Mono', monospace; line-height: 1;
}
.kpi-delta { font-size: 12px; margin-top: 6px; font-weight: 500; }
.kpi-up   { color: #4ade80; }
.kpi-down { color: #f87171; }
.kpi-warn { color: #fbbf24; }
section[data-testid="stSidebar"] { background: #13151f !important; }
.section-title {
    color: #c5c9d6; font-size: 13px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.2px;
    border-bottom: 1px solid #2a2d3e; padding-bottom: 8px; margin: 24px 0 16px 0;
}
.stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Navegação lateral ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 8px 0 24px 0;">
        <div style="color:#6366f1; font-size:22px; font-weight:700; letter-spacing:-0.5px;">
            📊 Sales Intel
        </div>
        <div style="color:#8b92a5; font-size:12px; margin-top:4px;">Business Intelligence Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navegação",
        ["🏠  Visão Geral", "📦  Produtos", "👥  Clientes", "🔍  Onde Perdemos Dinheiro"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Dados sintéticos · 18 meses · 120 clientes · 20 produtos")


# ── Carrega view pelo caminho absoluto ──────────────────────────────────────
# Tenta diretório base primeiro, depois 'views/' e 'pages/'
def load_view(name: str):
    for folder in (None, "views", "pages"):
        if folder is None:
            path = os.path.join(BASE_DIR, f"{name}.py")
        else:
            path = os.path.join(BASE_DIR, folder, f"{name}.py")
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location(name, path)
            mod  = importlib.util.module_from_spec(spec)
            mod.__spec__.origin = path  # garante __file__ correto dentro do módulo
            if folder:
                sys.path.insert(0, os.path.join(BASE_DIR, folder))
            spec.loader.exec_module(mod)
            return mod
    raise FileNotFoundError(
        f"View '{name}' não encontrada no diretório base, views/ nem em pages/\n"
        f"Diretório base: {BASE_DIR}\n"
        f"Conteúdo: {os.listdir(BASE_DIR)}"
    )


# ── Roteamento ────────────────────────────────────────────────────────────────
if page == "🏠  Visão Geral":
    load_view("overview").render()
elif page == "📦  Produtos":
    load_view("products").render()
elif page == "👥  Clientes":
    load_view("customers").render()
else:
    load_view("intelligence").render()