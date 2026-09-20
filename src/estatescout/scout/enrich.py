"""Enrich a listing with public reference data — honestly.

Per ADR-0001 there is no legal automated source for the Bodenrichtwert (BORIS has no public
REST API) or for fine-grained regional signals. So the providers here are seams:

- for tests, and
- for the honest production path: a user-maintained table of values they looked up (BORIS.NI /
  BORIS.NRW, Gutachterausschuss, Zensus). An empty table degrades to "unavailable" — a value is
  NEVER fabricated. Missing data is recorded in ``Enrichment.unavailable``, not guessed.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml

from .model import Listing

_PROVIDER_CONFIG = Path(__file__).resolve().parents[3] / "config" / "providers.yaml"


class UnavailableReason(StrEnum):
    """Why a signal has no value. A ``StrEnum`` so it serializes to JSON as its value."""

    PROVIDER_MISSING = "provider_missing"  # nothing configured to look this up
    NO_DATA = "no_data"  # provider ran, but knows nothing about this listing


@dataclass(frozen=True)
class RegionSignal:
    population_trend_pct: float | None = None  # yearly % change (positive = growing region)
    vacancy_rate_pct: float | None = None  # marktaktiver Leerstand in %


@dataclass(frozen=True)
class Enrichment:
    bodenrichtwert_eur_per_sqm: float | None = None
    region: RegionSignal | None = None
    # signal name -> why it is absent. Scoring needs the distinction: a missing provider is a
    # setup gap, missing data is a fact about this listing. Treat as read-only.
    unavailable: dict[str, UnavailableReason] = field(default_factory=dict)


@runtime_checkable
class BodenrichtwertProvider(Protocol):
    def lookup(self, listing: Listing) -> float | None:
        """Local Bodenrichtwert in EUR/m², or None if unavailable (never a guess)."""
        ...


@runtime_checkable
class RegionSignalProvider(Protocol):
    def lookup(self, listing: Listing) -> RegionSignal | None:
        """Regional demographic/vacancy signal, or None if unavailable (never a guess)."""
        ...


class StaticBodenrichtwert:
    """Bodenrichtwert from a user-maintained ``{plz: EUR/m²}`` table. Empty → all unavailable.

    Serves both as the test fake and as the honest production provider (the user enters values
    they looked up on BORIS / at the Gutachterausschuss). Nothing is fabricated.
    """

    def __init__(self, by_plz: dict[str, float] | None = None):
        self._by_plz = dict(by_plz or {})

    def lookup(self, listing: Listing) -> float | None:
        return self._by_plz.get(listing.plz)


class StaticRegionSignal:
    """Regional signal from a user-maintained ``{plz: RegionSignal}`` table (Zensus/Destatis)."""

    def __init__(self, by_plz: dict[str, RegionSignal] | None = None):
        self._by_plz = dict(by_plz or {})

    def lookup(self, listing: Listing) -> RegionSignal | None:
        return self._by_plz.get(listing.plz)


def enrich(
    listing: Listing,
    *,
    bodenrichtwert: BodenrichtwertProvider | None = None,
    region: RegionSignalProvider | None = None,
) -> Enrichment:
    """Attach available public reference data to a listing; record why anything is missing."""
    unavailable: dict[str, UnavailableReason] = {}

    brw = bodenrichtwert.lookup(listing) if bodenrichtwert is not None else None
    if brw is None:
        unavailable["bodenrichtwert"] = (
            UnavailableReason.PROVIDER_MISSING
            if bodenrichtwert is None
            else UnavailableReason.NO_DATA
        )

    signal = region.lookup(listing) if region is not None else None
    if signal is None:
        unavailable["region_signal"] = (
            UnavailableReason.PROVIDER_MISSING if region is None else UnavailableReason.NO_DATA
        )

    return Enrichment(bodenrichtwert_eur_per_sqm=brw, region=signal, unavailable=unavailable)


def to_dict(enrichment: Enrichment) -> dict:
    """JSON-ready view of an enrichment (used for persistence and the API)."""
    region = enrichment.region
    return {
        "bodenrichtwert_eur_per_sqm": enrichment.bodenrichtwert_eur_per_sqm,
        "region": (
            None
            if region is None
            else {
                "population_trend_pct": region.population_trend_pct,
                "vacancy_rate_pct": region.vacancy_rate_pct,
            }
        ),
        "unavailable": {k: v.value for k, v in enrichment.unavailable.items()},
    }


def from_dict(data: dict) -> Enrichment:
    """Inverse of :func:`to_dict`. Unknown reasons raise rather than being silently dropped."""
    region = data.get("region")
    return Enrichment(
        bodenrichtwert_eur_per_sqm=data.get("bodenrichtwert_eur_per_sqm"),
        region=(
            None
            if region is None
            else RegionSignal(
                population_trend_pct=region.get("population_trend_pct"),
                vacancy_rate_pct=region.get("vacancy_rate_pct"),
            )
        ),
        unavailable={k: UnavailableReason(v) for k, v in (data.get("unavailable") or {}).items()},
    )


@lru_cache(maxsize=8)
def load_provider_config(path: str | None = None) -> dict:
    """Parse ``config/providers.yaml`` (or an explicit path). Cached per path."""
    p = Path(path) if path else _PROVIDER_CONFIG
    if not p.exists():
        raise FileNotFoundError(f"provider config not found: {p}")
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"provider config at {p} is not a mapping")
    return data


def _build_bodenrichtwert(block: dict) -> BodenrichtwertProvider | None:
    kind = block.get("provider", "none")
    if kind == "none":
        return None
    if kind == "static":
        return StaticBodenrichtwert(block.get("static", {}).get("by_plz") or {})
    if kind == "wfs_ni":
        from .bodenrichtwert_wfs import DEFAULT_URL, WfsBodenrichtwert

        settings = block.get("wfs_ni") or {}
        return WfsBodenrichtwert(
            settings.get("url", DEFAULT_URL),
            max_features=int(settings.get("max_features", 200)),
            timeout=float(settings.get("timeout_seconds", 60)),
        )
    raise ValueError(f"unknown bodenrichtwert provider '{kind}' (none | static | wfs_ni)")


def _build_region(block: dict) -> RegionSignalProvider | None:
    kind = block.get("provider", "none")
    if kind == "none":
        return None
    if kind == "static":
        table = {
            plz: RegionSignal(**fields)
            for plz, fields in (block.get("static", {}).get("by_plz") or {}).items()
        }
        return StaticRegionSignal(table)
    raise ValueError(f"unknown region_signal provider '{kind}' (none | static)")


def configured_providers(
    config: dict | None = None,
) -> tuple[BodenrichtwertProvider | None, RegionSignalProvider | None]:
    """The providers the running app enriches with, per ``config/providers.yaml``.

    ``None`` means nothing is configured for that signal — enrichment then records
    ``provider_missing`` instead of inventing a value.
    """
    cfg = config if config is not None else load_provider_config()
    return (
        _build_bodenrichtwert(cfg.get("bodenrichtwert") or {}),
        _build_region(cfg.get("region_signal") or {}),
    )
