"""Bewirtschaftungskosten — annual non-allocable operating costs of a rental unit.

    instandhaltung    = living_area_sqm · instandhaltung_eur_per_sqm_year
    verwaltung        = units · verwaltung_eur_per_unit_year
    mietausfallwagnis = annual cold rent · mietausfallwagnis_rate

Anchored on the II. BV (§§ 26-29) Pauschalen as practice values from ``config/rates.yaml``
(source + date there). An estimate anchor for the net-yield calculation, not an invoice.
Pure and deterministic.
"""

from dataclasses import dataclass

from .config import load_config


@dataclass(frozen=True)
class OperatingCosts:
    instandhaltung: float
    verwaltung: float
    mietausfallwagnis: float
    total_annual: float


def operating_costs(
    living_area_sqm: float,
    monthly_cold_rent: float,
    *,
    units: int = 1,
    config: dict | None = None,
) -> OperatingCosts:
    """Estimate annual operating costs from the config-anchored practice values.

    Args:
        living_area_sqm: living area in m² (> 0).
        monthly_cold_rent: monthly Kaltmiete in EUR (> 0).
        units: number of residential units (>= 1), scales the per-unit management fee.
    """
    if living_area_sqm <= 0:
        raise ValueError("living_area_sqm must be > 0")
    if monthly_cold_rent <= 0:
        raise ValueError("monthly_cold_rent must be > 0")
    if units < 1:
        raise ValueError("units must be >= 1")

    cfg = (config or load_config())["bewirtschaftung"]
    instandhaltung = living_area_sqm * cfg["instandhaltung_eur_per_sqm_year"]
    verwaltung = units * cfg["verwaltung_eur_per_unit_year"]
    mietausfallwagnis = monthly_cold_rent * 12.0 * cfg["mietausfallwagnis_rate"]
    return OperatingCosts(
        instandhaltung=instandhaltung,
        verwaltung=verwaltung,
        mietausfallwagnis=mietausfallwagnis,
        total_annual=instandhaltung + verwaltung + mietausfallwagnis,
    )
