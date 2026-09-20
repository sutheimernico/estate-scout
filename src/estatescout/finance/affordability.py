"""Leistbarkeit — how expensive a property you can afford.

Works backwards from a monthly-payment budget (a rule-of-thumb share of net household income)
through the loan to the maximum purchase price, accounting for the fact that ancillary costs
(Kaufnebenkosten) also have to be covered:

    max_loan  = budget · 12 / (annual_rate + initial_repayment)
    max_price = (max_loan + equity) / (1 + ancillary_quota)

Pure and deterministic. The rule-of-thumb income share and rates come from the config.
"""

from dataclasses import dataclass

from .config import grunderwerbsteuer_rate, load_config


@dataclass(frozen=True)
class Affordability:
    max_monthly_payment: float
    max_loan: float
    max_purchase_price: float
    ancillary_quota: float
    equity: float


def affordability(
    net_monthly_income: float,
    equity: float,
    annual_rate: float,
    initial_repayment: float,
    bundesland: str,
    *,
    max_rate_to_net_income: float | None = None,
    existing_obligations: float = 0.0,
    running_costs_monthly: float = 0.0,
    makler_rate: float | None = None,
    config: dict | None = None,
) -> Affordability:
    """Maximum affordable purchase price from a net-income-based payment budget.

    Args:
        net_monthly_income: net monthly household income in EUR (> 0).
        equity: available equity in EUR (>= 0).
        annual_rate: nominal annual interest rate as a fraction (>= 0).
        initial_repayment: anfängliche Tilgung as a fraction (> 0).
        bundesland: code or name, for the Grunderwerbsteuer share of the ancillary quota.
        max_rate_to_net_income: payment-to-income cap (fraction). ``None`` uses the config.
        existing_obligations: other monthly loan/credit payments in EUR (subtracted).
        running_costs_monthly: estimated monthly running costs in EUR (subtracted).
        makler_rate: buyer's Makler share for the ancillary quota. ``None`` uses the config.
    """
    if net_monthly_income <= 0:
        raise ValueError("net_monthly_income must be > 0")
    if equity < 0:
        raise ValueError("equity must be >= 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")
    if initial_repayment <= 0:
        raise ValueError("initial_repayment must be > 0")
    if annual_rate > 0.25:
        raise ValueError(
            "annual_rate is a fraction (0.036 = 3.6 %) — a value above 0.25 looks like percent"
        )
    if initial_repayment > 0.2:
        raise ValueError(
            "initial_repayment is a fraction (0.02 = 2 %) — a value above 0.2 looks like percent"
        )

    cfg = config or load_config()
    if max_rate_to_net_income is None:
        max_rate_to_net_income = cfg["affordability"]["max_rate_to_net_income"]
    if not 0 < max_rate_to_net_income <= 1:
        raise ValueError("max_rate_to_net_income must be in (0, 1]")

    max_monthly_payment = (
        net_monthly_income * max_rate_to_net_income - existing_obligations - running_costs_monthly
    )
    if max_monthly_payment <= 0:
        raise ValueError("no payment budget left after obligations and running costs")

    max_loan = max_monthly_payment * 12.0 / (annual_rate + initial_repayment)

    notary_rate = cfg["notary_and_land_registry"]["notary_rate"]
    lr_rate = cfg["notary_and_land_registry"]["land_registry_rate"]
    if makler_rate is None:
        makler_rate = cfg["makler"]["typical_buyer_rate"]
    if makler_rate < 0:
        raise ValueError("makler_rate must be >= 0")
    grest = grunderwerbsteuer_rate(bundesland, config=cfg)
    ancillary_quota = grest + notary_rate + lr_rate + makler_rate

    max_purchase_price = (max_loan + equity) / (1.0 + ancillary_quota)

    return Affordability(
        max_monthly_payment=max_monthly_payment,
        max_loan=max_loan,
        max_purchase_price=max_purchase_price,
        ancillary_quota=ancillary_quota,
        equity=equity,
    )
