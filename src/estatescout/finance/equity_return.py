"""Eigenkapitalrendite — first-year cash-on-cash return of a financed buy-to-let.

    loan                 = purchase_price + ancillary_costs − equity
    annual_debt_service  = loan · (annual_rate + initial_repayment)
    net_operating_income = annual cold rent − annual operating costs
    cashflow_before_tax  = net_operating_income − annual_debt_service
    cash_on_cash         = cashflow_before_tax / equity

The unlevered net yield (``yield_metrics``) says what the object earns; cash-on-cash says
what the invested equity earns after debt service — the number a leveraged investor actually
optimizes. Year-1, before tax (the annuity payment is constant, its interest/principal split
shifts over time — see ``annuity``). Pure and deterministic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EquityReturn:
    loan: float
    annual_debt_service: float
    net_operating_income: float
    cashflow_before_tax: float
    cash_on_cash: float


def equity_return(
    purchase_price: float,
    monthly_cold_rent: float,
    equity: float,
    annual_rate: float,
    initial_repayment: float,
    *,
    ancillary_costs: float = 0.0,
    annual_operating_costs: float = 0.0,
) -> EquityReturn:
    """First-year cash-on-cash return. Rates are fractions (0.036 = 3.6 %)."""
    if purchase_price <= 0:
        raise ValueError("purchase_price must be > 0")
    if monthly_cold_rent <= 0:
        raise ValueError("monthly_cold_rent must be > 0")
    if equity <= 0:
        raise ValueError("equity must be > 0 (cash-on-cash needs invested equity)")
    if ancillary_costs < 0:
        raise ValueError("ancillary_costs must be >= 0")
    if annual_operating_costs < 0:
        raise ValueError("annual_operating_costs must be >= 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")
    if annual_rate > 0.25:
        raise ValueError(
            "annual_rate is a fraction (0.036 = 3.6 %) — a value above 0.25 looks like percent"
        )
    if initial_repayment <= 0:
        raise ValueError("initial_repayment must be > 0")
    if initial_repayment > 0.2:
        raise ValueError(
            "initial_repayment is a fraction (0.02 = 2 %) — a value above 0.2 looks like percent"
        )

    total_investment = purchase_price + ancillary_costs
    if equity > total_investment:
        raise ValueError("equity exceeds the total investment — nothing to finance")

    loan = total_investment - equity
    annual_debt_service = loan * (annual_rate + initial_repayment)
    net_operating_income = monthly_cold_rent * 12.0 - annual_operating_costs
    cashflow_before_tax = net_operating_income - annual_debt_service
    return EquityReturn(
        loan=loan,
        annual_debt_service=annual_debt_service,
        net_operating_income=net_operating_income,
        cashflow_before_tax=cashflow_before_tax,
        cash_on_cash=cashflow_before_tax / equity,
    )
