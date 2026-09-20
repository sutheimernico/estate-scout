"""Tests for listing enrichment (Bodenrichtwert seam; honest 'unavailable' degradation)."""

import pytest

from estatescout.scout.enrich import (
    BodenrichtwertProvider,
    RegionSignal,
    RegionSignalProvider,
    StaticBodenrichtwert,
    StaticRegionSignal,
    UnavailableReason,
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
    assert e.unavailable == {}


def test_enrich_region_unavailable_when_unknown():
    e = enrich(_listing("49074"), bodenrichtwert=StaticBodenrichtwert({"49074": 420.0}))
    assert e.region is None
    assert "region_signal" in e.unavailable


def test_missing_provider_and_missing_data_are_distinguishable():
    # no providers at all → both signals report PROVIDER_MISSING
    e = enrich(_listing("49074"))
    assert e.unavailable == {
        "bodenrichtwert": UnavailableReason.PROVIDER_MISSING,
        "region_signal": UnavailableReason.PROVIDER_MISSING,
    }

    # providers configured but with no entry for this listing → NO_DATA
    e = enrich(
        _listing("12345"),
        bodenrichtwert=StaticBodenrichtwert({"49074": 420.0}),
        region=StaticRegionSignal({"49074": RegionSignal(vacancy_rate_pct=2.1)}),
    )
    assert e.unavailable == {
        "bodenrichtwert": UnavailableReason.NO_DATA,
        "region_signal": UnavailableReason.NO_DATA,
    }


def test_unavailable_reason_serializes_as_its_string_value():
    import json

    e = enrich(_listing())
    assert json.loads(json.dumps(e.unavailable))["bodenrichtwert"] == "provider_missing"


def test_configured_providers_reads_the_config_and_defaults_to_none():
    from estatescout.scout.bodenrichtwert_wfs import WfsBodenrichtwert
    from estatescout.scout.enrich import configured_providers

    boris, region = configured_providers({"bodenrichtwert": {"provider": "none"}})
    assert boris is None and region is None

    boris, region = configured_providers(
        {"bodenrichtwert": {"provider": "wfs_ni", "wfs_ni": {"max_features": 50}}}
    )
    assert isinstance(boris, WfsBodenrichtwert)
    assert boris.max_features == 50


def test_configured_providers_builds_the_static_tables():
    from estatescout.scout.enrich import configured_providers

    boris, region = configured_providers(
        {
            "bodenrichtwert": {"provider": "static", "static": {"by_plz": {"49074": 420.0}}},
            "region_signal": {
                "provider": "static",
                "static": {"by_plz": {"49074": {"vacancy_rate_pct": 2.1}}},
            },
        }
    )
    assert boris.lookup(_listing("49074")) == 420.0
    assert region.lookup(_listing("49074")).vacancy_rate_pct == 2.1


def test_unknown_provider_name_errors_loudly():
    from estatescout.scout.enrich import configured_providers

    with pytest.raises(ValueError, match="unknown bodenrichtwert provider"):
        configured_providers({"bodenrichtwert": {"provider": "magic"}})


def test_the_shipped_provider_config_parses():
    # parse the real file directly — conftest pins the loader to "no providers" for the suite
    import yaml

    from estatescout.scout.enrich import _PROVIDER_CONFIG, configured_providers

    cfg = yaml.safe_load(_PROVIDER_CONFIG.read_text(encoding="utf-8"))
    assert cfg["bodenrichtwert"]["source"]
    assert cfg["bodenrichtwert"]["as_of"]
    configured_providers(cfg)  # the shipped config must build without error
