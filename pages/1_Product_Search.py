
import hashlib
from difflib import SequenceMatcher
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.theme import apply_theme, render_sidebar, render_hero


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Product Discovery | Findly",
    page_icon="🔎",
    layout="wide",
)

apply_theme()
render_sidebar()

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "transactions.csv"

for key, default in {
    "basket": [],
    "map_focus": None,
    "selected_product": None,
    "last_product_query": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# PRODUCT DATA
# ============================================================

@st.cache_data
def load_products():
    if not DATA_FILE.exists():
        return pd.DataFrame(columns=["StockCode", "Description"])

    df = pd.read_csv(
        DATA_FILE,
        usecols=["StockCode", "Description"],
        dtype={"StockCode": str},
        low_memory=False,
    )

    df["StockCode"] = df["StockCode"].fillna("").str.strip()
    df["Description"] = (
        df["Description"]
        .fillna("Unnamed product")
        .astype(str)
        .str.strip()
    )

    df = df[df["StockCode"] != ""]

    return (
        df.drop_duplicates(subset="StockCode")
        .reset_index(drop=True)
    )


def assign_demo_location(stock_code):
    """Keep this algorithm identical to the Store Map."""

    digest = hashlib.sha256(
        str(stock_code).encode("utf-8")
    ).hexdigest()

    number = int(digest[:12], 16)

    return {
        "Floor": ["Floor 1", "Floor 2"][number % 2],
        "Row": f"Row {list('ABCDEFGH')[(number // 2) % 8]}",
        "Shelf": f"Shelf {((number // 16) % 12) + 1:02d}",
    }


products = load_products()

if products.empty:
    st.error(
        "The product catalogue could not be loaded. Check this file:\n\n"
        f"{DATA_FILE}"
    )
    st.stop()

name_by_code = dict(
    zip(products["StockCode"], products["Description"])
)


# ============================================================
# ACTIONS
# ============================================================

def add_to_basket(code):
    code = str(code).strip()

    if code and code not in st.session_state.basket:
        st.session_state.basket.append(code)


def select_product(code):
    st.session_state.selected_product = str(code)


def clear_selected_product():
    st.session_state.selected_product = None


def locate_product(code):
    # The Store Map reads this code, selects its floor,
    # highlights the corresponding shelf, and displays its products.
    st.session_state.map_focus = str(code)
    st.switch_page("pages/2_Store_Map.py")


# ============================================================
# SEARCH
# ============================================================

def search_products(df, query):
    query = query.strip().lower()

    if not query:
        return df.head(0)

    description_matches = df["Description"].str.lower().str.contains(
        query,
        regex=False,
        na=False,
    )

    code_matches = df["StockCode"].str.lower().str.contains(
        query,
        regex=False,
        na=False,
    )

    matches = df[description_matches | code_matches]

    if not matches.empty:
        return matches.head(60)

    # Fuzzy matching fallback for small spelling mistakes.
    scored = []

    for _, row in df.iterrows():
        ratio = SequenceMatcher(
            None,
            query,
            row["Description"].lower(),
        ).ratio()

        if ratio >= 0.45:
            scored.append((ratio, row))

    scored.sort(key=lambda item: item[0], reverse=True)

    if not scored:
        return df.head(0)

    return pd.DataFrame(
        [row.to_dict() for _, row in scored[:30]]
    )


# ============================================================
# PAGE HEADER
# ============================================================

render_hero(
    "Findly / Product Discovery",
    "Find your next favourite.",
    "Search the retail catalogue, inspect products, add them to your "
    "basket, or locate their simulated shelf in the store map.",
)


# ============================================================
# SEARCH FORM
# ============================================================

with st.form("product_search_form"):
    query = st.text_input(
        "Search products",
        value=st.session_state.last_product_query,
        placeholder="Try WHITE METAL LANTERN or a stock code...",
    )

    submitted = st.form_submit_button(
        "Search products",
        type="primary",
        use_container_width=True,
    )

    if submitted:
        st.session_state.last_product_query = query.strip()
        st.session_state.selected_product = None

current_query = st.session_state.last_product_query


# ============================================================
# SEARCH RESULTS
# ============================================================

if current_query:
    results = search_products(products, current_query)

    st.subheader(f"Search results · {len(results)} products")

    if results.empty:
        st.warning(
            "No matching products found. Try a different product name "
            "or stock code."
        )

    else:
        for start in range(0, len(results), 2):
            columns = st.columns(2, gap="large")

            for column, (_, product) in zip(
                columns,
                results.iloc[start:start + 2].iterrows(),
            ):
                code = str(product["StockCode"])
                name = str(product["Description"])
                location = assign_demo_location(code)

                with column:
                    with st.container(border=True):
                        st.markdown(
                            f'<div class="findly-product-name">'
                            f'{escape(name)}</div>'
                            f'<div class="findly-product-code">'
                            f'Product code: {escape(code)}</div>',
                            unsafe_allow_html=True,
                        )

                        st.caption(
                            f'{location["Floor"]} · '
                            f'{location["Row"]} · '
                            f'{location["Shelf"]} · Simulated location'
                        )

                        already_added = (
                            code in st.session_state.basket
                        )

                        details_col, basket_col, map_col = st.columns(
                            3,
                            gap="small",
                        )

                        with details_col:
                            st.button(
                                "View details",
                                key=f"details_{code}",
                                use_container_width=True,
                                on_click=select_product,
                                args=(code,),
                            )

                        with basket_col:
                            st.button(
                                "✓ Added" if already_added else "+ Basket",
                                key=f"add_search_{code}",
                                disabled=already_added,
                                type="primary",
                                use_container_width=True,
                                on_click=add_to_basket,
                                args=(code,),
                            )

                        with map_col:
                            st.button(
                                "⌖ Locate",
                                key=f"locate_search_{code}",
                                help="Open the Store Map at this product's shelf",
                                use_container_width=True,
                                on_click=locate_product,
                                args=(code,),
                            )


# ============================================================
# PRODUCT DETAILS
# ============================================================

selected_code = st.session_state.selected_product

if selected_code:
    selected_rows = products[
        products["StockCode"] == str(selected_code)
    ]

    if not selected_rows.empty:
        selected_name = str(
            selected_rows.iloc[0]["Description"]
        )

        location = assign_demo_location(selected_code)

        st.markdown("---")
        st.subheader("Product details")

        with st.container(border=True):
            st.markdown(f"### {escape(selected_name)}")
            st.caption(f"Stock code: {selected_code}")

            st.markdown("**Simulated store location**")

            floor_col, row_col, shelf_col = st.columns(3)

            floor_col.metric("Floor", location["Floor"])
            row_col.metric("Row", location["Row"])
            shelf_col.metric("Shelf", location["Shelf"])

            st.caption(
                "These locations are generated for the project demonstration. "
                "The source dataset does not contain actual shelf coordinates."
            )

            details_col, basket_col, map_col, close_col = st.columns(
                4,
                gap="small",
            )

            already_added = (
                selected_code in st.session_state.basket
            )

            with details_col:
                st.button(
                    "View catalogue",
                    key=f"detail_catalogue_{selected_code}",
                    use_container_width=True,
                    on_click=clear_selected_product,
                )

            with basket_col:
                st.button(
                    "✓ Added" if already_added else "+ Basket",
                    key=f"detail_add_{selected_code}",
                    disabled=already_added,
                    type="primary",
                    use_container_width=True,
                    on_click=add_to_basket,
                    args=(selected_code,),
                )

            with map_col:
                st.button(
                    "⌖ Locate on map",
                    key=f"detail_map_{selected_code}",
                    use_container_width=True,
                    on_click=locate_product,
                    args=(selected_code,),
                )

            with close_col:
                st.button(
                    "Close details",
                    key=f"detail_close_{selected_code}",
                    use_container_width=True,
                    on_click=clear_selected_product,
                )


# ============================================================
# DISCOVERY WHEN NO SEARCH HAS BEEN SUBMITTED
# ============================================================

if not current_query:
    st.markdown("---")
    st.subheader("Discover something")
    st.caption(
        "Explore products from the catalogue, or search above for a specific item."
    )

    sample = products.sample(
        n=min(6, len(products)),
        random_state=42,
    )

    columns = st.columns(3, gap="large")

    for column, (_, product) in zip(columns, sample.iterrows()):
        code = str(product["StockCode"])
        name = str(product["Description"])
        location = assign_demo_location(code)

        with column:
            with st.container(border=True):
                st.markdown(
                    f'<div class="findly-product-name">'
                    f'{escape(name)}</div>'
                    f'<div class="findly-product-code">'
                    f'Code: {escape(code)}</div>',
                    unsafe_allow_html=True,
                )

                st.caption(
                    f'{location["Floor"]} · {location["Row"]} · '
                    f'{location["Shelf"]}'
                )

                st.button(
                    "View details",
                    key=f"discover_details_{code}",
                    use_container_width=True,
                    on_click=select_product,
                    args=(code,),
                )

                st.button(
                    "⌖ Locate on map",
                    key=f"discover_locate_{code}",
                    use_container_width=True,
                    on_click=locate_product,
                    args=(code,),
                )

                already_added = code in st.session_state.basket

                st.button(
                    "✓ Added" if already_added else "+ Add to basket",
                    key=f"discover_add_{code}",
                    disabled=already_added,
                    type="primary",
                    use_container_width=True,
                    on_click=add_to_basket,
                    args=(code,),
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    f"Catalogue: {len(products):,} unique products. "
    "Product shelf assignments are simulated demonstration locations."
)