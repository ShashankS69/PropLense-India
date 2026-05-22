"""
PropLens India — Tab 6: Development Feasibility & IRR Calculator
================================================================
Institutional-grade project underwriting and IRR analysis for
real estate development projects.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dashboard.styles import *

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# CALCULATION FUNCTIONS (with fallback)
# ─────────────────────────────────────────────

# Note: utils.calculations.py has different param names (saleable_area_sqft, interest_rate_pct etc.)
# Tab6 always uses its inline functions to match the UI param names exactly.
try:
    from utils.calculations import calculate_irr as _utils_irr
except ImportError:
    _utils_irr = None

if False:  # keep block structure for fallback helpers below
    pass
else:

    def _calculate_irr_newton(cashflows, guess=0.10, tol=1e-8, max_iter=300):
        """Compute IRR via Newton-Raphson on the NPV polynomial."""
        rate = guess
        for _ in range(max_iter):
            npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
            dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))
            if abs(dnpv) < 1e-14:
                break
            rate -= npv / dnpv
            if abs(npv) < tol:
                break
        return rate

    def calculate_irr(cashflows):
        """Return annualised IRR (as %).  Falls back to Newton-Raphson."""
        try:
            return float(np.irr(cashflows)) * 100
        except (AttributeError, Exception):
            pass
        try:
            import numpy_financial as npf
            return float(npf.irr(cashflows)) * 100
        except (ImportError, Exception):
            pass
        return _calculate_irr_newton(cashflows) * 100

    def calculate_development_feasibility(
        land_cost_cr: float,
        construction_cost_sqft: float,
        saleable_area: float,
        sale_price_sqft: float,
        timeline_months: int,
        debt_pct: float,
        interest_rate: float,
        marketing_admin_pct: float,
        developer_margin_target: float,
    ) -> dict:
        """
        Full feasibility model returning cost components, margins, IRRs,
        and monthly cashflow arrays for project IRR and equity IRR.
        """
        land_cost = land_cost_cr * 1e7  # convert Cr to ₹
        construction_cost = construction_cost_sqft * saleable_area
        marketing_admin = (land_cost + construction_cost) * (marketing_admin_pct / 100)

        # Debt & interest (simple interest on average outstanding)
        debt_amount = (land_cost + construction_cost) * (debt_pct / 100)
        equity_amount = (land_cost + construction_cost) - debt_amount
        # Interest accrued over construction period (drawn uniformly)
        avg_outstanding = debt_amount / 2  # uniform drawdown average
        interest_cost = avg_outstanding * (interest_rate / 100) * (timeline_months / 12)

        total_project_cost = land_cost + construction_cost + marketing_admin + interest_cost
        revenue = sale_price_sqft * saleable_area
        gross_margin_pct = (revenue - total_project_cost) / revenue * 100 if revenue else 0
        net_margin_pct = gross_margin_pct - developer_margin_target
        profit = revenue - total_project_cost
        break_even_sqft = total_project_cost / saleable_area if saleable_area else 0

        # ── Monthly cashflows for Project IRR (unlevered) ──
        monthly_construction = construction_cost / timeline_months
        monthly_marketing = marketing_admin / timeline_months
        project_cashflows = [-land_cost]  # month 0
        for m in range(1, timeline_months + 1):
            outflow = -(monthly_construction + monthly_marketing)
            if m == timeline_months:
                outflow += revenue  # all revenue at completion
            project_cashflows.append(outflow)

        # Convert monthly IRR → annual
        monthly_irr_val = _calculate_irr_newton(project_cashflows, guess=0.01)
        project_irr = ((1 + monthly_irr_val) ** 12 - 1) * 100

        # ── Equity IRR (levered) ──
        # Equity outflows: land equity at t=0, monthly equity portion + interest
        equity_in_land = land_cost * (1 - debt_pct / 100)
        monthly_debt_drawdown = debt_amount / timeline_months
        monthly_interest = 0  # will compute per-period
        equity_cashflows = [-equity_in_land]  # month 0
        outstanding_debt = 0
        for m in range(1, timeline_months + 1):
            outstanding_debt += monthly_debt_drawdown
            m_interest = outstanding_debt * (interest_rate / 100) / 12
            equity_outflow = -(
                monthly_construction * (1 - debt_pct / 100)
                + monthly_marketing
                + m_interest
            )
            if m == timeline_months:
                equity_outflow += revenue - outstanding_debt  # repay debt from revenue
            equity_cashflows.append(equity_outflow)

        monthly_eq_irr = _calculate_irr_newton(equity_cashflows, guess=0.02)
        equity_irr = ((1 + monthly_eq_irr) ** 12 - 1) * 100

        return {
            "land_cost": land_cost,
            "construction_cost": construction_cost,
            "marketing_admin": marketing_admin,
            "interest_cost": interest_cost,
            "total_project_cost": total_project_cost,
            "revenue": revenue,
            "profit": profit,
            "gross_margin_pct": gross_margin_pct,
            "net_margin_pct": net_margin_pct,
            "project_irr": project_irr,
            "equity_irr": equity_irr,
            "break_even_sqft": break_even_sqft,
            "debt_amount": debt_amount,
            "equity_amount": equity_amount,
        }


# ─────────────────────────────────────────────
# TAB RENDERER
# ─────────────────────────────────────────────

def render(df):
    """Render the Development Feasibility & IRR Calculator tab."""

    render_hero(
        "Development Feasibility",
        "Institutional-grade project underwriting and IRR analysis",
    )

    # ── INPUT PANEL ──────────────────────────
    render_category_label("PROJECT PARAMETERS")
    st.write("")

    col1, col2, col3 = st.columns(3)
    with col1:
        land_cost_cr = st.number_input(
            "Land Cost (₹ Cr)",
            min_value=0.5,
            max_value=500.0,
            value=10.0,
            step=0.5,
            format="%.1f",
        )
    with col2:
        construction_cost_sqft = st.number_input(
            "Construction Cost (₹/sqft)",
            min_value=500,
            max_value=25000,
            value=4500,
            step=100,
        )
    with col3:
        saleable_area = st.number_input(
            "Saleable Area (sqft)",
            min_value=5000,
            max_value=5_000_000,
            value=100_000,
            step=5000,
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        sale_price_sqft = st.number_input(
            "Expected Sale Price (₹/sqft)",
            min_value=1000,
            max_value=100000,
            value=12000,
            step=500,
        )
    with col5:
        timeline_months = st.slider(
            "Launch → Completion (months)",
            min_value=12,
            max_value=60,
            value=36,
        )
    with col6:
        debt_pct = st.slider(
            "Debt Percentage (%)",
            min_value=0.0,
            max_value=80.0,
            value=60.0,
            step=5.0,
        )

    col7, col8, col9 = st.columns(3)
    with col7:
        interest_rate = st.slider(
            "Interest Rate on Debt (%)",
            min_value=5.0,
            max_value=18.0,
            value=12.0,
            step=0.5,
        )
    with col8:
        marketing_admin_pct = st.slider(
            "Marketing & Admin Cost (%)",
            min_value=0.0,
            max_value=20.0,
            value=8.0,
            step=1.0,
        )
    with col9:
        developer_margin_target = st.slider(
            "Developer Margin Target (%)",
            min_value=0.0,
            max_value=40.0,
            value=20.0,
            step=1.0,
        )

    render_section_divider()

    # ── CALCULATIONS ─────────────────────────
    result = calculate_development_feasibility(
        land_cost_cr=land_cost_cr,
        construction_cost_sqft=construction_cost_sqft,
        saleable_area=saleable_area,
        sale_price_sqft=sale_price_sqft,
        timeline_months=timeline_months,
        debt_pct=debt_pct,
        interest_rate=interest_rate,
        marketing_admin_pct=marketing_admin_pct,
        developer_margin_target=developer_margin_target,
    )

    # ── METRIC CARDS ─────────────────────────
    render_category_label("PROJECT SUMMARY")
    st.write("")

    m1, m2, m3 = st.columns(3)
    with m1:
        render_metric_card("Total Project Cost", format_inr(result["total_project_cost"]))
    with m2:
        render_metric_card("Total Revenue", format_inr(result["revenue"]))
    with m3:
        render_metric_card(
            "Gross Margin",
            format_pct(result["gross_margin_pct"]),
            delta=f"Net Margin: {result['net_margin_pct']:.1f}%",
            delta_positive=result["net_margin_pct"] > 0,
        )

    st.write("")

    m4, m5, m6 = st.columns(3)
    with m4:
        render_metric_card(
            "Project IRR (Unlevered)",
            format_pct(result["project_irr"]),
        )
    with m5:
        render_metric_card(
            "Equity IRR (Levered)",
            format_pct(result["equity_irr"]),
            delta=f"Leverage boost: {result['equity_irr'] - result['project_irr']:+.0f} bps",
            delta_positive=result["equity_irr"] >= result["project_irr"],
        )
    with m6:
        render_metric_card(
            "Break-even Price",
            f"₹{result['break_even_sqft']:,.0f}/sqft",
            delta=f"vs sale ₹{sale_price_sqft:,}/sqft",
            delta_positive=sale_price_sqft > result["break_even_sqft"],
        )

    st.write("")
    render_section_divider()

    # ── COST BREAKDOWN: STACKED BAR ──────────
    render_category_label("PROJECT COST BREAKDOWN")
    st.write("")

    cost_components = ["Land", "Construction", "Marketing & Admin", "Interest on Debt"]
    cost_values = [
        result["land_cost"],
        result["construction_cost"],
        result["marketing_admin"],
        result["interest_cost"],
    ]
    cost_colors = [
        COLORS["accent_gold"],
        COLORS["chart_neutral"],
        COLORS["chart_accent3"],
        COLORS["chart_negative"],
    ]

    fig_stack = go.Figure()
    for comp, val, clr in zip(cost_components, cost_values, cost_colors):
        fig_stack.add_trace(go.Bar(
            x=["Project Cost"],
            y=[val],
            name=comp,
            marker_color=clr,
            text=[format_inr(val)],
            textposition="inside",
            textfont=dict(family=FONTS["mono"], size=11, color=COLORS["text_primary"]),
            hovertemplate=f"{comp}: {format_inr(val)}<extra></extra>",
        ))
    fig_stack.update_layout(
        **get_plotly_layout(
            title="Cost Components",
            barmode="stack",
            height=380,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
    )
    fig_stack.update_yaxes(tickformat=",.0f", gridcolor=COLORS["grid_line"])
    st.plotly_chart(fig_stack, use_container_width=True)

    # ── WATERFALL CHART ──────────────────────
    render_category_label("COST → REVENUE → MARGIN WATERFALL")
    st.write("")

    waterfall_labels = cost_components + ["Total Cost", "Revenue", "Profit / (Loss)"]
    waterfall_values = cost_values + [
        result["total_project_cost"],
        result["revenue"],
        result["profit"],
    ]
    waterfall_measure = ["relative"] * 4 + ["total", "relative", "total"]

    wf_colors = []
    for m, v in zip(waterfall_measure, waterfall_values):
        if m == "total":
            wf_colors.append(COLORS["accent_gold"])
        elif v >= 0:
            wf_colors.append(COLORS["positive"])
        else:
            wf_colors.append(COLORS["negative"])

    fig_wf = go.Figure(go.Waterfall(
        x=waterfall_labels,
        y=[
            cost_values[0],
            cost_values[1],
            cost_values[2],
            cost_values[3],
            0,  # total marker
            result["revenue"],
            0,  # total marker
        ],
        measure=waterfall_measure,
        text=[format_inr(v) for v in waterfall_values],
        textposition="outside",
        textfont=dict(family=FONTS["mono"], size=11, color=COLORS["text_primary"]),
        connector_line_color=COLORS["grid_line"],
        increasing_marker_color=COLORS["positive"],
        decreasing_marker_color=COLORS["negative"],
        totals_marker_color=COLORS["accent_gold"],
        hovertemplate="%{x}: %{text}<extra></extra>",
    ))
    fig_wf.update_layout(
        **get_plotly_layout(
            title="Project Waterfall — Cost to Margin",
            height=440,
            showlegend=False,
        )
    )
    fig_wf.update_yaxes(tickformat=",.0f", gridcolor=COLORS["grid_line"])
    st.plotly_chart(fig_wf, use_container_width=True)

    render_section_divider()

    # ── SENSITIVITY HEATMAP ──────────────────
    render_category_label("SENSITIVITY ANALYSIS — PROJECT IRR (%)")
    st.write("")

    # 5×5 grid: construction cost rows × sale price columns
    base_cc = construction_cost_sqft
    base_sp = sale_price_sqft
    cc_range = [int(base_cc * f) for f in [0.80, 0.90, 1.00, 1.10, 1.20]]
    sp_range = [int(base_sp * f) for f in [0.80, 0.90, 1.00, 1.10, 1.20]]

    z_matrix = []
    for cc in cc_range:
        row = []
        for sp in sp_range:
            r = calculate_development_feasibility(
                land_cost_cr, cc, saleable_area, sp,
                timeline_months, debt_pct, interest_rate,
                marketing_admin_pct, developer_margin_target,
            )
            row.append(round(r["project_irr"], 1))
        z_matrix.append(row)

    fig_sens = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=[f"₹{sp:,}" for sp in sp_range],
        y=[f"₹{cc:,}" for cc in cc_range],
        colorscale=[
            [0.0, COLORS["chart_negative"]],
            [0.35, COLORS["bg_secondary"]],
            [0.6, COLORS["accent_gold_dim"]],
            [1.0, COLORS["accent_gold"]],
        ],
        text=[[f"{v:.1f}%" for v in row] for row in z_matrix],
        texttemplate="%{text}",
        textfont=dict(family=FONTS["mono"], size=13, color=COLORS["text_primary"]),
        hovertemplate=(
            "Sale Price: %{x}<br>Construction Cost: %{y}<br>Project IRR: %{z:.1f}%<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="IRR %", font=dict(color=COLORS["text_secondary"])),
            tickfont=dict(color=COLORS["text_secondary"]),
        ),
    ))
    fig_sens.update_layout(
        **get_plotly_layout(
            title="Project IRR — Sale Price vs Construction Cost",
            xaxis_title="Sale Price (₹/sqft)",
            yaxis_title="Construction Cost (₹/sqft)",
            height=460,
        )
    )
    st.plotly_chart(fig_sens, use_container_width=True)

    render_section_divider()

    # ── VERDICT CARD ─────────────────────────
    margin = result["gross_margin_pct"]
    pirr = result["project_irr"]
    eirr = result["equity_irr"]

    if margin >= developer_margin_target and pirr >= 15:
        feasibility = "FEASIBLE"
        color_word = "strong"
        detail = (
            f"Gross margin of {margin:.1f}% exceeds the {developer_margin_target:.0f}% target. "
            f"Project IRR of {pirr:.1f}% and Equity IRR of {eirr:.1f}% indicate attractive risk-adjusted returns."
        )
    elif margin >= developer_margin_target * 0.7:
        feasibility = "MARGINAL"
        color_word = "marginal"
        detail = (
            f"Gross margin of {margin:.1f}% is within reach of the {developer_margin_target:.0f}% target. "
            f"Consider optimising construction costs or improving realisations."
        )
    else:
        feasibility = "NOT FEASIBLE"
        color_word = "weak"
        detail = (
            f"Gross margin of {margin:.1f}% falls well below the {developer_margin_target:.0f}% target. "
            f"The project does not meet minimum return thresholds at current assumptions."
        )

    render_verdict(
        f"Feasibility Verdict: {feasibility}",
        f"{detail} Break-even sale price is ₹{result['break_even_sqft']:,.0f}/sqft "
        f"({(result['break_even_sqft']/sale_price_sqft - 1)*100:+.1f}% vs target sale price)."
    )

    st.write("")

    # ── DETAIL TABLE ─────────────────────────
    with st.expander("📋  Full Cost & Returns Summary"):
        summary_data = {
            "Component": [
                "Land Cost",
                "Construction Cost",
                "Marketing & Admin",
                "Interest on Debt",
                "─── Total Project Cost",
                "Revenue",
                "─── Profit / (Loss)",
                "",
                "Gross Margin %",
                "Net Margin %",
                "Project IRR (Unlevered)",
                "Equity IRR (Levered)",
                "Break-even ₹/sqft",
                "Debt Amount",
                "Equity Required",
            ],
            "Value": [
                format_inr(result["land_cost"]),
                format_inr(result["construction_cost"]),
                format_inr(result["marketing_admin"]),
                format_inr(result["interest_cost"]),
                format_inr(result["total_project_cost"]),
                format_inr(result["revenue"]),
                format_inr(result["profit"]),
                "",
                format_pct(result["gross_margin_pct"]),
                format_pct(result["net_margin_pct"]),
                format_pct(result["project_irr"]),
                format_pct(result["equity_irr"]),
                f"₹{result['break_even_sqft']:,.0f}",
                format_inr(result["debt_amount"]),
                format_inr(result["equity_amount"]),
            ],
        }
        st.dataframe(
            pd.DataFrame(summary_data).set_index("Component"),
            use_container_width=True,
        )
