"""Tests for the transparent 0-100 scoring engine.

Every expected number below is hand-computed from `config/scoring.yaml` (same convention as
the finance tests) so a threshold change fails loudly instead of silently shifting scores.
"""

import pytest

from estatescout.scout.enrich import Enrichment, RegionSignal, UnavailableReason
from estatescout.scout.model import Listing
from estatescout.scout.scoring import load_scoring_config, score_listing


def _listing(price: float = 300_000, area: float = 100) -> Listing:
    return Listing(price=price, living_area_sqm=area, bundesland="NI", plz="49074")


def _full_enrichment() -> Enrichment:
    return Enrichment(
        bodenrichtwert_eur_per_sqm=2_500.0,
        region=RegionSignal(population_trend_pct=0.5, vacancy_rate_pct=3.0),
        unavailable={},
    )


def _sub(report, name):
    return next(s for s in report.subscores if s.name == name)


def test_full_data_worked_example():
    # yield:  1_000 €/month → 12_000 €/a ÷ 300_000 = 4.0 % → 4.0/6.0 · 100 = 66.67 → 67
    # price:  3_000 €/m² ÷ 2_500 = 1.2 → (1.5-1.2)/(1.5-0.8) · 100 = 42.86 → 43
    # region: Bev. +0.5 → (0.5+1)/2 · 100 = 75 ; Leerstand 3.0 → (8-3)/(8-1) · 100 = 71.43 → 71
    #         region = mean of the rounded parts (75 + 71) / 2 = 73
    # total:  0.4·67 + 0.4·43 + 0.2·73 = 26.8 + 17.2 + 14.6 = 58.6 → 59
    report = score_listing(_listing(), _full_enrichment(), monthly_cold_rent=1_000.0)
    assert _sub(report, "yield").value == 67
    assert _sub(report, "price").value == 43
    assert _sub(report, "region").value == 73
    assert report.total == 59
    assert report.confidence == pytest.approx(1.0)
    assert report.inputs_available == 4
    assert report.inputs_expected == 4
    assert report.reasons == {}
    assert report.weights_used == {"yield": pytest.approx(0.4), "price": pytest.approx(0.4),
                                   "region": pytest.approx(0.2)}


def test_partial_data_renormalizes_the_weights():
    # only the yield block is computable → its weight becomes 1.0 → total == yield score
    report = score_listing(_listing(), Enrichment(), monthly_cold_rent=1_000.0)
    assert _sub(report, "yield").value == 67
    assert _sub(report, "price").value is None
    assert _sub(report, "region").value is None
    assert report.total == 67
    assert report.weights_used == {"yield": pytest.approx(1.0)}
    assert report.confidence == pytest.approx(0.25)  # 1 of 4 inputs


def test_two_blocks_renormalize_proportionally():
    # yield 67 (weight .4) + price 43 (weight .4) → both renormalize to .5
    # total = 0.5·67 + 0.5·43 = 55.0 → 55
    enrichment = Enrichment(bodenrichtwert_eur_per_sqm=2_500.0)
    report = score_listing(_listing(), enrichment, monthly_cold_rent=1_000.0)
    assert report.total == 55
    assert report.weights_used == {"yield": pytest.approx(0.5), "price": pytest.approx(0.5)}


def test_no_data_yields_no_total_and_never_fabricates():
    report = score_listing(_listing(), Enrichment())
    assert report.total is None
    assert all(s.value is None for s in report.subscores)
    assert report.weights_used == {}
    assert report.confidence == pytest.approx(0.0)


def test_reasons_pass_through_the_typed_enrichment_reasons():
    enrichment = Enrichment(
        unavailable={
            "bodenrichtwert": UnavailableReason.PROVIDER_MISSING,
            "region_signal": UnavailableReason.NO_DATA,
        }
    )
    report = score_listing(_listing(), enrichment)
    assert report.reasons["price"] == "provider_missing"
    assert report.reasons["region"] == "no_data"
    assert report.reasons["yield"] == "rent_missing"
    assert _sub(report, "price").reason == "provider_missing"


