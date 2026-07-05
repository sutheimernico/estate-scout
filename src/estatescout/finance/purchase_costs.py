"""Kaufnebenkosten — the ancillary costs on top of a property's purchase price.

Grunderwerbsteuer (per Bundesland), notary + Grundbuch, and Makler. All rates come from the
versioned config; the Makler share is optional (Bestellerprinzip — the buyer may pay a share,
half, or nothing). Pure and deterministic — numbers only from here.
"""

from dataclasses import dataclass

from .config import grunderwerbsteuer_rate, load_config


@dataclass(frozen=True)
class PurchaseCosts:
    purchase_price: float
    bundesland: str
    grunderwerbsteuer: float
    notary: float
    land_registry: float
    makler: float
    total_ancillary: float
    total_investment: float  # purchase_price + total_ancillary
    ancillary_quota: float  # total_ancillary / purchase_price
    min_equity: float  # rule of thumb: finance at least the ancillary costs from own funds


def purchase_costs(
    purchase_price: float,
    bundesland: str,
    *,
    makler_rate: float | None = None,
    config: dict | None = None,
) -> PurchaseCosts:
    """Break the ancillary purchase costs down for a given price and Bundesland.

    Args:
        purchase_price: property price in EUR (> 0).
        bundesland: code (``NI``, ``NW``) or name (``Niedersachsen``, ``NRW``).
        makler_rate: buyer's Makler share as a fraction. ``None`` uses the config default;
            pass ``0.0`` for no agent / seller-paid.
        config: optional pre-loaded config (else loaded from ``config/rates.yaml``).
    """
    if purchase_price <= 0:
        raise ValueError("purchase_price must be > 0")

    cfg = config or load_config()
    grest = grunderwerbsteuer_rate(bundesland, config=cfg)
    notary_rate = cfg["notary_and_land_registry"]["notary_rate"]
    lr_rate = cfg["notary_and_land_registry"]["land_registry_rate"]
    if makler_rate is None:
        makler_rate = cfg["makler"]["typical_buyer_rate"]
    if makler_rate < 0:
        raise ValueError("makler_rate must be >= 0")

    grunderwerbsteuer = purchase_price * grest
    notary = purchase_price * notary_rate
    land_registry = purchase_price * lr_rate
    makler = purchase_price * makler_rate
    total_ancillary = grunderwerbsteuer + notary + land_registry + makler

    return PurchaseCosts(
        purchase_price=purchase_price,
        bundesland=bundesland,
        grunderwerbsteuer=grunderwerbsteuer,
        notary=notary,
        land_registry=land_registry,
        makler=makler,
        total_ancillary=total_ancillary,
        total_investment=purchase_price + total_ancillary,
        ancillary_quota=total_ancillary / purchase_price,
        min_equity=total_ancillary,
    )
