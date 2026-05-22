"""
PropLens India — Tab 3: City-to-City Comparison
=================================================
Head-to-head micro-market analysis across all 15 locations.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dashboard.styles import *

import streamlit as st
import pandas as pd


def _compute_mm_stats(df: pd.DataFrame, micro_market: str) -> dict:
    """Compute aggregate statistics for a single micro-market."""
    mm_df = df[df["micro_market"] == micro_market]
    if mm_df.empty:
        return {
            "city": "—",
            "median_sale": None,
            "median_rent": None,
            "median_ppsf": None,
            "median_yield": None,
            "listing_count": 0,
            "source_breakdown": {},
        }
    return {
        "city": mm_df["city"].iloc[0],
        "median_sale": mm_df["sale_price"].median(),
        "median_rent": mm_df["rent_price"].median(),
        "median_ppsf": mm_df["price_per_sqft"].median(),
        "median_yield": mm_df["gross_rental_yield"].median(),
        "listing_count": len(mm_df),
        "source_breakdown": mm_df["source"].value_counts().to_dict(),
    }


def _render_comparison_metric(
    label: str,
    value_a: str,
    value_b: str,
    raw_a: float,
    raw_b: float,
    higher_is_better: bool = True,
):
    """Render a single comparison row with green highlight on the better side."""
    col_a, col_b = st.columns(2)

    a_better = False
    b_better = False
    if raw_a is not None and raw_b is not None:
        if higher_is_better:
            a_better = raw_a > raw_b
            b_better = raw_b > raw_a
        else:
            a_better = raw_a < raw_b
            b_better = raw_b < raw_a

    with col_a:
        css_class = "comparison-better" if a_better else "comparison-worse"
        st.markdown(
            f'<div class="{css_class}">'
            f'<div style="font-size:0.75rem;color:{COLORS["text_secondary"]};">{label}</div>'
            f'<div style="font-size:1.4rem;font-family:{FONTS["mono"]};">{value_a}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        css_class = "comparison-better" if b_better else "comparison-worse"
        st.markdown(
            f'<div class="{css_class}">'
            f'<div style="font-size:0.75rem;color:{COLORS["text_secondary"]};">{label}</div>'
            f'<div style="font-size:1.4rem;font-family:{FONTS["mono"]};">{value_b}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )


def render(df: pd.DataFrame):
    """Render the City-to-City Comparison tab."""

    render_hero(
        "City-to-City Comparison",
        "Head-to-head micro-market analysis across all 15 locations",
    )

    if df.empty:
        st.warning("No data available for the current filters.")
        return

    # ── Micro-market selection ──────────────────────────────────
    all_mms = sorted(df["micro_market"].dropna().unique())

    if len(all_mms) < 2:
        st.info("At least 2 micro-markets are required for comparison.")
        return

    col_sel_a, col_sel_b = st.columns(2)
    with col_sel_a:
        mm_a = st.selectbox(
            "Select Micro-Market A",
            options=all_mms,
            index=0,
            key="comparison_mm_a",
        )
    with col_sel_b:
        default_b = 1 if len(all_mms) > 1 else 0
        mm_b = st.selectbox(
            "Select Micro-Market B",
            options=all_mms,
            index=default_b,
            key="comparison_mm_b",
        )

    render_section_divider()

    # ── Compute stats ───────────────────────────────────────────
    stats_a = _compute_mm_stats(df, mm_a)
    stats_b = _compute_mm_stats(df, mm_b)

    # ── Header row ──────────────────────────────────────────────
    h_col_a, h_col_b = st.columns(2)
    with h_col_a:
        st.markdown(
            f"<h2 style='text-align:center;color:{COLORS['accent_gold']};'>"
            f"{mm_a}</h2>"
            f"<p style='text-align:center;color:{COLORS['text_secondary']};"
            f"font-size:0.85rem;'>{stats_a['city']}</p>",
            unsafe_allow_html=True,
        )
    with h_col_b:
        st.markdown(
            f"<h2 style='text-align:center;color:{COLORS['accent_gold']};'>"
            f"{mm_b}</h2>"
            f"<p style='text-align:center;color:{COLORS['text_secondary']};"
            f"font-size:0.85rem;'>{stats_b['city']}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Comparison metrics ──────────────────────────────────────
    render_category_label("Key Metrics")

    _render_comparison_metric(
        "Median Sale Price",
        format_inr(stats_a["median_sale"]),
        format_inr(stats_b["median_sale"]),
        stats_a["median_sale"],
        stats_b["median_sale"],
        higher_is_better=False,  # lower price = better for buyers
    )

    _render_comparison_metric(
        "Median Rent",
        format_inr(stats_a["median_rent"]),
        format_inr(stats_b["median_rent"]),
        stats_a["median_rent"],
        stats_b["median_rent"],
        higher_is_better=True,  # higher rent = better for investors
    )

    _render_comparison_metric(
        "Price per Sqft",
        format_inr(stats_a["median_ppsf"]),
        format_inr(stats_b["median_ppsf"]),
        stats_a["median_ppsf"],
        stats_b["median_ppsf"],
        higher_is_better=False,
    )

    _render_comparison_metric(
        "Gross Rental Yield",
        format_pct(stats_a["median_yield"]),
        format_pct(stats_b["median_yield"]),
        stats_a["median_yield"],
        stats_b["median_yield"],
        higher_is_better=True,
    )

    _render_comparison_metric(
        "Listing Count",
        str(stats_a["listing_count"]),
        str(stats_b["listing_count"]),
        stats_a["listing_count"],
        stats_b["listing_count"],
        higher_is_better=True,
    )

    render_section_divider()

    # ── Source Breakdown ────────────────────────────────────────
    render_category_label("Source Breakdown")

    src_col_a, src_col_b = st.columns(2)

    with src_col_a:
        if stats_a["source_breakdown"]:
            src_df_a = pd.DataFrame(
                list(stats_a["source_breakdown"].items()),
                columns=["Source", "Listings"],
            ).sort_values("Listings", ascending=False)
            st.dataframe(src_df_a, use_container_width=True, hide_index=True)
        else:
            st.caption("No source data available.")

    with src_col_b:
        if stats_b["source_breakdown"]:
            src_df_b = pd.DataFrame(
                list(stats_b["source_breakdown"].items()),
                columns=["Source", "Listings"],
            ).sort_values("Listings", ascending=False)
            st.dataframe(src_df_b, use_container_width=True, hide_index=True)
        else:
            st.caption("No source data available.")

    # ── Verdict ─────────────────────────────────────────────────
    if stats_a["median_yield"] is not None and stats_b["median_yield"] is not None:
        if stats_a["median_yield"] > stats_b["median_yield"]:
            winner, loser = mm_a, mm_b
            w_yield = stats_a["median_yield"]
        else:
            winner, loser = mm_b, mm_a
            w_yield = stats_b["median_yield"]

        render_verdict(
            "Comparison Verdict",
            f"{winner} offers a stronger rental yield at {format_pct(w_yield)}, "
            f"making it more attractive for income-focused investors compared to {loser}.",
        )
