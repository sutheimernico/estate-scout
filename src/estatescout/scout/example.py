"""One example object with complete data coverage, so the score can be seen working.

A real object only reaches 3 of 4 raw signals today: no keyless source exists for the regional
signal (see ``docs/bodenrichtwert-quelle.md``). The example therefore carries **illustrative**
reference values, stored directly. They are labelled as an example everywhere (``beispiel``
feature, "(Beispiel)" in the place name) and are not measurements of Lingen. With a Kaltmiete
entered, all four signals are present.
"""

from .enrich import Enrichment, RegionSignal
from .model import EXAMPLE_FEATURE, Listing
from .store import ListingStore

EXAMPLE_ORT = "Lingen (Beispiel)"
EXAMPLE_RENT = 1000.0  # monthly Kaltmiete that completes the data coverage in the UI


def seed_example(store: ListingStore) -> Listing:
    """Add the example object once and return it (idempotent)."""
    for existing in store.list():
        if existing.is_example:
            return existing
    saved = store.add(
        Listing(
            price=285_000,
            living_area_sqm=92,
            bundesland="NI",
            plz="49808",
            ort=EXAMPLE_ORT,
            rooms=3,
            year_built=2004,
            features=(EXAMPLE_FEATURE,),
        )
    )
    assert saved.id is not None
    store.set_enrichment(
        saved.id,
        Enrichment(
            bodenrichtwert_eur_per_sqm=280.0,
            region=RegionSignal(population_trend_pct=0.4, vacancy_rate_pct=2.1),
        ),
    )
    return saved
