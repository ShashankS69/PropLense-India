"""
PropLens India — Main Dashboard Application
=============================================
Multi-city property intelligence dashboard with luxury dark UI.
Run: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import os
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dashboard.styles import (
    inject_styles,
    render_sidebar_brand,
    render_data_freshness,
    COLORS,
    FONTS,
)

# ─────────────────────────────────────────────
# PAGE CONFIG — must be first Streamlit call
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="PropLens India — Property Intelligence",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "PropLens India V2 — Multi-City Property Intelligence Dashboard",
    },
)

# ─────────────────────────────────────────────
# INJECT STYLES
# ─────────────────────────────────────────────

inject_styles()

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    """Load the master combined listings CSV."""
    data_path = os.path.join(PROJECT_ROOT, "data", "processed", "combined_listings.csv")

    if not os.path.exists(data_path):
        st.error(
            "📂 Data file not found. Please run the data pipeline first:\n\n"
            "```\npython -m scrapers.synthetic_data\n```"
        )
        st.stop()

    df = pd.read_csv(data_path)

    # Ensure required columns exist
    required_cols = [
        "property_name", "bhk", "sale_price", "rent_price",
        "area_sqft", "price_per_sqft", "micro_market", "city",
        "source", "listing_url",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing columns in data: {missing}")
        st.stop()

    # Compute derived columns if missing
    if "gross_rental_yield" not in df.columns:
        df["gross_rental_yield"] = (
            (df["rent_price"] * 12) / df["sale_price"] * 100
        ).round(2)

    if "price_per_sqft" not in df.columns or df["price_per_sqft"].isna().all():
        df["price_per_sqft"] = (df["sale_price"] / df["area_sqft"]).round(0)

    if "source_count" not in df.columns:
        df["source_count"] = 1

    if "affordability_index" not in df.columns:
        city_medians = df.groupby("city")["price_per_sqft"].transform("median")
        df["affordability_index"] = (df["price_per_sqft"] / city_medians * 100).round(1)

    return df


def get_data_freshness(df: pd.DataFrame) -> str:
    """Get data freshness date string."""
    data_path = os.path.join(PROJECT_ROOT, "data", "processed", "combined_listings.csv")
    if os.path.exists(data_path):
        import datetime
        mod_time = os.path.getmtime(data_path)
        dt = datetime.datetime.fromtimestamp(mod_time)
        return dt.strftime("%d %b %Y")
    return "N/A"


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Render the sidebar with brand, filters, and data freshness."""
    render_sidebar_brand()

    st.sidebar.markdown("---")

    # ── Filters ──
    st.sidebar.markdown(
        f'<p style="font-family: {FONTS["body"]}; color: {COLORS["text_secondary"]}; '
        f'font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; '
        f'margin-bottom: 0.5rem;">FILTERS</p>',
        unsafe_allow_html=True,
    )

    # City filter
    all_cities = sorted(df["city"].unique().tolist())
    selected_cities = st.sidebar.multiselect(
        "City",
        options=all_cities,
        default=all_cities,
        key="filter_city",
    )

    # BHK filter
    all_bhk = sorted(df["bhk"].unique().tolist())
    selected_bhk = st.sidebar.multiselect(
        "BHK Type",
        options=all_bhk,
        default=all_bhk,
        key="filter_bhk",
    )

    # Source filter
    all_sources = sorted(df["source"].unique().tolist())
    selected_sources = st.sidebar.multiselect(
        "Source Platform",
        options=all_sources,
        default=all_sources,
        key="filter_source",
    )

    # Apply filters
    filtered = df[
        (df["city"].isin(selected_cities if selected_cities else all_cities))
        & (df["bhk"].isin(selected_bhk if selected_bhk else all_bhk))
        & (df["source"].isin(selected_sources if selected_sources else all_sources))
    ]

    # ── Data Summary ──
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f'<p style="font-family: {FONTS["mono"]}; color: {COLORS["text_secondary"]}; '
        f'font-size: 0.75rem;">'
        f'<span style="color: {COLORS["accent_gold"]}; font-size: 1.2rem; font-weight: 600;">'
        f'{len(filtered):,}</span><br>'
        f'listings matched</p>',
        unsafe_allow_html=True,
    )

    # ── Data Freshness ──
    render_data_freshness(get_data_freshness(df))

    return filtered


# ─────────────────────────────────────────────
# TAB IMPORTS
# ─────────────────────────────────────────────

from dashboard import tab1_overview
from dashboard import tab2_heatmap
from dashboard import tab3_comparison
from dashboard import tab4_modes
from dashboard import tab5_yield_comparator
from dashboard import tab6_feasibility
from dashboard import tab7_browser


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    """Main application entry point."""
    # Load data
    df = load_data()

    # Render sidebar and get filtered data
    filtered_df = render_sidebar(df)

    # ── Tab Navigation ──
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "🏙  OVERVIEW",
        "🗺  YIELD MAP",
        "⚖  COMPARE",
        "👤  INVESTOR / USER",
        "📊  YIELD CALC",
        "🏗  FEASIBILITY",
        "📋  BROWSER",
    ])

    with tab1:
        tab1_overview.render(filtered_df)

    with tab2:
        tab2_heatmap.render(filtered_df)

    with tab3:
        tab3_comparison.render(filtered_df)

    with tab4:
        tab4_modes.render(filtered_df)

    with tab5:
        tab5_yield_comparator.render(filtered_df)

    with tab6:
        tab6_feasibility.render(filtered_df)

    with tab7:
        tab7_browser.render(filtered_df)


if __name__ == "__main__":
    main()
