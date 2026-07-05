"""Tests for listing enrichment (Bodenrichtwert seam; honest 'unavailable' degradation)."""

from estatescout.scout.enrich import (
    BodenrichtwertProvider,
    StaticBodenrichtwert,
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
