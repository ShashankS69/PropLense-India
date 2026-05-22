"""
PropLens India — Tab 4: Investor vs End-User Mode
===================================================
Tailored rankings for different buyer profiles.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dashboard.styles import *

import streamlit as st
import pandas as pd
import numpy as np


def _build_investor_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build investor-mode ranking table sorted by gross rental yield."""
    mm_stats = (
        df.groupby("micro_market")
        .agg(
            city=("city", "first"),
            gross_yield=("gross_rental_yield", "median"),
            price_per_sqft=("price_per_sqft", "median"),
            source_count=("source_count", "median"),
            listing_count=("property_name", "count"),
        )
        .reset_index()
    )

    # Annual income per ₹1 Cr invested = 1,00,00,000 × (yield / 100)
    mm_stats["annual_income_per_cr"] = mm_stats["gross_yield"].apply(
        lambda y: 1_00_00_000 * (y / 100) if pd.notna(y) else None
    )

    # Source reliability score: weighted by median source_count
    max_sc = mm_stats["source_count"].max()
    mm_stats["source_reliability"] = mm_stats["source_count"].apply(
        lambda sc: round((sc / max_sc) * 100, 1) if pd.notna(sc) and max_sc > 0 else 0
    )

    # Sort by gross yield descending
    mm_stats = mm_stats.sort_values("gross_yield", ascending=False).reset_index(drop=True)
    mm_stats.index += 1  # 1-based rank
    mm_stats.index.name = "Rank"

    # Format for display
    display = pd.DataFrame(
        {
            "Micro-Market": mm_stats["micro_market"].values,
            "City": mm_stats["city"].values,
            "Gross Yield %": mm_stats["gross_yield"].apply(
                lambda v: f"{v:.2f}%" if pd.notna(v) else "—"
            ).values,
            "Price/sqft": mm_stats["price_per_sqft"].apply(
                lambda v: format_inr(v) if pd.notna(v) else "—"
            ).values,
            "Annual Income per ₹1Cr": mm_stats["annual_income_per_cr"].apply(
                lambda v: format_inr(v, compact=True) if pd.notna(v) else "—"
            ).values,
            "Source Reliability": mm_stats["source_reliability"].apply(
                lambda v: f"{v}/100"
            ).values,
        },
        index=mm_stats.index,
    )
    return display


def _build_enduser_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build end-user mode ranking table sorted by affordability index."""
    mm_stats = (
        df.groupby("micro_market")
        .agg(
            city=("city", "first"),
            median_price=("sale_price", "median"),
            price_per_sqft=("price_per_sqft", "median"),
            affordability=("affordability_index", "median"),
            bhk_types=("bhk", lambda x: ", ".join(sorted(x.dropna().unique().astype(str)))),
            top_platform=("source", lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A"),
        )
        .reset_index()
    )

    # Sort by affordability index ascending (most affordable first)
    mm_stats = mm_stats.sort_values("affordability", ascending=True).reset_index(drop=True)
    mm_stats.index += 1
    mm_stats.index.name = "Rank"

    display = pd.DataFrame(
        {
            "Micro-Market": mm_stats["micro_market"].values,
            "City": mm_stats["city"].values,
            "Median Price": mm_stats["median_price"].apply(
                lambda v: format_inr(v) if pd.notna(v) else "—"
            ).values,
            "Price/sqft": mm_stats["price_per_sqft"].apply(
                lambda v: format_inr(v) if pd.notna(v) else "—"
            ).values,
            "BHK Availability": mm_stats["bhk_types"].values,
            "Top Platform": mm_stats["top_platform"].values,
        },
        index=mm_stats.index,
    )
    return display


def render(df: pd.DataFrame):
    """Render the Investor vs End-User Mode tab."""

    render_hero(
        "Investor vs End-User Mode",
        "Tailored rankings for different buyer profiles",
    )

    if df.empty:
        st.warning("No data available for the current filters.")
        return

    # ── Mode toggle ─────────────────────────────────────────────
    mode = st.radio(
        "Select Analysis Mode",
        options=["🏦 Investor", "🏠 End-User"],
        horizontal=True,
        key="buyer_mode_toggle",
    )

    render_section_divider()

    if "Investor" in mode:
        # ── INVESTOR MODE ───────────────────────────────────────
        render_category_label("Investor Rankings — By Gross Rental Yield")

        st.markdown(
            f"<p style='color:{COLORS['text_secondary']};font-size:0.85rem;"
            f"margin-bottom:1rem;'>"
            f"Micro-markets ranked by median gross rental yield. "
            f"Annual income is calculated per ₹1 Crore invested.</p>",
            unsafe_allow_html=True,
        )

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        overall_yield = df["gross_rental_yield"].median()
        top_mm = (
            df.groupby("micro_market")["gross_rental_yield"]
            .median()
            .idxmax()
        )
        top_yield = df.groupby("micro_market")["gross_rental_yield"].median().max()
        annual_income_top = 1_00_00_000 * (top_yield / 100) if pd.notna(top_yield) else None

        with col1:
            render_metric_card("Overall Median Yield", format_pct(overall_yield))
        with col2:
            render_metric_card("Top Performer", format_pct(top_yield), delta=top_mm, delta_positive=True)
        with col3:
            render_metric_card(
                "Annual Income / ₹1Cr",
                format_inr(annual_income_top),
                delta="Best micro-market",
                delta_positive=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        investor_df = _build_investor_table(df)
        st.dataframe(
            investor_df,
            use_container_width=True,
            height=min(600, 40 + len(investor_df) * 35),
        )

        # Verdict
        if top_mm:
            render_verdict(
                "Investor Insight",
                f"{top_mm} delivers the highest gross rental yield at "
                f"{format_pct(top_yield)}, translating to "
                f"{format_inr(annual_income_top)} annual income per ₹1Cr invested.",
            )

    else:
        # ── END-USER MODE ───────────────────────────────────────
        render_category_label("End-User Rankings — By Affordability Index")

        st.markdown(
            f"<p style='color:{COLORS['text_secondary']};font-size:0.85rem;"
            f"margin-bottom:1rem;'>"
            f"Micro-markets ranked by affordability index (lower = more affordable). "
            f"Ideal for home-buyers looking for value.</p>",
            unsafe_allow_html=True,
        )

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        median_price = df["sale_price"].median()
        most_affordable = (
            df.groupby("micro_market")["affordability_index"]
            .median()
            .idxmin()
        )
        aff_val = df.groupby("micro_market")["affordability_index"].median().min()
        total_bhk_types = df["bhk"].nunique()

        with col1:
            render_metric_card("Median Sale Price", format_inr(median_price))
        with col2:
            render_metric_card(
                "Most Affordable",
                f"{aff_val:.1f}" if pd.notna(aff_val) else "—",
                delta=most_affordable,
                delta_positive=True,
            )
        with col3:
            render_metric_card("BHK Types Available", str(total_bhk_types))

        st.markdown("<br>", unsafe_allow_html=True)

        enduser_df = _build_enduser_table(df)
        st.dataframe(
            enduser_df,
            use_container_width=True,
            height=min(600, 40 + len(enduser_df) * 35),
        )

        # Verdict
        if most_affordable:
            aff_price = df[df["micro_market"] == most_affordable]["sale_price"].median()
            render_verdict(
                "Buyer Insight",
                f"{most_affordable} is the most affordable micro-market with a "
                f"median price of {format_inr(aff_price)}, offering the best "
                f"value proposition for end-user home buyers.",
            )
