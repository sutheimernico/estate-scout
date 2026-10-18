"""End to end: two re-score runs with a provider change in between produce a delta digest."""

from estatescout.scout.enrich import RegionSignal, StaticBodenrichtwert, StaticRegionSignal
from estatescout.scout.model import Listing
from estatescout.scout.rescore import rescore
from estatescout.scout.store import ListingStore


def _store() -> ListingStore:
    store = ListingStore()
    store.add(Listing(price=300_000, living_area_sqm=100, bundesland="NI", ort="Lingen",
                      plz="49808"))
    return store


def _run(store, tmp_path, brw, day):
    return rescore(
        store,
        bodenrichtwert=StaticBodenrichtwert({"49808": brw}),
        region=StaticRegionSignal({"49808": RegionSignal(0.5, 3.0)}),
        state_path=tmp_path / "state.json",
        digest_dir=tmp_path / "digests",
        today=day,
    )


def test_first_run_reports_the_object_as_new(tmp_path):
    text = _run(_store(), tmp_path, 500.0, "2026-10-18").read_text(encoding="utf-8")
    assert "neu, Score" in text


def test_second_run_after_a_value_change_reports_the_delta(tmp_path):
    store = _store()
    _run(store, tmp_path, 500.0, "2026-10-18")
    text = _run(store, tmp_path, 800.0, "2026-10-19").read_text(encoding="utf-8")
    assert "Bodenrichtwert (€/m²) 500 → 800" in text
    assert "neu," not in text


def test_second_run_without_change_says_so(tmp_path):
    store = _store()
    _run(store, tmp_path, 500.0, "2026-10-18")
    text = _run(store, tmp_path, 500.0, "2026-10-19").read_text(encoding="utf-8")
    assert "Keine Änderungen" in text


def test_run_persists_the_new_enrichment(tmp_path):
    store = _store()
    _run(store, tmp_path, 500.0, "2026-10-18")
    stored = store.get_enrichment(1)
    assert stored is not None
    assert stored.enrichment.bodenrichtwert_eur_per_sqm == 500.0
