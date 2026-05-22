"""
PropLens India — Tab 7: Listings Browser
==========================================
Search, filter, and export individual property listings.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dashboard.styles import *

import streamlit as st
import pandas as pd
from io import BytesIO


def _make_clickable(url):
    """Convert a URL string to a clickable HTML link."""
    if pd.isna(url) or not url:
        return "—"
    return f'<a href="{url}" target="_blank" style="color:{COLORS["accent_gold"]};">View →</a>'


def render(df: pd.DataFrame):
    """Render the Listings Browser tab."""

    render_hero(
        "Listings Browser",
        "Search, filter, and export individual property listings",
    )

    if df.empty:
        st.warning("No data available for the current filters.")
        return

    # ── Filter Row ──────────────────────────────────────────────
    render_category_label("Filters")

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)

    with f_col1:
        all_cities = sorted(df["city"].dropna().unique())
        sel_cities = st.multiselect(
            "City",
            options=all_cities,
            default=all_cities,
            key="browser_city",
        )

    with f_col2:
        # Filter micro-markets based on selected cities
        available_mms = sorted(
            df[df["city"].isin(sel_cities)]["micro_market"].dropna().unique()
        ) if sel_cities else sorted(df["micro_market"].dropna().unique())
        sel_mms = st.multiselect(
            "Micro-Market",
            options=available_mms,
            default=available_mms,
            key="browser_mm",
        )

    with f_col3:
        all_bhks = sorted(df["bhk"].dropna().unique(), key=lambda x: str(x))
        sel_bhks = st.multiselect(
            "BHK",
            options=all_bhks,
            default=all_bhks,
            key="browser_bhk",
        )

    with f_col4:
        all_sources = sorted(df["source"].dropna().unique())
        sel_sources = st.multiselect(
            "Source",
            options=all_sources,
            default=all_sources,
            key="browser_source",
        )

    # Price range slider
    price_col = df["sale_price"].dropna()
    if not price_col.empty:
        min_price = float(price_col.min())
        max_price = float(price_col.max())

        if min_price < max_price:
            price_range = st.slider(
                "Sale Price Range (₹)",
                min_value=min_price,
                max_value=max_price,
                value=(min_price, max_price),
                format="₹%.0f",
                key="browser_price_range",
            )
        else:
            price_range = (min_price, max_price)
    else:
        price_range = None

    render_section_divider()

    # ── Apply Filters ───────────────────────────────────────────
    filtered = df.copy()

    if sel_cities:
        filtered = filtered[filtered["city"].isin(sel_cities)]
    if sel_mms:
        filtered = filtered[filtered["micro_market"].isin(sel_mms)]
    if sel_bhks:
        filtered = filtered[filtered["bhk"].isin(sel_bhks)]
    if sel_sources:
        filtered = filtered[filtered["source"].isin(sel_sources)]
    if price_range:
        filtered = filtered[
            (filtered["sale_price"] >= price_range[0])
            & (filtered["sale_price"] <= price_range[1])
        ]

    # ── Results count ───────────────────────────────────────────
    total = len(filtered)

    st.markdown(
        f"<div style='display:flex; justify-content:space-between; "
        f"align-items:center; margin-bottom:1rem;'>"
        f"<span style='font-family:{FONTS['mono']};font-size:1rem;"
        f"color:{COLORS['accent_gold']};'>"
        f"{total:,} listings found</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.info("No listings match the selected filters. Try broadening your criteria.")
        return

    # ── Display columns ─────────────────────────────────────────
    display_cols = [
        "property_name", "bhk", "sale_price", "rent_price",
        "area_sqft", "price_per_sqft", "micro_market", "city",
        "source", "gross_rental_yield", "listing_url",
    ]
    # Only keep columns that actually exist in the data
    display_cols = [c for c in display_cols if c in filtered.columns]

    display_df = filtered[display_cols].copy()

    # Format listing_url as clickable links
    if "listing_url" in display_df.columns:
        display_df["listing_url"] = display_df["listing_url"].apply(_make_clickable)

    # Render with HTML links
    if "listing_url" in display_df.columns:
        st.markdown(
            display_df.to_html(escape=False, index=False),
            unsafe_allow_html=True,
        )
    else:
        st.dataframe(
            display_df,
            use_container_width=True,
            height=min(700, 40 + total * 35),
            hide_index=True,
        )

    render_section_divider()

    # ── Export to Excel ─────────────────────────────────────────
    render_category_label("Export")

    def _to_excel(dataframe: pd.DataFrame) -> bytes:
        """Convert DataFrame to Excel bytes using openpyxl."""
        output = BytesIO()
        # Use the raw data (not the HTML-formatted one) for export
        export_df = filtered[display_cols].copy() if display_cols else filtered.copy()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="PropLens Listings")
        return output.getvalue()

    excel_data = _to_excel(filtered)

    st.download_button(
        label="📥  EXPORT TO EXCEL",
        data=excel_data,
        file_name="proplens_listings_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="browser_export_btn",
    )

    # ── Summary stats ───────────────────────────────────────────
    render_category_label("Filtered Data Summary")

    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        render_metric_card("Total Listings", f"{total:,}")
    with s_col2:
        render_metric_card(
            "Median Sale Price",
            format_inr(filtered["sale_price"].median()),
        )
    with s_col3:
        render_metric_card(
            "Median Rent",
            format_inr(filtered["rent_price"].median()),
        )
    with s_col4:
        render_metric_card(
            "Median Yield",
            format_pct(filtered["gross_rental_yield"].median()),
        )
