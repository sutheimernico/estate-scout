"""Transparent 0-100 scoring of a saved listing — the scout's core judgement.

Three building blocks, each 0-100 and each explainable on its own:

    yield   gross rental yield (from ``finance.yield_metrics``) mapped onto 0..100
    price   listing EUR/m² versus the local Bodenrichtwert, mapped onto 100..0
    region  population trend and vacancy rate from the region signal

The total is the weighted mean of the blocks that could actually be computed; the weights of
the available blocks are renormalized to 1. If nothing is computable the total is ``None`` —
a missing score is reported, never invented. Every weight and threshold comes from
``config/scoring.yaml`` with ``source`` + ``as_of``; this module contains no magic numbers.

Honesty notes worth repeating to a user:

* ``PRICE_VS_LAND_VALUE`` compares the price per m² of *living space* with the Bodenrichtwert,
  which is the value per m² of *land*. Those are different quantities, so the ratio is a
  transparency-first proxy for "expensive for the area", not a valuation. It is used because
  the Bodenrichtwert is the one locally-specific figure available from official sources
  without scraping (ADR-0001). Read the ratio as a relative signal, not an appraisal.
* The thresholds are own heuristics. They are in config precisely so they can be argued with.

The total is computed from the *rounded* sub-scores, so the breakdown the UI shows adds up to
the total it shows.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from ..finance.yield_metrics import yield_metrics
from .enrich import Enrichment
from .model import Listing

_DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "scoring.yaml"

# The three building blocks, in display order.
BLOCKS = ("yield", "price", "region")

# Name of the price heuristic, spelled out so it is searchable from the UI copy.
PRICE_VS_LAND_VALUE = "price_per_sqm_vs_bodenrichtwert"

# Why a block could not be computed, when the reason does not come from the enrichment.
REASON_RENT_MISSING = "rent_missing"


@lru_cache(maxsize=8)
def load_scoring_config(path: str | None = None) -> dict:
    """Parse ``config/scoring.yaml`` (or an explicit path). Cached per path."""
    p = Path(path) if path else _DEFAULT_CONFIG
    if not p.exists():
        raise FileNotFoundError(f"scoring config not found: {p}")
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"scoring config at {p} is not a mapping")
    weights = data.get("weights", {})
    for block in BLOCKS:
        if block not in weights:
            raise KeyError(f"scoring config is missing the weight for '{block}'")
        if float(weights[block]) <= 0:
            raise ValueError(f"scoring weight for '{block}' must be > 0")
    return data


@dataclass(frozen=True)
class SubScore:
    """One building block of the total score."""

    name: str
    value: int | None  # 0-100, or None when the inputs were missing
    weight: float  # configured weight, before renormalization
    detail: dict = field(default_factory=dict)  # the inputs it used, for the drilldown
    reason: str | None = None  # why it is unavailable (provider_missing / no_data / ...)


@dataclass(frozen=True)
class ScoreReport:
    total: int | None  # None when no block was computable — never a fabricated 0
    subscores: tuple[SubScore, ...]
    weights_used: dict[str, float]  # renormalized, only the available blocks
    confidence: float  # available inputs / expected inputs, 0..1
    inputs_available: int
    inputs_expected: int
    reasons: dict[str, str]  # block -> why it is missing
    as_of: str  # date of the weights in the config


def _clamp_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, value))))


def _linear(value: float, at_0: float, at_100: float) -> int:
    """Map ``value`` linearly onto 0..100 between the two anchors (clamped, either direction)."""
    if at_0 == at_100:
        raise ValueError("scoring bounds must differ")
    return _clamp_score((value - at_0) / (at_100 - at_0) * 100.0)


def _yield_block(listing: Listing, monthly_cold_rent: float | None, cfg: dict) -> SubScore:
    weight = float(cfg["weights"]["yield"])
    if monthly_cold_rent is None or monthly_cold_rent <= 0:
        return SubScore("yield", None, weight, reason=REASON_RENT_MISSING)
    block = cfg["yield_score"]
    metrics = yield_metrics(listing.price, monthly_cold_rent)
    gross_percent = metrics.gross_yield * 100.0
    return SubScore(
        "yield",
        _linear(
            gross_percent,
            float(block["gross_yield_percent_at_0"]),
            float(block["gross_yield_percent_at_100"]),
        ),
        weight,
        detail={
            "monthly_cold_rent": monthly_cold_rent,
            "annual_cold_rent": metrics.annual_cold_rent,
            "gross_yield_percent": round(gross_percent, 3),
            "kaufpreisfaktor": round(metrics.kaufpreisfaktor, 1),
        },
    )


def _price_block(listing: Listing, enrichment: Enrichment, cfg: dict) -> SubScore:
    weight = float(cfg["weights"]["price"])
    bodenrichtwert = enrichment.bodenrichtwert_eur_per_sqm
    if bodenrichtwert is None or bodenrichtwert <= 0:
        reason = enrichment.unavailable.get("bodenrichtwert")
        return SubScore("price", None, weight, reason=str(reason) if reason else "no_data")
    block = cfg["price_score"]
    ratio = listing.price_per_sqm / bodenrichtwert
    return SubScore(
        "price",
        _linear(ratio, float(block["ratio_at_0"]), float(block["ratio_at_100"])),
        weight,
        detail={
            "heuristic": PRICE_VS_LAND_VALUE,
            "price_per_sqm": round(listing.price_per_sqm, 2),
            "bodenrichtwert_eur_per_sqm": bodenrichtwert,
            "ratio": round(ratio, 3),
        },
    )


def _region_block(enrichment: Enrichment, cfg: dict) -> SubScore:
    weight = float(cfg["weights"]["region"])
    signal = enrichment.region
    block = cfg["region_score"]
    parts: list[int] = []
    detail: dict = {}
    if signal is not None and signal.population_trend_pct is not None:
        detail["population_trend_pct"] = signal.population_trend_pct
        parts.append(
            _linear(
                signal.population_trend_pct,
                float(block["population_trend_pct_at_0"]),
                float(block["population_trend_pct_at_100"]),
            )
        )
    if signal is not None and signal.vacancy_rate_pct is not None:
        detail["vacancy_rate_pct"] = signal.vacancy_rate_pct
        parts.append(
            _linear(
                signal.vacancy_rate_pct,
                float(block["vacancy_rate_pct_at_0"]),
                float(block["vacancy_rate_pct_at_100"]),
            )
        )
    if not parts:
        reason = enrichment.unavailable.get("region_signal")
        return SubScore("region", None, weight, reason=str(reason) if reason else "no_data")
    detail["parts"] = parts  # the per-field scores the average is built from
    return SubScore("region", _clamp_score(sum(parts) / len(parts)), weight, detail=detail)


def _count_inputs(listing_rent: float | None, enrichment: Enrichment) -> tuple[int, int]:
    """Available vs. expected raw signals — the basis of the confidence figure.

    Counted per signal, not per block, so half a region signal honestly reads as half.
    """
    signal = enrichment.region
    present = [
        listing_rent is not None and listing_rent > 0,
        enrichment.bodenrichtwert_eur_per_sqm is not None,
        signal is not None and signal.population_trend_pct is not None,
        signal is not None and signal.vacancy_rate_pct is not None,
    ]
    return sum(present), len(present)


def score_listing(
    listing: Listing,
    enrichment: Enrichment,
    *,
    monthly_cold_rent: float | None = None,
    config: dict | None = None,
) -> ScoreReport:
    """Score one listing against its enrichment.

    Args:
        listing: the saved object (price and living area drive the price block).
        enrichment: the stored enrichment; missing signals carry their typed reason.
        monthly_cold_rent: expected Kaltmiete in EUR. The ``Listing`` model deliberately has
            no rent field (it records what the exposé states about the object), so the rent
            is supplied per scoring run; without it the yield block stays unavailable.
    """
    cfg = config or load_scoring_config()
    subscores = (
        _yield_block(listing, monthly_cold_rent, cfg),
        _price_block(listing, enrichment, cfg),
        _region_block(enrichment, cfg),
    )

    available = [s for s in subscores if s.value is not None]
    weight_sum = sum(s.weight for s in available)
    weights_used = {s.name: s.weight / weight_sum for s in available} if available else {}
    total = (
        int(round(sum(s.value * weights_used[s.name] for s in available))) if available else None
    )

    inputs_available, inputs_expected = _count_inputs(monthly_cold_rent, enrichment)
    return ScoreReport(
        total=total,
        subscores=subscores,
        weights_used=weights_used,
        confidence=inputs_available / inputs_expected,
        inputs_available=inputs_available,
        inputs_expected=inputs_expected,
        reasons={s.name: s.reason for s in subscores if s.reason is not None},
        as_of=str(cfg["weights"]["as_of"]),
    )
