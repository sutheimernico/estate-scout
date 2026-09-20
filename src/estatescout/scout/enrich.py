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
from typing import Protocol, runtime_checkable

from .model import Listing


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
