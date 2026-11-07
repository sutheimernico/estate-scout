"""The bundled example object: full data coverage, idempotent, and never overwritten."""

from fastapi.testclient import TestClient

from estatescout.api import app, get_providers, get_store
from estatescout.scout.enrich import StaticBodenrichtwert
from estatescout.scout.example import EXAMPLE_RENT, seed_example
from estatescout.scout.rescore import rescore
from estatescout.scout.scoring import score_listing
from estatescout.scout.store import ListingStore


def test_with_a_rent_all_four_signals_are_present():
    store = ListingStore()
    listing = seed_example(store)
    stored = store.get_enrichment(listing.id)
    report = score_listing(listing, stored.enrichment, monthly_cold_rent=EXAMPLE_RENT)
    assert (report.inputs_available, report.inputs_expected) == (4, 4)
    assert report.confidence == 1.0
    assert report.total is not None


def test_seeding_twice_creates_one_object():
    store = ListingStore()
    first = seed_example(store)
    second = seed_example(store)
    assert first.id == second.id
    assert len(store.list()) == 1


def test_the_example_is_labelled_as_an_example():
    listing = seed_example(ListingStore())
    assert listing.is_example
    assert "Beispiel" in listing.ort


def test_rescore_keeps_the_fixed_example_data(tmp_path):
    store = ListingStore()
    listing = seed_example(store)
    rescore(
        store,
        bodenrichtwert=StaticBodenrichtwert({"49808": 999.0}),
        region=None,
        state_path=tmp_path / "state.json",
        digest_dir=tmp_path / "digests",
        today="2026-10-28",
    )
    stored = store.get_enrichment(listing.id)
    assert stored.enrichment.bodenrichtwert_eur_per_sqm == 280.0
    assert stored.enrichment.region is not None


def test_enrich_endpoint_refuses_the_example(tmp_path):
    db = str(tmp_path / "api.db")
    seeded = ListingStore(db)
    listing_id = seed_example(seeded).id
    seeded.close()

    def per_request_store():
        store = ListingStore(db)  # fresh connection per request thread
        try:
            yield store
        finally:
            store.close()

    app.dependency_overrides[get_store] = per_request_store
    app.dependency_overrides[get_providers] = lambda: (None, None)
    try:
        r = TestClient(app).post(f"/api/listings/{listing_id}/enrich")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 409
    assert "Beispielobjekt" in r.json()["detail"]


def test_list_score_of_the_example_matches_its_detail_score(tmp_path):
    db = str(tmp_path / "api.db")
    seeded = ListingStore(db)
    listing = seed_example(seeded)
    stored = seeded.get_enrichment(listing.id)
    expected = score_listing(listing, stored.enrichment, monthly_cold_rent=EXAMPLE_RENT)
    seeded.close()

    def per_request_store():
        store = ListingStore(db)
        try:
            yield store
        finally:
            store.close()

    app.dependency_overrides[get_store] = per_request_store
    try:
        rows = TestClient(app).get("/api/listings").json()
    finally:
        app.dependency_overrides.clear()
    assert rows[0]["score"] == {"total": expected.total, "confidence": 1.0}
