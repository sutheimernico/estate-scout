"""The Listing object model.

Holds only object attributes — deliberately NO seller contact data (name/phone/email), per
ADR-0001 and DSGVO. Bundesland is normalized to its canonical code on construction.
"""

from dataclasses import dataclass

from ..finance.config import normalize_bundesland


@dataclass(frozen=True)
class Listing:
    price: float  # EUR
    living_area_sqm: float
    bundesland: str  # code or name; normalized to a code on construction
    plz: str = ""
    ort: str = ""
    rooms: float | None = None
    year_built: int | None = None
    object_type: str = "wohnung"  # e.g. wohnung | haus | grundstueck
    features: tuple[str, ...] = ()
    source_url: str = ""
    id: int | None = None  # assigned by the store

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError("price must be > 0")
        if self.living_area_sqm <= 0:
            raise ValueError("living_area_sqm must be > 0")
        if self.year_built is not None and not (1800 <= self.year_built <= 2100):
            raise ValueError("year_built out of range")
        # normalize + validate the Bundesland (raises on unknown)
        object.__setattr__(self, "bundesland", normalize_bundesland(self.bundesland))

    @property
    def price_per_sqm(self) -> float:
        return self.price / self.living_area_sqm
