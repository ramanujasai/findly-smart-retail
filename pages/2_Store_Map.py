
import hashlib
import html
from pathlib import Path

import pandas as pd
import streamlit as st

from ui.theme import apply_theme, render_sidebar, render_hero


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Store Map | Findly",
    page_icon="🗺️",
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
    "selected_shelf": None,
    "map_floor": "Floor 1",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# DATA
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
    """Assign a deterministic simulated location to a product."""

    digest = hashlib.sha256(
        str(stock_code).encode("utf-8")
    ).hexdigest()

    number = int(digest[:12], 16)

    return {
        "Floor": ["Floor 1", "Floor 2"][number % 2],
        "Row": f"Row {list('ABCDEFGH')[(number // 2) % 8]}",
        "Shelf": f"Shelf {((number // 16) % 12) + 1:02d}",
    }


@st.cache_data
def build_store_inventory(products_df):
    """Build the location table once for the loaded product catalogue."""

    inventory = products_df.copy()

    if inventory.empty:
        inventory["Floor"] = pd.Series(dtype=str)
        inventory["Row"] = pd.Series(dtype=str)
        inventory["Shelf"] = pd.Series(dtype=str)
        return inventory

    locations = pd.DataFrame(
        inventory["StockCode"].map(assign_demo_location).tolist(),
        index=inventory.index,
    )

    inventory[["Floor", "Row", "Shelf"]] = locations[
        ["Floor", "Row", "Shelf"]
    ]

    return inventory


products = load_products()

if products.empty:
    st.error(
        "No products were loaded. Check the processed dataset:\n\n"
        f"{DATA_FILE}"
    )
    st.stop()

inventory = build_store_inventory(products)


# ============================================================
# ACTIONS
# ============================================================

def select_shelf(floor, row, shelf):
    st.session_state.selected_shelf = (floor, row, shelf)


def open_product(code):
    st.session_state.selected_product = str(code)
    st.switch_page("pages/1_Product_Search.py")


def add_product_to_basket(code):
    code = str(code).strip()

    if code and code not in st.session_state.basket:
        st.session_state.basket.append(code)


# ============================================================
# HEADER
# ============================================================

render_hero(
    "Findly / Interactive Store Map",
    "Explore every aisle.",
    "Browse simulated store floors, inspect shelves, and locate products "
    "from the retail catalogue.",
)

st.info(
    "Store floor, row, and shelf assignments are simulated for this "
    "demonstration. They are not real store coordinates."
)


# ============================================================
# HANDLE PRODUCT LOCATION REQUESTS
# ============================================================

focus_code = st.session_state.get("map_focus")

if focus_code:
    focused_product = inventory[
        inventory["StockCode"] == str(focus_code)
    ]

    if not focused_product.empty:
        location = focused_product.iloc[0]

        # Set the floor before the floor selector is created.
        st.session_state.map_floor = location["Floor"]

        st.session_state.selected_shelf = (
            location["Floor"],
            location["Row"],
            location["Shelf"],
        )

    st.session_state.map_focus = None


# ============================================================
# FLOOR SELECTION
# ============================================================

floor = st.selectbox(
    "Select a floor",
    options=["Floor 1", "Floor 2"],
    key="map_floor",
)

floor_products = inventory[
    inventory["Floor"] == floor
].copy()

floor_count = len(floor_products)
row_count = floor_products["Row"].nunique()

metric1, metric2, metric3 = st.columns(3)

metric1.metric("Selected floor", floor)
metric2.metric("Unique products", f"{floor_count:,}")
metric3.metric("Rows with products", f"{row_count}/8")

if floor_count == 0:
    st.error(
        f"No products are assigned to {floor}. "
        "Check the product location calculation."
    )
    st.stop()


# ============================================================
# SHELF GRID
# ============================================================

st.markdown("---")
st.subheader("Shelf layout")
st.caption(
    "Select a shelf to see the products assigned to it. "
    "Each count represents unique products."
)

row_letters = list("ABCDEFGH")
shelves = [f"Shelf {n:02d}" for n in range(1, 13)]

