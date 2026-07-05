"""Rental-yield metrics for a buy-to-let property.

    gross_yield      = annual cold rent / purchase price
    Kaufpreisfaktor  = purchase price / annual cold rent   (= 1 / gross_yield)
    net_yield        = (annual cold rent − non-allocable operating costs)
                       / (purchase price + ancillary costs)

Rents are Kaltmiete (cold rent). Pure and deterministic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class YieldMetrics:
    annual_cold_rent: float
    gross_yield: float
    net_yield: float
    kaufpreisfaktor: float


def yield_metrics(
    purchase_price: float,
    monthly_cold_rent: float,
    *,
    annual_operating_costs: float = 0.0,
    ancillary_costs: float = 0.0,
) -> YieldMetrics:
    """Compute gross/net rental yield and the Kaufpreisfaktor (price-to-annual-rent multiplier).

    Args:
        purchase_price: property price in EUR (> 0).
        monthly_cold_rent: monthly Kaltmiete in EUR (> 0).
        annual_operating_costs: non-allocable annual running costs in EUR (>= 0), subtracted
            for the net yield.
        ancillary_costs: Kaufnebenkosten in EUR (>= 0), added to the invested base for net yield.
    """
    if purchase_price <= 0:
        raise ValueError("purchase_price must be > 0")
    if monthly_cold_rent <= 0:
        raise ValueError("monthly_cold_rent must be > 0")
    if annual_operating_costs < 0:
        raise ValueError("annual_operating_costs must be >= 0")
    if ancillary_costs < 0:
        raise ValueError("ancillary_costs must be >= 0")

    annual_cold_rent = monthly_cold_rent * 12.0
    gross_yield = annual_cold_rent / purchase_price
    kaufpreisfaktor = purchase_price / annual_cold_rent
    invested_base = purchase_price + ancillary_costs
    net_yield = (annual_cold_rent - annual_operating_costs) / invested_base

    return YieldMetrics(
        annual_cold_rent=annual_cold_rent,
        gross_yield=gross_yield,
        net_yield=net_yield,
        kaufpreisfaktor=kaufpreisfaktor,
    )
