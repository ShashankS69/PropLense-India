"""
PropLens India — Financial Calculations
========================================
Institutional-grade financial calculation functions for:
- Rental yield analysis
- Investment return comparison
- Development feasibility & IRR
"""

import numpy as np
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────
# RENTAL YIELD CALCULATIONS
# ─────────────────────────────────────────────

def gross_rental_yield(annual_rent: float, sale_price: float) -> float:
    """
    Calculate gross rental yield.

    Args:
        annual_rent: Total annual rent income (₹)
        sale_price: Property purchase price (₹)

    Returns:
        Gross rental yield as percentage
    """
    if sale_price <= 0:
        return 0.0
    return (annual_rent / sale_price) * 100


def net_rental_yield(
    annual_rent: float,
    sale_price: float,
    maintenance_pct: float = 10.0,
    vacancy_pct: float = 5.0,
    tax_rate_pct: float = 30.0,
) -> float:
    """
    Calculate net rental yield after deductions.

    Args:
        annual_rent: Total annual rent income (₹)
        sale_price: Property purchase price (₹)
        maintenance_pct: Maintenance + repairs as % of annual rent
        vacancy_pct: Expected vacancy as % of annual rent
        tax_rate_pct: Income tax rate on rental income

    Returns:
        Net rental yield as percentage
    """
    if sale_price <= 0 or annual_rent <= 0:
        return 0.0

    net_rent = annual_rent * (1 - maintenance_pct / 100) * (1 - vacancy_pct / 100)
    after_tax = net_rent * (1 - tax_rate_pct / 100)
    return (after_tax / sale_price) * 100


def affordability_index(price_per_sqft: float, city_median_price_per_sqft: float) -> float:
    """
    Calculate affordability index (lower = more affordable).

    Args:
        price_per_sqft: Property's price per sqft
        city_median_price_per_sqft: Median price per sqft for the city

    Returns:
        Affordability index (100 = at city median)
    """
    if city_median_price_per_sqft <= 0:
        return 100.0
    return (price_per_sqft / city_median_price_per_sqft) * 100


# ─────────────────────────────────────────────
# IRR & NPV CALCULATIONS
# ─────────────────────────────────────────────

def calculate_irr(cashflows: List[float], guess: float = 0.1, max_iter: int = 1000, tol: float = 1e-8) -> float:
    """
    Calculate Internal Rate of Return using Newton-Raphson method.

    Args:
        cashflows: List of cash flows (negative = outflow, positive = inflow)
        guess: Initial IRR guess
        max_iter: Maximum iterations
        tol: Convergence tolerance

    Returns:
        IRR as a decimal (e.g., 0.12 for 12%). Returns NaN if not converging.
    """
    if not cashflows or len(cashflows) < 2:
        return float('nan')

    rate = guess
    for _ in range(max_iter):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
        dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))

        if abs(dnpv) < 1e-12:
            break

        new_rate = rate - npv / dnpv

        if abs(new_rate - rate) < tol:
            return new_rate

        rate = new_rate

    # Fallback: try numpy if Newton-Raphson fails
    try:
        return float(np.irr(cashflows))
    except (AttributeError, ValueError):
        # np.irr removed in newer numpy, use npf
        try:
            import numpy_financial as npf
            return float(npf.irr(cashflows))
        except ImportError:
            pass

    return float('nan')


def calculate_npv(cashflows: List[float], rate: float) -> float:
    """
    Calculate Net Present Value.

    Args:
        cashflows: List of cash flows
        rate: Discount rate as decimal

    Returns:
        Net Present Value
    """
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))


# ─────────────────────────────────────────────
# RENTAL YIELD vs ALTERNATIVE RETURNS
# ─────────────────────────────────────────────

