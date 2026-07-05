"""Tests for listing enrichment (Bodenrichtwert seam; honest 'unavailable' degradation)."""

from estatescout.scout.enrich import (
    BodenrichtwertProvider,
    RegionSignal,
    RegionSignalProvider,
    StaticBodenrichtwert,
    StaticRegionSignal,
    enrich,
)
from estatescout.scout.model import Listing


def _listing(plz: str = "49074") -> Listing:
    return Listing(price=300_000, living_area_sqm=100, bundesland="NI", plz=plz)


def test_static_provider_satisfies_protocol():
    assert isinstance(StaticBodenrichtwert(), BodenrichtwertProvider)


def test_enrich_attaches_known_bodenrichtwert():
    provider = StaticBodenrichtwert({"49074": 420.0})
    e = enrich(_listing("49074"), bodenrichtwert=provider)
    assert e.bodenrichtwert_eur_per_sqm == 420.0
    assert "bodenrichtwert" not in e.unavailable


def test_enrich_degrades_to_unavailable_when_unknown():
    provider = StaticBodenrichtwert({"49074": 420.0})
    e = enrich(_listing("12345"), bodenrichtwert=provider)  # plz not in table
    assert e.bodenrichtwert_eur_per_sqm is None
    assert "bodenrichtwert" in e.unavailable


def test_enrich_without_provider_is_unavailable_not_fabricated():
    e = enrich(_listing())
    assert e.bodenrichtwert_eur_per_sqm is None
    assert "bodenrichtwert" in e.unavailable
    assert "region_signal" in e.unavailable


def test_region_provider_satisfies_protocol():
    assert isinstance(StaticRegionSignal(), RegionSignalProvider)


def test_enrich_attaches_region_signal_and_clears_unavailable():
    boris = StaticBodenrichtwert({"49074": 420.0})
    region = StaticRegionSignal(
        {"49074": RegionSignal(population_trend_pct=1.2, vacancy_rate_pct=2.1)}
    )
    e = enrich(_listing("49074"), bodenrichtwert=boris, region=region)
    assert e.region is not None
    assert e.region.population_trend_pct == 1.2
    assert e.region.vacancy_rate_pct == 2.1
    assert e.unavailable == ()


def test_enrich_region_unavailable_when_unknown():
    e = enrich(_listing("49074"), bodenrichtwert=StaticBodenrichtwert({"49074": 420.0}))
    assert e.region is None
    assert "region_signal" in e.unavailable
