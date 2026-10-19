
import streamlit as st

BACKGROUND = "#070b09"
SURFACE = "#101812"
BORDER = "#26392b"
ACCENT = "#7cf0a3"
TEXT = "#edf7ef"
MUTED = "#9aafa0"


def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
        --bg: #070b09;
        --surface: #101812;
        --border: #26392b;
        --accent: #7cf0a3;
        --text: #edf7ef;
        --muted: #9aafa0;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 85% 0%, #10251a 0%, transparent 40%),
            var(--bg);
        color: var(--text);
        font-family: 'DM Sans', sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #f1fff4 !important;
    }

    [data-testid="stSidebar"] {
        background: #0b120d;
        border-right: 1px solid #203126;
    }

    .stButton > button {
        border-radius: 10px;
        min-height: 40px;
        font-weight: 600;
        border: 1px solid var(--border);
        transition: border-color .15s ease, transform .15s ease;
    }

    .stButton > button:hover {
        border-color: var(--accent);
        transform: translateY(-1px);
    }

    .stButton > button[kind="primary"] {
        background: var(--accent);
        color: #071009;
        border-color: var(--accent);
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--border);
        border-radius: 16px;
        background: rgba(15, 23, 17, .65);
    }

    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px;
    }

    [data-testid="stMetricValue"] {
        color: var(--accent);
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
    }

    [data-testid="stTextInput"] input {
        border-radius: 10px;
    }

    hr {
        border-color: #243328;
    }

    .findly-hero {
        padding: 30px;
        border: 1px solid #23392b;
        border-radius: 22px;
        background:
            radial-gradient(circle at 95% 10%, rgba(124,240,163,.12), transparent 30%),
            linear-gradient(135deg, #12251a, #0a100c 75%);
        margin-bottom: 24px;
    }

    .findly-eyebrow {
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .findly-muted {
        color: var(--muted);
    }

    .findly-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px;
        min-height: 150px;
    }

    .findly-product-name {
        font-size: 16px;
        font-weight: 700;
        overflow-wrap: anywhere;
    }

    .findly-product-code {
        font-size: 12px;
        color: var(--muted);
        margin-top: 4px;
    }

    @media (max-width: 700px) {
        .findly-hero { padding: 20px; }
    }
    </style>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 16px">
          <div style="font-family:'Space Grotesk';font-size:25px;
                      font-weight:700;color:#7cf0a3">🟢 FINDLY</div>
          <div style="font-size:11px;letter-spacing:1.5px;
                      color:#9aafa0">SMART RETAIL EXPERIENCE</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if st.button("⌂  Home", key="shared_nav_home",
                     use_container_width=True):
            st.switch_page("app.py")

        if st.button("⌕  Product Discovery", key="shared_nav_search",
                     use_container_width=True):
            st.switch_page("pages/1_Product_Search.py")

        if st.button("▦  Interactive Store Map", key="shared_nav_map",
                     use_container_width=True):
            st.switch_page("pages/2_Store_Map.py")

        if st.button("🛒  Basket", key="shared_nav_basket",
                     use_container_width=True):
            st.switch_page("pages/3_Basket_Recommendations.py")

        st.divider()
        st.caption("Discover · Explore · Recommend")


def render_hero(eyebrow, title, description):
    st.markdown(f"""
    <div class="findly-hero">
      <div class="findly-eyebrow">{eyebrow}</div>
      <h1 style="font-size:36px;margin:10px 0">{title}</h1>
      <p class="findly-muted" style="font-size:16px;margin-bottom:0">
        {description}
      </p>
    </div>
    """, unsafe_allow_html=True)