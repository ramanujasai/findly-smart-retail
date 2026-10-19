from pathlib import Path

import pandas as pd
import streamlit as st

from ui.theme import apply_theme, render_sidebar, render_hero


st.set_page_config(
    page_title="Basket | Findly",
    page_icon="🛒",
    layout="wide",
)

apply_theme()
render_sidebar()

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "transactions.csv"


@st.cache_data
def load_products():
    if not DATA_FILE.exists():
        return pd.DataFrame(columns=["StockCode", "Description"])

    df = pd.read_csv(DATA_FILE, dtype={"StockCode": str})

    df["StockCode"] = df["StockCode"].astype(str).str.strip()
    df["Description"] = (
        df["Description"]
        .fillna("Unnamed product")
        .astype(str)
        .str.strip()
    )

    return (
        df[["StockCode", "Description"]]
        .drop_duplicates("StockCode")
        .reset_index(drop=True)
    )


products = load_products()
name_by_code = dict(zip(products["StockCode"], products["Description"]))

if "basket" not in st.session_state:
    st.session_state.basket = []

if "quick_add_version" not in st.session_state:
    st.session_state.quick_add_version = 0

if "map_focus" not in st.session_state:
    st.session_state.map_focus = None


def add_to_basket(code):
    code = str(code).strip()

    if code and code not in st.session_state.basket:
        st.session_state.basket.append(code)


def remove_from_basket(code):
    st.session_state.basket = [
        item for item in st.session_state.basket if item != code
    ]


def clear_basket():
    st.session_state.basket = []


def clear_product_selection():
    st.session_state.quick_add_version += 1


def locate_product(code):
    st.session_state.map_focus = str(code)
    st.switch_page("pages/2_Store_Map.py")


render_hero(
    "Findly / Basket",
    "Your shopping basket.",
    "Collect products, manage your selections, and locate items "
    "on the simulated store map.",
)

basket = list(dict.fromkeys(st.session_state.basket))
st.session_state.basket = basket

left, right = st.columns([1.7, 1], gap="large")

with left:
    st.subheader("Your current basket")
    st.caption("Each product appears once in the basket.")

    if not basket:
        st.info("Your basket is empty. Add a product below to get started.")
    else:
        for code in basket:
            with st.container(border=True):
                product_col, action_col = st.columns([5, 1])

                with product_col:
                    st.markdown(
                        f"**{name_by_code.get(code, 'Unknown product')}**"
                    )
                    st.caption(f"Product code: {code}")

                with action_col:
                    st.button(
                        "✕",
                        key=f"remove_basket_{code}",
                        help="Remove this product",
                        use_container_width=True,
                        on_click=remove_from_basket,
                        args=(code,),
                    )

with right:
    st.metric("Unique items", len(basket))

    st.button(
        "Clear basket",
        key="basket_clear_button",
        use_container_width=True,
        on_click=clear_basket,
    )

st.markdown("---")
st.subheader("Add a product")

if products.empty:
    st.error(f"Product data not found or empty: {DATA_FILE}")
else:
    options = products.sort_values("Description")
    option_codes = options["StockCode"].tolist()

    dropdown_key = f"quick_add_product_{st.session_state.quick_add_version}"

    selected_code = st.selectbox(
        "Search products",
        options=[""] + option_codes,
        format_func=lambda code: (
            "Select a product..."
            if code == ""
            else f"{name_by_code.get(code, 'Unknown product')} · {code}"
        ),
        key=dropdown_key,
        index=0,
        label_visibility="collapsed",
    )

    add_col, clear_col = st.columns(2)

    with add_col:
        if st.button(
            "＋ Add selected product",
            type="primary",
            disabled=not selected_code,
            use_container_width=True,
        ):
            add_to_basket(selected_code)
            st.rerun()

    with clear_col:
        st.button(
            "Clear selection",
            key=f"clear_selection_{st.session_state.quick_add_version}",
            use_container_width=True,
            on_click=clear_product_selection,
        )

st.markdown("---")
st.subheader("Find products on the store map")

st.write(
    "Use the Product Search page to discover items, or select a product "
    "from your basket to locate its shelf."
)

if basket:
    selected_map_code = st.selectbox(
        "Choose a basket product",
        options=basket,
        format_func=lambda code: (
            f"{name_by_code.get(code, 'Unknown product')} · {code}"
        ),
        key="basket_map_product",
    )

    st.button(
        "⌖ Locate selected product",
        key="basket_locate_button",
        type="primary",
        use_container_width=True,
        on_click=locate_product,
        args=(selected_map_code,),
    )

st.caption(
    "Shelf assignments are simulated demonstration locations. "
    "This page manages your basket and does not generate product recommendations."
)