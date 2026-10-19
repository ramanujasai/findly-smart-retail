from pathlib import Path

import pandas as pd
import streamlit as st

from ui.theme import apply_theme, render_sidebar, render_hero


st.set_page_config(
    page_title="Findly | Smart Retail",
    page_icon="🟢",
    layout="wide",
)

# Disable Streamlit's automatic multipage navigation.
st.set_option("client.showSidebarNavigation", False)

apply_theme()
render_sidebar()

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "processed" / "transactions.csv"
RULES_FILE = ROOT / "results" / "association_rules.csv"


# --------------------------------------------------
# Home page header
# --------------------------------------------------

render_hero(
    "Smart Retail Experience",
    "Shopping, reimagined.",
    "Discover products and explore a simulated store "
    "using insights from historical retail transactions.",
)


# --------------------------------------------------
# Project statistics
# --------------------------------------------------

products_count = 0
transactions_count = 0
rules_count = 0

if DATA_FILE.exists():
    try:
        data = pd.read_csv(
            DATA_FILE,
            usecols=["StockCode", "InvoiceNo"],
        )
        products_count = data["StockCode"].nunique()
        transactions_count = data["InvoiceNo"].nunique()
    except (ValueError, OSError, pd.errors.ParserError):
        pass

if RULES_FILE.exists():
    try:
        rules_count = len(pd.read_csv(RULES_FILE))
    except (OSError, pd.errors.ParserError):
        pass

m1, m2, m3 = st.columns(3)

m1.metric("Unique products", f"{products_count:,}")
m2.metric("Transactions", f"{transactions_count:,}")
m3.metric("Association rules", f"{rules_count:,}")


# --------------------------------------------------
# Feature navigation
# --------------------------------------------------

st.markdown("---")
st.subheader("Explore Findly")
st.caption("Choose a tool to get started.")

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    with st.container(border=True):
        st.markdown("### ⌕ Product Discovery")
        st.write(
            "Search the retail catalogue, inspect product details, "
            "and add products to your basket."
        )

        if st.button(
            "Explore products →",
            key="home_search",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page("pages/1_Product_Search.py")

with col2:
    with st.container(border=True):
        st.markdown("### ▦ Interactive Store Map")
        st.write(
            "Explore simulated floors, rows, and shelves, "
            "then locate selected products."
        )

        if st.button(
            "Explore store →",
            key="home_map",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page("pages/2_Store_Map.py")

with col3:
    with st.container(border=True):
        st.markdown("### 🛒 Basket")
        st.write(
            "Manage your basket, remove products, "
            "and locate selected products on the store map."
        )

        if st.button(
            "Open basket →",
            key="home_basket",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page("pages/3_Basket_Recommendations.py")


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.markdown("---")
st.caption(
    "Findly is a data-mining demonstration. Store locations are simulated, "
    "and historical purchase associations do not guarantee future purchases."
)