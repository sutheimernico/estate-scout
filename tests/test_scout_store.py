"""Tests for the SQLite listing store (in-memory + temp file)."""

from estatescout.scout.model import Listing
from estatescout.scout.store import ListingStore


def _sample() -> Listing:
    return Listing(
        price=300_000,
        living_area_sqm=100,
        bundesland="NI",
        ort="Osnabrück",
        rooms=4,
        year_built=1998,
        features=("Balkon", "Garage"),
        source_url="https://example.test/obj/1",
    )


def test_add_assigns_id_and_get_round_trips():
    store = ListingStore()
    saved = store.add(_sample())
    assert saved.id is not None
    got = store.get(saved.id)
    assert got is not None
    assert got.price == 300_000
    assert got.bundesland == "NI"
    assert got.features == ("Balkon", "Garage")  # JSON round-trip preserves the tuple
    store.close()


def test_list_and_delete():
    store = ListingStore()
    a = store.add(_sample())
    b = store.add(Listing(price=200_000, living_area_sqm=70, bundesland="NW"))
    assert {x.id for x in store.list()} == {a.id, b.id}
    assert store.delete(a.id) is True
    assert store.get(a.id) is None
    assert {x.id for x in store.list()} == {b.id}
    store.close()


def test_get_missing_returns_none():
    store = ListingStore()
    assert store.get(999) is None
    assert store.delete(999) is False
    store.close()


def test_persists_to_a_file(tmp_path):
    db = tmp_path / "listings.db"
    store = ListingStore(db)
    saved = store.add(_sample())
    store.close()
    reopened = ListingStore(db)
    got = reopened.get(saved.id)
    assert got is not None and got.ort == "Osnabrück"
    reopened.close()
