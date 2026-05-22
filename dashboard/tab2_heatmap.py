"""
PropLens India — Tab 2: Rental Yield Heatmap
=============================================
Geographic distribution of rental yield across 15 micro-markets.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dashboard.styles import *

import streamlit as st
import pandas as pd

try:
    import folium
    try:
        from streamlit_folium import st_folium
    except ImportError:
        from streamlit_folium import folium_static as st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# ── Coordinate data ───────────────────────────────────────────
try:
    from utils.geocoding import MICRO_MARKET_COORDS
except ImportError:
    # Fallback hardcoded coordinates as (lat, lon) tuples — matches geocoding.py
    MICRO_MARKET_COORDS = {
        # Mumbai
        "Bandra": (19.0544, 72.8406),
        "Thane": (19.1972, 72.9722),
        "Chembur": (19.0510, 72.8940),
        "Andheri": (19.1190, 72.8470),
        "Powai": (19.1164, 72.9047),
        # Bengaluru
        "Whitefield": (12.9698, 77.7499),
        "Koramangala": (12.9259, 77.6229),
        "Sarjapur": (12.8576, 77.7834),
        "Hebbal": (13.0354, 77.5988),
        "Electronic City": (12.8399, 77.6770),
        # Pune
        "Baner": (18.5600, 73.7903),
        "Hinjewadi": (18.5936, 73.7301),
        "Kharadi": (18.5545, 73.9419),
        "Viman Nagar": (18.5666, 73.9154),
        "Wakad": (18.5993, 73.7625),
    }


def _yield_color(yield_val: float) -> str:
    """Return circle colour based on yield band."""
    if yield_val < 2.0:
        return "#A0616A"   # Red-ish (low yield)
    elif yield_val < 4.0:
        return "#D4A843"   # Yellow / gold (moderate)
    else:
        return "#6B8E7B"   # Green (strong yield)


def _top_source(x) -> str:
    """Return the most common source string safely (avoids lambda serialisation issues)."""
    mode = x.mode()
    return str(mode.iloc[0]) if not mode.empty else "N/A"


def render(df: pd.DataFrame):
    """Render the Rental Yield Heatmap tab."""

    render_hero(
        "Rental Yield Heatmap",
        "Geographic distribution of rental yield across 15 micro-markets",
    )

    if df.empty:
        st.warning("No data available for the current filters.")
        return

    if not FOLIUM_AVAILABLE:
        st.error(
            "📦 `folium` and `streamlit-folium` are required for this tab. "
            "Install them with: `pip install folium streamlit-folium`"
        )
        return

    # ── Compute micro-market statistics ─────────────────────────
    mm_stats = (
        df.groupby("micro_market")
        .agg(
            city=("city", "first"),
            median_yield=("gross_rental_yield", "median"),
            median_ppsf=("price_per_sqft", "median"),
            top_source=("source", _top_source),
            listing_count=("property_name", "count"),
        )
        .reset_index()
    )

    # ── Summary metrics ─────────────────────────────────────────
    render_category_label("Yield Overview")

    col1, col2, col3 = st.columns(3)
    overall_yield = df["gross_rental_yield"].median()
    best_mm = mm_stats.loc[mm_stats["median_yield"].idxmax()] if not mm_stats.empty else None
    worst_mm = mm_stats.loc[mm_stats["median_yield"].idxmin()] if not mm_stats.empty else None

    with col1:
        render_metric_card("Overall Median Yield", format_pct(overall_yield))
    with col2:
        if best_mm is not None:
            render_metric_card(
                "Highest Yield",
                format_pct(best_mm["median_yield"]),
                delta=best_mm["micro_market"],
                delta_positive=True,
            )
    with col3:
        if worst_mm is not None:
            render_metric_card(
                "Lowest Yield",
                format_pct(worst_mm["median_yield"]),
                delta=worst_mm["micro_market"],
                delta_positive=False,
            )

    render_section_divider()

    # ── Folium Map ──────────────────────────────────────────────
    render_category_label("Geographic Yield Distribution")

    m = folium.Map(
        location=[20.5937, 78.9629],
        zoom_start=5,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )

    for _, row in mm_stats.iterrows():
        mm_name = row["micro_market"]
        coords = MICRO_MARKET_COORDS.get(mm_name)
        if coords is None:
            continue

        # coords is a (lat, lon) tuple
        lat, lon = coords[0], coords[1]

        yield_val = row["median_yield"] if pd.notna(row["median_yield"]) else 0
        radius = max(yield_val * 8, 5)  # minimum visible radius
        color = _yield_color(yield_val)

        popup_html = f"""
        <div style="
            font-family: Inter, sans-serif;
            background: #1A1A1A;
            color: #F5F0EB;
            padding: 12px 16px;
            border-radius: 6px;
            border-top: 2px solid #C9A96E;
            min-width: 200px;
        ">
            <div style="font-size: 14px; font-weight: 600; color: #C9A96E;
                         margin-bottom: 6px;">{mm_name}</div>
            <div style="font-size: 11px; color: #8A8480; margin-bottom: 8px;">
                {row['city']}</div>
            <table style="width:100%; font-size: 12px; color: #F5F0EB;">
                <tr><td style="color:#8A8480;">Median Yield</td>
                    <td style="text-align:right; font-weight:600;">
                        {format_pct(yield_val)}</td></tr>
                <tr><td style="color:#8A8480;">Price/sqft</td>
                    <td style="text-align:right;">
                        {format_inr(row['median_ppsf'])}</td></tr>
                <tr><td style="color:#8A8480;">Top Source</td>
                    <td style="text-align:right;">{row['top_source']}</td></tr>
                <tr><td style="color:#8A8480;">Listings</td>
                    <td style="text-align:right;">{row['listing_count']}</td></tr>
            </table>
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{mm_name}: {format_pct(yield_val)}",
        ).add_to(m)

    # Fit bounds to all plotted markers — coords are (lat, lon) tuples
    plotted = [
        [MICRO_MARKET_COORDS[r["micro_market"]][0],
         MICRO_MARKET_COORDS[r["micro_market"]][1]]
        for _, r in mm_stats.iterrows()
        if r["micro_market"] in MICRO_MARKET_COORDS
    ]
    if plotted:
        m.fit_bounds(plotted)

    # Render wrapped in styled container
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    try:
        from streamlit_folium import folium_static
        folium_static(m, width=1200, height=550)
    except Exception:
        st_folium(m, width=None, height=550)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Legend ──────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="display:flex; gap:2rem; justify-content:center;
                    margin:1rem 0; font-family:{FONTS['body']}; font-size:0.8rem;">
            <span>
                <span style="display:inline-block; width:12px; height:12px;
                             border-radius:50%; background:#A0616A; margin-right:6px;
                             vertical-align:middle;"></span>
                <span style="color:{COLORS['text_secondary']};">Yield &lt; 2%</span>
            </span>
            <span>
                <span style="display:inline-block; width:12px; height:12px;
                             border-radius:50%; background:#D4A843; margin-right:6px;
                             vertical-align:middle;"></span>
                <span style="color:{COLORS['text_secondary']};">Yield 2–4%</span>
            </span>
            <span>
                <span style="display:inline-block; width:12px; height:12px;
                             border-radius:50%; background:#6B8E7B; margin-right:6px;
                             vertical-align:middle;"></span>
                <span style="color:{COLORS['text_secondary']};">Yield &gt; 4%</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Verdict ─────────────────────────────────────────────────
    if best_mm is not None:
        render_verdict(
            "Yield Insight",
            f"{best_mm['micro_market']} ({best_mm['city']}) leads with a median "
            f"gross rental yield of {format_pct(best_mm['median_yield'])}, "
            f"making it the strongest income-generating micro-market in the dataset.",
        )