# IMPORTANT FIX:
# The inventory stores row names as "Row A", "Row B", etc.
# We use those exact names when counting products.
shelf_counts = (
    floor_products.groupby(["Row", "Shelf"])["StockCode"]
    .nunique()
    .to_dict()
)

for letter in row_letters:
    row_name = f"Row {letter}"

    st.markdown(f"**{row_name}**")

    # Display 12 shelves as two groups of six.
    for start in range(0, len(shelves), 6):
        shelf_group = shelves[start:start + 6]
        columns = st.columns(6, gap="small")

        for column, shelf in zip(columns, shelf_group):
            count = shelf_counts.get((row_name, shelf), 0)

            is_selected = st.session_state.selected_shelf == (
                floor,
                row_name,
                shelf,
            )

            shelf_number = shelf.replace("Shelf ", "")

            label = (
                f"✓ {shelf_number} · {count} items"
                if is_selected
                else f"{shelf_number} · {count} items"
            )

            with column:
                st.button(
                    label,
                    key=f"map_{floor}_{letter}_{shelf}",
                    type="primary" if is_selected else "secondary",
                    help=(
                        f"{count} unique products assigned to "
                        f"{row_name}, {shelf}"
                    ),
                    use_container_width=True,
                    on_click=select_shelf,
                    args=(floor, row_name, shelf),
                )


# ============================================================
# SELECTED SHELF PRODUCTS
# ============================================================

selected_shelf = st.session_state.selected_shelf

if selected_shelf is not None and selected_shelf[0] == floor:
    _, selected_row, selected_shelf_name = selected_shelf

    shelf_products = floor_products[
        (floor_products["Row"] == selected_row)
        & (floor_products["Shelf"] == selected_shelf_name)
    ].copy()

    st.markdown("---")
    st.subheader(
        f"{floor} · {selected_row} · {selected_shelf_name}"
    )
    st.caption(
        f"{len(shelf_products):,} unique products assigned to this shelf"
    )

    if shelf_products.empty:
        st.info(
            "No products are assigned to this shelf in the simulated layout."
        )
    else:
        page_size = 30
        total_pages = max(
            1,
            (len(shelf_products) + page_size - 1) // page_size,
        )

        page_key = (
            f"map_page_{floor}_{selected_row}_{selected_shelf_name}"
        )

        # Reset pagination if necessary after changing the selected shelf.
        if st.session_state.get(page_key, 1) > total_pages:
            st.session_state[page_key] = 1

        page_number = st.number_input(
            "Product list page",
            min_value=1,
            max_value=total_pages,
            step=1,
            key=page_key,
        )

        start_index = (int(page_number) - 1) * page_size
        visible_products = shelf_products.iloc[
            start_index:start_index + page_size
        ]

        for _, product in visible_products.iterrows():
            code = str(product["StockCode"])
            name = str(product["Description"])

            with st.container(border=True):
                product_col, actions_col = st.columns(
                    [4, 2],
                    vertical_alignment="center",
                )

                with product_col:
                    st.markdown(
                        f'<div class="findly-product-name">'
                        f'{html.escape(name)}</div>'
                        f'<div class="findly-product-code">'
                        f'Code: {html.escape(code)}</div>',
                        unsafe_allow_html=True,
                    )

                with actions_col:
                    view_col, add_col = st.columns(2)

                    with view_col:
                        st.button(
                            "View",
                            key=f"view_map_{code}",
                            use_container_width=True,
                            on_click=open_product,
                            args=(code,),
                        )

                    with add_col:
                        already_added = (
                            code in st.session_state.basket
                        )

                        st.button(
                            "✓ Added" if already_added else "+ Basket",
                            key=f"add_map_{code}",
                            disabled=already_added,
                            use_container_width=True,
                            on_click=add_product_to_basket,
                            args=(code,),
                        )

        end_index = min(
            start_index + page_size,
            len(shelf_products),
        )

        st.caption(
            f"Showing {start_index + 1}–{end_index} "
            f"of {len(shelf_products)} products."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption(
    f"Catalogue: {len(products):,} unique products. "
    "Shelf assignments are simulated and deterministic."
)