def test_region_uses_a_single_available_field():
    # only vacancy 3.0 → 71.43 → 71 ; one of two region inputs present
    enrichment = Enrichment(region=RegionSignal(vacancy_rate_pct=3.0))
    report = score_listing(_listing(), enrichment)
    assert _sub(report, "region").value == 71
    assert report.inputs_available == 1


def test_scores_are_clamped_to_the_0_100_range():
    # gross yield 12 % is far above the 6 % ceiling; ratio 0.3 far below the 0.8 floor
    enrichment = Enrichment(bodenrichtwert_eur_per_sqm=10_000.0)
    report = score_listing(_listing(), enrichment, monthly_cold_rent=3_000.0)
    assert _sub(report, "yield").value == 100
    assert _sub(report, "price").value == 100
    assert report.total == 100


def test_worst_case_is_zero_not_negative():
    enrichment = Enrichment(
        bodenrichtwert_eur_per_sqm=100.0,  # ratio 30 → far past the 1.5 floor
        region=RegionSignal(population_trend_pct=-5.0, vacancy_rate_pct=20.0),
    )
    report = score_listing(_listing(), enrichment, monthly_cold_rent=1.0)
    assert [s.value for s in report.subscores] == [0, 0, 0]
    assert report.total == 0


@pytest.mark.parametrize(
    "rent,brw,trend,vacancy",
    [
        (1_000.0, 2_500.0, 0.5, 3.0),
        (500.0, 1_000.0, -0.4, 6.5),
        (2_000.0, 4_000.0, 0.9, 1.5),
        (1_250.0, 3_300.0, 0.0, 4.0),
    ],
)
def test_total_always_lies_between_the_available_subscores(rent, brw, trend, vacancy):
    enrichment = Enrichment(
        bodenrichtwert_eur_per_sqm=brw,
        region=RegionSignal(population_trend_pct=trend, vacancy_rate_pct=vacancy),
    )
    report = score_listing(_listing(), enrichment, monthly_cold_rent=rent)
    values = [s.value for s in report.subscores if s.value is not None]
    assert min(values) <= report.total <= max(values)


def test_subscore_detail_shows_the_inputs_it_used():
    report = score_listing(_listing(), _full_enrichment(), monthly_cold_rent=1_000.0)
    assert _sub(report, "yield").detail["gross_yield_percent"] == pytest.approx(4.0)
    assert _sub(report, "price").detail["price_per_sqm"] == pytest.approx(3_000.0)
    assert _sub(report, "price").detail["bodenrichtwert_eur_per_sqm"] == pytest.approx(2_500.0)
    assert _sub(report, "region").detail["vacancy_rate_pct"] == pytest.approx(3.0)


def test_report_carries_the_config_as_of_date():
    report = score_listing(_listing(), Enrichment(), monthly_cold_rent=1_000.0)
    assert report.as_of == load_scoring_config()["weights"]["as_of"]


def test_config_errors_loudly_on_a_missing_block(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("weights:\n  yield: 0.4\n", encoding="utf-8")
    with pytest.raises(KeyError, match="price"):
        load_scoring_config(str(path))


def test_zero_weights_are_rejected(tmp_path):
    path = tmp_path / "zero.yaml"
    path.write_text(
        "weights:\n  as_of: x\n  source: y\n  yield: 0\n  price: 0\n  region: 0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="weight"):
        load_scoring_config(str(path))


def test_to_dict_is_json_serializable_and_keeps_every_field():
    import json

    from estatescout.scout.scoring import to_dict

    report = score_listing(_listing(), _full_enrichment(), monthly_cold_rent=1_000.0)
    payload = json.loads(json.dumps(to_dict(report)))
    assert payload["total"] == 59
    assert [s["name"] for s in payload["subscores"]] == ["yield", "price", "region"]
    assert payload["subscores"][1]["detail"]["heuristic"] == "price_per_sqm_vs_bodenrichtwert"
    assert payload["confidence"] == 1.0
    assert payload["as_of"]
