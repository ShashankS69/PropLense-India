"""
PropLens India — Tab 5: Rental Yield Comparator
=================================================
Compare real estate rental returns against alternative investment benchmarks.
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

# Note: utils.calculations.py has different param signatures;
# we always use the inline _calc_yc below for reliability.
try:
    from utils.calculations import calculate_irr as _utils_irr
except ImportError:
    _utils_irr = None


# ─── IRR engine (always defined) ──────────────────────────────────────────────

def _irr_newton(cashflows, guess=0.10, tol=1e-8, max_iter=200):
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


def _irr(cashflows):
    """Annualised IRR as decimal fraction. Uses numpy_financial if available."""
    try:
        import numpy_financial as npf
        return float(npf.irr(cashflows))
    except Exception:
        pass
    return _irr_newton(cashflows)


def calculate_irr(cashflows):
    """Return IRR as decimal fraction."""
    return _irr(cashflows)


# ─── Core yield model (always defined) ────────────────────────────────────────

def _calc_yc(
    property_price: float,
    monthly_rent: float,
    annual_escalation: float,
    annual_appreciation: float,
    holding_years: int,
    maintenance_vacancy_pct: float,
    tax_rate_pct: float,
) -> dict:
    """Inline rental yield comparison model — always available as fallback."""
    gross_yield = (monthly_rent * 12 / property_price) * 100
    net_yield = gross_yield * (1 - maintenance_vacancy_pct / 100) * (1 - tax_rate_pct / 100)
    cashflows = [-property_price]
    cumulative_rent = 0.0
    yearly_rents = []
    for yr in range(1, holding_years + 1):
        annual_rent = monthly_rent * 12 * (1 + annual_escalation / 100) ** (yr - 1)
        net_rent = annual_rent * (1 - maintenance_vacancy_pct / 100) * (1 - tax_rate_pct / 100)
        yearly_rents.append(net_rent)
        cumulative_rent += net_rent
        if yr < holding_years:
            cashflows.append(net_rent)
        else:
            sale_price = property_price * (1 + annual_appreciation / 100) ** holding_years
            cashflows.append(net_rent + sale_price)
    sale_price = property_price * (1 + annual_appreciation / 100) ** holding_years
    total_return = (sale_price + cumulative_rent - property_price) / property_price * 100
    annualized_irr = _irr(cashflows) * 100
    return {
        "gross_yield": gross_yield,
        "net_yield": net_yield,
        "total_return": total_return,
        "annualized_irr": annualized_irr,
        "yearly_rent_schedule": yearly_rents,
        "cumulative_rent": cumulative_rent,
        "sale_price": sale_price,
    }




def _sensitivity_matrix_inline(
    property_price, monthly_rent, annual_escalation,
    maintenance_vacancy_pct, tax_rate_pct,
    appreciation_range, holding_range,
) -> pd.DataFrame:
    """Standalone sensitivity matrix — always uses inline calc to avoid signature conflicts."""
    rows = []
    for appr in appreciation_range:
        row = {}
        for yrs in holding_range:
            cashflows = [-property_price]
            for yr in range(1, yrs + 1):
                annual_rent = monthly_rent * 12 * (1 + annual_escalation / 100) ** (yr - 1)
                net_rent = annual_rent * (1 - maintenance_vacancy_pct / 100) * (1 - tax_rate_pct / 100)
                if yr < yrs:
                    cashflows.append(net_rent)
                else:
                    sale_price = property_price * (1 + appr / 100) ** yrs
                    cashflows.append(net_rent + sale_price)
            try:
                r = float(np.irr(cashflows))
            except Exception:
                r = 0.0
                try:
                    rate = 0.1
                    for _ in range(200):
                        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
                        dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))
                        if abs(dnpv) < 1e-14:
                            break
                        rate -= npv / dnpv
                    r = rate
                except Exception:
                    pass
            row[f"{yrs} yrs"] = round(r * 100, 2)
        rows.append(row)
    return pd.DataFrame(rows, index=[f"{a}%" for a in appreciation_range])


# ─────────────────────────────────────────────
# TAB RENDERER
# ─────────────────────────────────────────────

def render(df):
    """Render the Rental Yield Comparator tab."""

    render_hero(
        "Rental Yield Comparator",
        "Compare real estate returns against alternative investment benchmarks",
    )

    # ── INPUT PANEL ──────────────────────────
    render_category_label("PROPERTY INPUTS")
    st.write("")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        property_price = st.number_input(
            "Property Price (₹)",
            min_value=500_000,
            max_value=500_000_000,
            value=10_000_000,
            step=500_000,
            format="%d",
            help="Total purchase price of the property",
        )
    with col_b:
        monthly_rent = st.number_input(
            "Expected Monthly Rent (₹)",
            min_value=1_000,
            max_value=5_000_000,
            value=25_000,
            step=1_000,
            format="%d",
        )
    with col_c:
        holding_years = st.slider(
            "Holding Period (years)",
            min_value=1,
            max_value=30,
            value=10,
        )

    col_d, col_e, col_f, col_g = st.columns(4)
    with col_d:
        annual_escalation = st.slider(
            "Rental Escalation (%/yr)", 0.0, 15.0, 5.0, 0.5,
        )
    with col_e:
        annual_appreciation = st.slider(
            "Property Appreciation (%/yr)", 0.0, 20.0, 6.0, 0.5,
        )
    with col_f:
        maintenance_vacancy = st.slider(
            "Maintenance & Vacancy (%)", 0.0, 30.0, 15.0, 1.0,
        )
    with col_g:
        tax_rate = st.slider(
            "Tax Rate (%)", 0.0, 40.0, 30.0, 1.0,
        )

    render_section_divider()

    # ── BENCHMARK INPUTS ─────────────────────
    render_category_label("BENCHMARK RETURNS (ANNUALISED)")
    st.write("")

    bm1, bm2, bm3, bm4 = st.columns(4)
    with bm1:
        fd_rate = st.number_input("Fixed Deposit (%)", 0.0, 20.0, 7.0, 0.5)
    with bm2:
        nifty_rate = st.number_input("Nifty 50 (%)", 0.0, 30.0, 12.0, 0.5)
    with bm3:
        gold_rate = st.number_input("Gold (%)", 0.0, 25.0, 8.0, 0.5)
    with bm4:
        debt_mf_rate = st.number_input("Debt Mutual Fund (%)", 0.0, 20.0, 7.5, 0.5)

    render_section_divider()

    # ── CALCULATIONS (always use inline model for consistency) ─────
    result = _calc_yc(
        property_price=property_price,
        monthly_rent=monthly_rent,
        annual_escalation=annual_escalation,
        annual_appreciation=annual_appreciation,
        holding_years=holding_years,
        maintenance_vacancy_pct=maintenance_vacancy,
        tax_rate_pct=tax_rate,
    )

    gross_yield = result.get("gross_yield", 0)
    net_yield = result.get("net_yield", 0)
    total_return = result.get("total_return", result.get("total_return_pct", 0))
    annualized_irr = result.get("annualized_irr", 0)

    # Benchmark compound returns (total %)
    benchmarks = {
        "Fixed Deposit": fd_rate,
        "Nifty 50": nifty_rate,
        "Gold": gold_rate,
        "Debt MF": debt_mf_rate,
    }

    # ── METRIC CARDS ─────────────────────────
    render_category_label("YIELD ANALYSIS")
    st.write("")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Gross Yield", format_pct(gross_yield))
    with m2:
        render_metric_card("Net Yield", format_pct(net_yield))
    with m3:
        render_metric_card(
            "Total Return",
            format_pct(total_return),
            delta=f"over {holding_years} yrs",
            delta_positive=total_return > 0,
        )
    with m4:
        irr_vs_fd = annualized_irr - fd_rate
        render_metric_card(
            "Annualised IRR",
            format_pct(annualized_irr),
            delta=f"{'+'if irr_vs_fd>=0 else ''}{irr_vs_fd:.0f} bps vs FD",
            delta_positive=irr_vs_fd >= 0,
        )

    st.write("")
    render_section_divider()

    # ── GROUPED BAR CHART: ANNUALISED RETURNS ─
    render_category_label("ANNUALISED RETURNS COMPARISON")
    st.write("")

    categories = ["Property"] + list(benchmarks.keys())
    # Post-tax annualised: property IRR already accounts for tax;
    # benchmarks — apply simplified post-tax
    post_tax_returns = [annualized_irr]
    for name, rate in benchmarks.items():
        # Simplified post-tax (interest income taxed, equity LTCG 10% above 1L simplified)
        if name in ("Fixed Deposit", "Debt MF"):
            post_tax_returns.append(rate * (1 - tax_rate / 100))
        else:
            post_tax_returns.append(rate * (1 - 0.10))  # LTCG 10%

    bar_colors = [
        COLORS["accent_gold"] if i == 0 else COLORS["chart_neutral"]
        for i in range(len(categories))
    ]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=categories,
        y=post_tax_returns,
        marker_color=bar_colors,
        text=[f"{v:.2f}%" for v in post_tax_returns],
        textposition="outside",
        textfont=dict(family=FONTS["mono"], size=12, color=COLORS["text_primary"]),
    ))
    fig_bar.update_layout(
        **get_plotly_layout(
            title="Post-Tax Annualised Returns",
            yaxis_title="Return (%)",
            height=420,
            showlegend=False,
        )
    )
    fig_bar.update_yaxes(gridcolor=COLORS["grid_line"])
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── CUMULATIVE WEALTH CHART ───────────────
    render_category_label("CUMULATIVE WEALTH GROWTH")
    st.write("")

    years_x = list(range(0, holding_years + 1))

    # Property cumulative wealth
    prop_wealth = [property_price]
    cum_rent = 0
    for yr in range(1, holding_years + 1):
        annual_rent = monthly_rent * 12 * (1 + annual_escalation / 100) ** (yr - 1)
        net_rent = annual_rent * (1 - maintenance_vacancy / 100) * (1 - tax_rate / 100)
        cum_rent += net_rent
        prop_value = property_price * (1 + annual_appreciation / 100) ** yr
        prop_wealth.append(prop_value + cum_rent)

    fig_wealth = go.Figure()
    fig_wealth.add_trace(go.Scatter(
        x=years_x, y=prop_wealth,
        name="Property",
        line=dict(color=COLORS["accent_gold"], width=3),
        fill="tozeroy",
        fillcolor="rgba(201, 169, 110, 0.08)",
    ))
    for name, rate in benchmarks.items():
        wealth = [property_price * (1 + rate / 100) ** yr for yr in years_x]
        fig_wealth.add_trace(go.Scatter(
            x=years_x, y=wealth,
            name=name,
            line=dict(width=2, dash="dot"),
        ))
    fig_wealth.update_layout(
        **get_plotly_layout(
            title=f"₹{property_price/1e7:.1f} Cr Invested — Wealth Over {holding_years} Years",
            xaxis_title="Year",
            yaxis_title="Portfolio Value (₹)",
            height=440,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
    )
    fig_wealth.update_yaxes(tickformat=",.0f", gridcolor=COLORS["grid_line"])
    st.plotly_chart(fig_wealth, use_container_width=True)

    render_section_divider()

    # ── VERDICT CARD ─────────────────────────
    irr_vs_fd_bps = round((annualized_irr - fd_rate) * 100)
    if irr_vs_fd_bps >= 0:
        verdict_word = "outperforms"
        verdict_detail = f"by {abs(irr_vs_fd_bps)} basis points"
    else:
        verdict_word = "underperforms"
        verdict_detail = f"by {abs(irr_vs_fd_bps)} basis points"

    best_alt = max(benchmarks, key=benchmarks.get)
    best_alt_rate = benchmarks[best_alt]
    alt_comparison = (
        f"Compared to the best-performing benchmark ({best_alt} at {best_alt_rate}%), "
        f"property IRR of {annualized_irr:.2f}% {'leads' if annualized_irr >= best_alt_rate else 'trails'} "
        f"by {abs(annualized_irr - best_alt_rate)*100:.0f} bps."
    )

    render_verdict(
        "Investment Verdict",
        f"Property {verdict_word} Fixed Deposit {verdict_detail} on a post-tax annualised basis. "
        f"{alt_comparison}"
    )

    st.write("")
    render_section_divider()

    # ── SENSITIVITY HEATMAP ──────────────────
    render_category_label("SENSITIVITY ANALYSIS — IRR (%) BY APPRECIATION & HOLDING PERIOD")
    st.write("")

    appreciation_range = [2, 4, 6, 8, 10, 12]
    holding_range = [3, 5, 7, 10, 15, 20]

    sens_df = _sensitivity_matrix_inline(
        property_price, monthly_rent, annual_escalation,
        maintenance_vacancy, tax_rate,
        appreciation_range, holding_range,
    )

    z_values = sens_df.values.tolist()
    x_labels = [str(c) for c in sens_df.columns]
    y_labels = [str(i) for i in sens_df.index]

    fig_heat = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        colorscale=[
            [0.0, COLORS["bg_primary"]],
            [0.3, COLORS["chart_neutral"]],
            [0.6, COLORS["accent_gold_dim"]],
            [1.0, COLORS["accent_gold"]],
        ],
        text=[[f"{v:.1f}%" for v in row] for row in z_values],
        texttemplate="%{text}",
        textfont=dict(family=FONTS["mono"], size=12, color=COLORS["text_primary"]),
        hovertemplate=(
            "Appreciation: %{y}<br>Holding: %{x}<br>IRR: %{z:.2f}%<extra></extra>"
        ),
        colorbar=dict(
            title=dict(text="IRR %", font=dict(color=COLORS["text_secondary"])),
            tickfont=dict(color=COLORS["text_secondary"]),
        ),
    ))
    fig_heat.update_layout(
        **get_plotly_layout(
            title="Annualised IRR — Sensitivity Grid",
            xaxis_title="Holding Period",
            yaxis_title="Annual Appreciation (%)",
            height=450,
        )
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── BOTTOM DETAIL: RENT SCHEDULE ─────────
    with st.expander("📋  Year-by-Year Net Rent Schedule"):
        schedule_data = {
            "Year": list(range(1, holding_years + 1)),
            "Net Annual Rent (₹)": [format_inr(r, compact=True) for r in result.get("yearly_rent_schedule", result.get("yearly_rents", []))],
            "Cumulative Rent (₹)": [
                format_inr(sum(result.get("yearly_rent_schedule", result.get("yearly_rents", []))[:i+1]), compact=True)
                for i in range(holding_years)
            ],
        }
        st.dataframe(
            pd.DataFrame(schedule_data).set_index("Year"),
            use_container_width=True,
        )
