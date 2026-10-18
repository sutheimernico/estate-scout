"""Delta logic of the nightly re-score digest (pure functions, no network or clock)."""

from estatescout.scout.digest import diff_snapshots, render_digest, snapshot
from estatescout.scout.enrich import Enrichment, RegionSignal
from estatescout.scout.model import Listing
from estatescout.scout.scoring import score_listing


def _snap(brw: float, listing_id: int = 1) -> dict:
    listing = Listing(price=300_000, living_area_sqm=100, bundesland="NI", ort="Lingen",
                      plz="49808", id=listing_id)
    enrichment = Enrichment(
        bodenrichtwert_eur_per_sqm=brw,
        region=RegionSignal(population_trend_pct=0.5, vacancy_rate_pct=3.0),
    )
    return snapshot(listing, enrichment, score_listing(listing, enrichment))


def test_snapshot_records_label_total_and_inputs():
    s = _snap(500.0)
    assert s["label"] == "Lingen, 49808"
    assert s["inputs"]["bodenrichtwert"] == 500.0
    assert s["total"] is not None


def test_unchanged_object_produces_no_delta():
    assert diff_snapshots({"1": _snap(500.0)}, {"1": _snap(500.0)}) == []


def test_input_change_names_the_input_and_the_score_move():
    deltas = diff_snapshots({"1": _snap(500.0)}, {"1": _snap(800.0)})
    assert len(deltas) == 1
    d = deltas[0]
    assert d.old_total != d.new_total
    assert d.changed_inputs == (("bodenrichtwert", 500.0, 800.0),)


def test_new_object_is_reported_without_an_old_score():
    deltas = diff_snapshots({}, {"2": _snap(500.0, listing_id=2)})
    assert deltas[0].old_total is None


def test_deleted_object_is_not_reported():
    assert diff_snapshots({"1": _snap(500.0)}, {}) == []


def test_render_digest_is_german_and_shows_old_to_new():
    prev, cur = _snap(500.0), _snap(800.0)
    text = render_digest("2026-10-18", diff_snapshots({"1": prev}, {"1": cur}))
    assert text.startswith("# Score-Digest 2026-10-18")
    assert f"Score {prev['total']} → {cur['total']}" in text
    assert "Bodenrichtwert (€/m²) 500 → 800" in text


def test_render_digest_without_changes_says_so():
    assert "Keine Änderungen" in render_digest("2026-10-18", [])