def calculate_rental_yield_comparison(
    property_price: float,
    monthly_rent: float,
    annual_escalation_pct: float = 5.0,
    annual_appreciation_pct: float = 6.0,
    holding_years: int = 10,
    maintenance_vacancy_pct: float = 15.0,
    tax_rate_pct: float = 30.0,
    benchmarks: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Compare real estate investment returns against alternative benchmarks.

    Args:
        property_price: Purchase price (₹)
        monthly_rent: Expected monthly rent (₹)
        annual_escalation_pct: Annual rent increase (%)
        annual_appreciation_pct: Annual property value appreciation (%)
        holding_years: Investment horizon in years
        maintenance_vacancy_pct: Total deductions as % of rent
        tax_rate_pct: Income tax rate on rental income
        benchmarks: Dict of benchmark name → annual return %

    Returns:
        Dict with gross_yield, net_yield, total_return, annualized_irr,
        benchmark_returns, yearly_cashflows, verdict
    """
    if benchmarks is None:
        benchmarks = {
            "Fixed Deposit": 7.0,
            "Nifty 50": 12.0,
            "Gold": 8.0,
            "Debt Mutual Fund": 7.5,
        }

    # Gross and net yield
    annual_rent = monthly_rent * 12
    g_yield = gross_rental_yield(annual_rent, property_price)
    n_yield = net_rental_yield(annual_rent, property_price, maintenance_vacancy_pct, 0, tax_rate_pct)

    # Build yearly cash flows for IRR
    cashflows = [-property_price]
    yearly_rents = []
    current_annual_rent = annual_rent

    for year in range(1, holding_years + 1):
        net_rent = current_annual_rent * (1 - maintenance_vacancy_pct / 100) * (1 - tax_rate_pct / 100)
        yearly_rents.append(net_rent)

        if year < holding_years:
            cashflows.append(net_rent)
        else:
            # Final year: rent + sale proceeds
            sale_price = property_price * (1 + annual_appreciation_pct / 100) ** holding_years
            # Capital gains tax (simplified: 20% LTCG after indexation)
            capital_gain = sale_price - property_price
            ltcg_tax = max(0, capital_gain * 0.125)  # 12.5% LTCG post-2024 budget
            net_sale = sale_price - ltcg_tax
            cashflows.append(net_rent + net_sale)

        current_annual_rent *= (1 + annual_escalation_pct / 100)

    # Property IRR
    irr = calculate_irr(cashflows)
    annualized_irr = irr * 100 if not np.isnan(irr) else 0.0

    # Total return
    total_invested = property_price
    total_rent_received = sum(yearly_rents)
    final_property_value = property_price * (1 + annual_appreciation_pct / 100) ** holding_years
    total_return_value = total_rent_received + final_property_value - total_invested
    total_return_pct = (total_return_value / total_invested) * 100

    # Benchmark returns (compound interest)
    benchmark_returns = {}
    for name, annual_return in benchmarks.items():
        final_value = property_price * (1 + annual_return / 100) ** holding_years
        # Post-tax (simplified): FD taxed at slab, equity at 12.5% LTCG, gold at 12.5%
        tax_rates = {"Fixed Deposit": 0.30, "Nifty 50": 0.125, "Gold": 0.125, "Debt Mutual Fund": 0.20}
        gain = final_value - property_price
        tax = gain * tax_rates.get(name, 0.20)
        post_tax_value = final_value - tax
        post_tax_return = ((post_tax_value / property_price) ** (1 / holding_years) - 1) * 100
        benchmark_returns[name] = {
            "annual_return": annual_return,
            "final_value": final_value,
            "post_tax_value": post_tax_value,
            "post_tax_annualized": post_tax_return,
        }

    # Verdict
    fd_return = benchmark_returns.get("Fixed Deposit", {}).get("post_tax_annualized", 7.0)
    diff_bps = round((annualized_irr - fd_return) * 100)
    if diff_bps > 0:
        verdict = f"Property outperforms Fixed Deposit by {diff_bps} basis points"
    elif diff_bps < 0:
        verdict = f"Property underperforms Fixed Deposit by {abs(diff_bps)} basis points"
    else:
        verdict = "Property returns are at par with Fixed Deposit"

    return {
        "gross_yield": g_yield,
        "net_yield": n_yield,
        "total_return_pct": total_return_pct,
        "annualized_irr": annualized_irr,
        "cashflows": cashflows,
        "yearly_rents": yearly_rents,
        "final_property_value": final_property_value,
        "benchmark_returns": benchmark_returns,
        "verdict": verdict,
    }


def calculate_yield_sensitivity(
    property_price: float,
    monthly_rent: float,
    holding_years_range: List[int],
    appreciation_range: List[float],
    maintenance_vacancy_pct: float = 15.0,
    tax_rate_pct: float = 30.0,
    annual_escalation_pct: float = 5.0,
) -> np.ndarray:
    """
    Generate IRR sensitivity matrix across holding periods and appreciation rates.

    Args:
        property_price: Purchase price
        monthly_rent: Monthly rent
        holding_years_range: List of holding periods to test
        appreciation_range: List of appreciation rates to test
        maintenance_vacancy_pct: Deductions %
        tax_rate_pct: Tax rate %
        annual_escalation_pct: Rent escalation %

    Returns:
        2D numpy array of IRR values (rows=appreciation, cols=holding_years)
    """
    matrix = np.zeros((len(appreciation_range), len(holding_years_range)))

    for i, appreciation in enumerate(appreciation_range):
        for j, years in enumerate(holding_years_range):
            result = calculate_rental_yield_comparison(
                property_price=property_price,
                monthly_rent=monthly_rent,
                annual_escalation_pct=annual_escalation_pct,
                annual_appreciation_pct=appreciation,
                holding_years=years,
                maintenance_vacancy_pct=maintenance_vacancy_pct,
                tax_rate_pct=tax_rate_pct,
            )
            matrix[i, j] = result["annualized_irr"]

    return matrix


# ─────────────────────────────────────────────
# DEVELOPMENT FEASIBILITY & IRR
# ─────────────────────────────────────────────

def calculate_development_feasibility(
    land_cost_cr: float = 10.0,
    construction_cost_sqft: float = 4500.0,
    saleable_area_sqft: float = 100000.0,
    sale_price_sqft: float = 12000.0,
    timeline_months: int = 36,
    debt_pct: float = 60.0,
    interest_rate_pct: float = 12.0,
    marketing_admin_pct: float = 8.0,
    developer_margin_target_pct: float = 20.0,
) -> Dict:
    """
    Calculate development project feasibility and returns.

    Args:
        land_cost_cr: Land acquisition cost in ₹ Crores
        construction_cost_sqft: Construction cost per sqft (₹)
        saleable_area_sqft: Total saleable area in sqft
        sale_price_sqft: Expected sale price per sqft (₹)
        timeline_months: Project timeline in months
        debt_pct: Debt as % of total project cost
        interest_rate_pct: Annual interest rate on construction finance
        marketing_admin_pct: Marketing & admin as % of revenue
        developer_margin_target_pct: Target developer margin (%)

    Returns:
        Dict with cost breakdown, margins, IRRs, break-even price, cash flows
    """
    # Cost calculations
    land_cost = land_cost_cr * 1e7  # Convert Cr to ₹
    construction_cost = construction_cost_sqft * saleable_area_sqft
    revenue = sale_price_sqft * saleable_area_sqft
    marketing_admin_cost = revenue * (marketing_admin_pct / 100)

    # Interest on construction finance
    # Simplified: average outstanding = 50% of construction cost over timeline
    total_project_cost_excl_interest = land_cost + construction_cost + marketing_admin_cost
    debt_amount = total_project_cost_excl_interest * (debt_pct / 100)
    equity_amount = total_project_cost_excl_interest * (1 - debt_pct / 100)
    avg_outstanding_debt = debt_amount * 0.5  # Average over drawdown period
    interest_cost = avg_outstanding_debt * (interest_rate_pct / 100) * (timeline_months / 12)

    total_project_cost = total_project_cost_excl_interest + interest_cost

    # Margins
    gross_profit = revenue - total_project_cost
    gross_margin_pct = (gross_profit / revenue) * 100 if revenue > 0 else 0
    net_margin_pct = gross_margin_pct - developer_margin_target_pct

    # Break-even sale price
    break_even_price_sqft = total_project_cost / saleable_area_sqft if saleable_area_sqft > 0 else 0

    # Project IRR (unlevered)
    # Cash flows: land at month 0, construction spread evenly, revenue at completion
    monthly_construction = construction_cost / timeline_months
    monthly_marketing = marketing_admin_cost / timeline_months

    project_cashflows = []
    # Month 0: land cost
    project_cashflows.append(-land_cost)
    # Months 1 to timeline-1: construction + marketing
    for m in range(1, timeline_months):
        project_cashflows.append(-(monthly_construction + monthly_marketing))
    # Final month: last construction payment + revenue
    project_cashflows.append(-(monthly_construction + monthly_marketing) + revenue)

    # Convert monthly IRR to annual
    monthly_irr = calculate_irr(project_cashflows, guess=0.02)
    project_irr = ((1 + monthly_irr) ** 12 - 1) * 100 if not np.isnan(monthly_irr) else 0.0

    # Equity IRR (levered)
    # Equity cash flows: only equity portion of costs, plus interest payments
    monthly_debt_draw = (debt_amount / timeline_months)
    monthly_interest = 0  # Interest accrued, paid at end

    equity_cashflows = []
    # Month 0: equity portion of land cost
    equity_land = land_cost * (1 - debt_pct / 100)
    equity_cashflows.append(-equity_land)

    # Monthly: equity portion of construction + marketing
    monthly_equity_outflow = (monthly_construction + monthly_marketing) * (1 - debt_pct / 100)
    for m in range(1, timeline_months):
        equity_cashflows.append(-monthly_equity_outflow)

    # Final month: last equity payment + revenue - debt repayment - interest
    equity_cashflows.append(-monthly_equity_outflow + revenue - debt_amount - interest_cost)

    monthly_equity_irr = calculate_irr(equity_cashflows, guess=0.03)
    equity_irr = ((1 + monthly_equity_irr) ** 12 - 1) * 100 if not np.isnan(monthly_equity_irr) else 0.0

    return {
        "cost_breakdown": {
            "land_cost": land_cost,
            "construction_cost": construction_cost,
            "marketing_admin_cost": marketing_admin_cost,
            "interest_cost": interest_cost,
            "total_project_cost": total_project_cost,
        },
        "revenue": revenue,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "net_margin_pct": net_margin_pct,
        "project_irr": project_irr,
        "equity_irr": equity_irr,
        "break_even_price_sqft": break_even_price_sqft,
        "debt_amount": debt_amount,
        "equity_amount": equity_amount,
        "interest_cost": interest_cost,
        "project_cashflows": project_cashflows,
        "equity_cashflows": equity_cashflows,
    }


def calculate_sensitivity_matrix(
    base_params: Dict,
    sale_price_range: List[float],
    construction_cost_range: List[float],
) -> np.ndarray:
    """
    Generate IRR sensitivity matrix across sale price and construction cost.

    Args:
        base_params: Base parameters dict for calculate_development_feasibility
        sale_price_range: List of sale prices per sqft to test
        construction_cost_range: List of construction costs per sqft to test

    Returns:
        2D numpy array of Project IRR values (rows=construction_cost, cols=sale_price)
    """
    matrix = np.zeros((len(construction_cost_range), len(sale_price_range)))

    for i, cc in enumerate(construction_cost_range):
        for j, sp in enumerate(sale_price_range):
            params = base_params.copy()
            params["construction_cost_sqft"] = cc
            params["sale_price_sqft"] = sp
            result = calculate_development_feasibility(**params)
            matrix[i, j] = result["project_irr"]

    return matrix
