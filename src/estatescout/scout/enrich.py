"""Enrich a listing with public reference data — honestly.

Per ADR-0001 there is no legal automated source for the Bodenrichtwert (BORIS has no public
REST API) or for fine-grained regional signals. So the providers here are seams:

- for tests, and
- for the honest production path: a user-maintained table of values they looked up (BORIS.NI /
  BORIS.NRW, Gutachterausschuss, Zensus). An empty table degrades to "unavailable" — a value is
  NEVER fabricated. Missing data is recorded in ``Enrichment.unavailable``, not guessed.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .model import Listing


@dataclass(frozen=True)
class Enrichment:
    bodenrichtwert_eur_per_sqm: float | None = None
    unavailable: tuple[str, ...] = ()  # source names that had no data for this listing


@runtime_checkable
class BodenrichtwertProvider(Protocol):
    def lookup(self, listing: Listing) -> float | None:
        """Local Bodenrichtwert in EUR/m², or None if unavailable (never a guess)."""
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


def enrich(listing: Listing, *, bodenrichtwert: BodenrichtwertProvider | None = None) -> Enrichment:
    """Attach available public reference data to a listing; record what was unavailable."""
    unavailable: list[str] = []

    brw = bodenrichtwert.lookup(listing) if bodenrichtwert is not None else None
    if brw is None:
        unavailable.append("bodenrichtwert")

    return Enrichment(bodenrichtwert_eur_per_sqm=brw, unavailable=tuple(unavailable))
