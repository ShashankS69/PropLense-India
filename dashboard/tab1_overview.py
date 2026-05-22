"""
PropLens India — Tab 1: City Overview
=====================================
Aggregate market intelligence across 3 cities and 15 micro-markets.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dashboard.styles import *

import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render(df: pd.DataFrame):
    """Render the City Overview tab."""

    render_hero(
        "City Overview",
        "Aggregate market intelligence across 3 cities and 15 micro-markets",
    )

    if df.empty:
        st.warning("No data available for the current filters.")
        return

    # ── Per-city aggregate metrics ──────────────────────────────
    cities = sorted(df["city"].dropna().unique())

    render_category_label("Market Snapshot by City")

    cols = st.columns(len(cities) if cities else 1)
    city_stats = {}

    for i, city in enumerate(cities):
        city_df = df[df["city"] == city]
        median_sale = city_df["sale_price"].median()
        median_rent = city_df["rent_price"].median()
        median_ppsf = city_df["price_per_sqft"].median()
        city_stats[city] = {
            "median_sale": median_sale,
            "median_rent": median_rent,
            "median_ppsf": median_ppsf,
        }

        with cols[i]:
            st.markdown(
                f"<h3 style='color:{COLORS['accent_gold']};text-align:center;"
                f"font-family:{FONTS['heading']};margin-bottom:1rem;'>{city}</h3>",
                unsafe_allow_html=True,
            )
            render_metric_card("Median Sale Price", format_inr(median_sale))
            render_metric_card("Median Rent", format_inr(median_rent))
            render_metric_card("Median ₹/sqft", format_inr(median_ppsf))

    render_section_divider()

    # ── Comparative Bar Charts ──────────────────────────────────
    render_category_label("City-Level Comparison")

    if not city_stats:
        st.info("Not enough data to generate comparison charts.")
        return

    chart_cities = list(city_stats.keys())
    median_sales = [city_stats[c]["median_sale"] for c in chart_cities]
    median_rents = [city_stats[c]["median_rent"] for c in chart_cities]
    median_ppsf = [city_stats[c]["median_ppsf"] for c in chart_cities]

    col1, col2 = st.columns(2)

    # Chart 1: Median Sale Prices
    with col1:
        fig_sale = go.Figure(
            data=[
                go.Bar(
                    x=chart_cities,
                    y=median_sales,
                    marker_color=COLORS["chart_positive"],
                    text=[format_inr(v) for v in median_sales],
                    textposition="outside",
                    textfont=dict(color=COLORS["text_secondary"], size=11),
                )
            ]
        )
        fig_sale.update_layout(
            **get_plotly_layout(
                title="Median Sale Price",
                yaxis_title="Price (₹)",
                height=380,
            )
        )
        st.plotly_chart(fig_sale, use_container_width=True)

    # Chart 2: Median Rents
    with col2:
        fig_rent = go.Figure(
            data=[
                go.Bar(
                    x=chart_cities,
                    y=median_rents,
                    marker_color=COLORS["chart_accent2"],
                    text=[format_inr(v) for v in median_rents],
                    textposition="outside",
                    textfont=dict(color=COLORS["text_secondary"], size=11),
                )
            ]
        )
        fig_rent.update_layout(
            **get_plotly_layout(
                title="Median Rent",
                yaxis_title="Rent (₹/month)",
                height=380,
            )
        )
        st.plotly_chart(fig_rent, use_container_width=True)

    # Chart 3: Median Price per Sqft (full width)
    fig_ppsf = go.Figure(
        data=[
            go.Bar(
                x=chart_cities,
                y=median_ppsf,
                marker_color=COLORS["chart_accent3"],
                text=[format_inr(v) for v in median_ppsf],
                textposition="outside",
                textfont=dict(color=COLORS["text_secondary"], size=11),
            )
        ]
    )
    fig_ppsf.update_layout(
        **get_plotly_layout(
            title="Median Price per Sqft",
            yaxis_title="₹ / sqft",
            height=380,
        )
    )
    st.plotly_chart(fig_ppsf, use_container_width=True)

    render_section_divider()

    # ── Data Coverage Table ─────────────────────────────────────
    render_category_label("Data Coverage — Listings per Source per City")

    coverage = (
        df.groupby(["city", "source"])
        .size()
        .reset_index(name="listings")
    )
    coverage_pivot = coverage.pivot_table(
        index="source", columns="city", values="listings", fill_value=0, aggfunc="sum"
    )
    coverage_pivot["Total"] = coverage_pivot.sum(axis=1)
    coverage_pivot = coverage_pivot.sort_values("Total", ascending=False)

    st.dataframe(
        coverage_pivot,
        use_container_width=True,
        height=min(400, 40 + len(coverage_pivot) * 35),
    )

    # ── Verdict ─────────────────────────────────────────────────
    if city_stats:
        top_city = max(city_stats, key=lambda c: city_stats[c]["median_ppsf"] or 0)
        render_verdict(
            "Market Insight",
            f"{top_city} commands the highest median price per sqft at "
            f"{format_inr(city_stats[top_city]['median_ppsf'])}, "
            f"reflecting premium demand across its micro-markets.",
        )
