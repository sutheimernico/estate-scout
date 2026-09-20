"""Tests for persisting enrichment on the listing row (schema v1 migration included)."""

import json
import sqlite3

from estatescout.scout.enrich import Enrichment, RegionSignal, UnavailableReason
from estatescout.scout.model import Listing
from estatescout.scout.store import SCHEMA_VERSION, ListingStore


def _sample() -> Listing:
    return Listing(price=300_000, living_area_sqm=100, bundesland="NI", plz="49074")


def _enrichment() -> Enrichment:
    return Enrichment(
        bodenrichtwert_eur_per_sqm=420.0,
        region=RegionSignal(population_trend_pct=1.2, vacancy_rate_pct=2.1),
        unavailable={},
    )


def test_fresh_store_is_at_the_current_schema_version():
    store = ListingStore(":memory:")
    assert store.schema_version() == SCHEMA_VERSION
    store.close()


def test_set_and_get_enrichment_round_trips():
    store = ListingStore(":memory:")
    listing = store.add(_sample())
    assert store.set_enrichment(listing.id, _enrichment()) is True
    stored = store.get_enrichment(listing.id)
    assert stored is not None
    assert stored.enrichment.bodenrichtwert_eur_per_sqm == 420.0
    assert stored.enrichment.region.vacancy_rate_pct == 2.1
    assert stored.enriched_at  # ISO timestamp
    store.close()


def test_set_enrichment_unknown_id_is_false():
    store = ListingStore(":memory:")
    assert store.set_enrichment(999, _enrichment()) is False
    store.close()


def test_get_enrichment_is_none_before_enriching():
    store = ListingStore(":memory:")
    listing = store.add(_sample())
    assert store.get_enrichment(listing.id) is None
    store.close()


def test_reenriching_updates_the_timestamp_and_the_payload():
    store = ListingStore(":memory:")
    listing = store.add(_sample())
    store.set_enrichment(listing.id, _enrichment())
    first = store.get_enrichment(listing.id)
    store.set_enrichment(
        listing.id,
        Enrichment(unavailable={"bodenrichtwert": UnavailableReason.NO_DATA}),
    )
    second = store.get_enrichment(listing.id)
    assert second.enrichment.bodenrichtwert_eur_per_sqm is None
    assert second.enrichment.unavailable["bodenrichtwert"] is UnavailableReason.NO_DATA
    assert second.enriched_at >= first.enriched_at
    store.close()


def test_enrichment_map_returns_every_enriched_listing(tmp_path):
    store = ListingStore(str(tmp_path / "s.db"))
    a = store.add(_sample())
    store.add(Listing(price=200_000, living_area_sqm=70, bundesland="NW"))
    store.set_enrichment(a.id, _enrichment())
    assert set(store.enrichment_map()) == {a.id}
    store.close()


def test_migrates_a_legacy_v0_database(tmp_path):
    """A DB written before schema v1 gains the new columns without losing rows."""
    path = str(tmp_path / "legacy.db")
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE listings (id INTEGER PRIMARY KEY AUTOINCREMENT, price REAL NOT NULL, "
        "living_area_sqm REAL NOT NULL, bundesland TEXT NOT NULL, plz TEXT, ort TEXT, "
        "rooms REAL, year_built INTEGER, object_type TEXT, features TEXT, source_url TEXT)"
    )
    conn.execute(
        "INSERT INTO listings (price, living_area_sqm, bundesland, features) VALUES (?, ?, ?, ?)",
        (300_000, 100, "NI", json.dumps([])),
    )
    conn.commit()
    conn.close()

    store = ListingStore(path)
    assert store.schema_version() == SCHEMA_VERSION
    assert len(store.list()) == 1
    listing_id = store.list()[0].id
    assert store.set_enrichment(listing_id, _enrichment()) is True
    assert store.get_enrichment(listing_id).enrichment.bodenrichtwert_eur_per_sqm == 420.0
    store.close()
