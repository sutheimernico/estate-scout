"""Bodenrichtwert from the BORIS Niedersachsen WFS — one real, keyless public source.

Why this source (see docs/bodenrichtwert-quelle.md for the full decision): BORIS-NI publishes
``BR_BodenrichtwertZonal`` over an OGC WFS 2.0 endpoint that needs no registration and no key,
under the Datenlizenz Deutschland Namensnennung 2.0 (attribution: © GDI-NI / LGLN). No HTML is
scraped — this is the documented machine interface (ADR-0001 stays satisfied).

Two honest limitations, both deliberate and surfaced to the user:

1. **Municipality median, not the address's zone.** A ``Listing`` carries a PLZ and a town, not
   coordinates, so a point-in-polygon query is impossible. This provider filters the zones of the
   matching Gemeinde down to residential building land and returns their *median* — a robust,
   explainable aggregate, not the value of the specific street.
2. **Land value, not property value.** The Bodenrichtwert is EUR per m² of *land*. The scoring
   engine uses it only as a relative proxy (see ``scoring.PRICE_VS_LAND_VALUE``).

Requests use the WFS POST binding: the portal's web application firewall rejects filter XML in
the query string (verified 2026-09-20 — GET with FILTER/CQL_FILTER returns a WAF 400 page).
"""

from statistics import median

import httpx

from .model import Listing

DEFAULT_URL = "https://opendata.lgln.niedersachsen.de/doorman/noauth/boris_wfs"
DEFAULT_TYPENAME = "boris:BR_BodenrichtwertZonal"

# Attribution required by the licence; travels with any value this provider produces.
SOURCE = "BORIS Niedersachsen WFS 2.0 (LGLN) — Datenlizenz Deutschland Namensnennung 2.0, © GDI-NI"

# adv/BORIS nutzung codes that count as residential building land.
RESIDENTIAL_NUTZUNG = ("W", "WA", "WR", "WB")
# entwicklungszustand "B" = baureifes Land (as opposed to farmland, expectant land, ...).
BUILDABLE = "B"

_NS = {
    "wfs": "http://www.opengis.net/wfs/2.0",
    "boris": "http://www.adv-online.de/namespaces/adv/boris/2.0",
}

_REQUEST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<wfs:GetFeature service="WFS" version="2.0.0" count="{count}"
  xmlns:wfs="http://www.opengis.net/wfs/2.0"
  xmlns:fes="http://www.opengis.net/fes/2.0"
  xmlns:boris="http://www.adv-online.de/namespaces/adv/boris/2.0">
  <wfs:Query typeNames="{typename}">
    <fes:Filter>
      <fes:PropertyIsLike wildCard="*" singleChar="?" escapeChar="\\">
        <fes:ValueReference>boris:gemeinde/boris:BR_Gemeinde/boris:name</fes:ValueReference>
        <fes:Literal>*{gemeinde}*</fes:Literal>
      </fes:PropertyIsLike>
    </fes:Filter>
  </wfs:Query>
</wfs:GetFeature>"""


def _escape(text: str) -> str:
    """Escape for an XML text node, and drop the WFS wildcards so a town cannot inject them."""
    cleaned = text.replace("*", " ").replace("?", " ").replace("\\", " ")
    return (
        cleaned.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").strip()
    )


def parse_residential_values(
    xml_text: str,
    *,
    residential: tuple[str, ...] = RESIDENTIAL_NUTZUNG,
    buildable: str | None = BUILDABLE,
) -> list[float]:
    """Pull the residential building-land Bodenrichtwerte out of a WFS FeatureCollection."""
    import xml.etree.ElementTree as ET  # stdlib; the payload is our own request's response

    root = ET.fromstring(xml_text)  # noqa: S314 — trusted public endpoint, no entity expansion
    values: list[float] = []
    for feature in root.iterfind(f".//boris:{DEFAULT_TYPENAME.split(':')[1]}", _NS):
        art = feature.findtext("boris:nutzung/boris:BR_Nutzung/boris:art", namespaces=_NS)
        if art not in residential:
            continue
        if buildable is not None:
            zustand = feature.findtext("boris:entwicklungszustand", namespaces=_NS)
            if zustand != buildable:
                continue
        raw = feature.findtext("boris:bodenrichtwert", namespaces=_NS)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            values.append(value)
    return values


class WfsBodenrichtwert:
    """Median residential Bodenrichtwert of a listing's Gemeinde, from the BORIS-NI WFS.

    Returns ``None`` — never a guess — when the town is unknown, the service is unreachable or
    the Gemeinde has no residential zone in the dataset.
    """

    def __init__(
        self,
        url: str = DEFAULT_URL,
        *,
        typename: str = DEFAULT_TYPENAME,
        max_features: int = 200,
        residential: tuple[str, ...] = RESIDENTIAL_NUTZUNG,
        buildable: str | None = BUILDABLE,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
    ):
        self.url = url
        self.typename = typename
        self.max_features = max_features
        self.residential = tuple(residential)
        self.buildable = buildable
        self._client = client
        self._timeout = timeout
        self._cache: dict[str, float | None] = {}  # per Gemeinde, per process

    def lookup(self, listing: Listing) -> float | None:
        gemeinde = _escape(listing.ort or "")
        if not gemeinde:
            return None
        if gemeinde in self._cache:
            return self._cache[gemeinde]
        value = self._fetch(gemeinde)
        self._cache[gemeinde] = value
        return value

    def _fetch(self, gemeinde: str) -> float | None:
        body = _REQUEST_TEMPLATE.format(
            count=self.max_features, typename=self.typename, gemeinde=gemeinde
        )
        client = self._client or httpx.Client(timeout=self._timeout)
        try:
            response = client.post(self.url, content=body.encode("utf-8"),
                                   headers={"Content-Type": "text/xml"})
            response.raise_for_status()
            xml_text = response.text
        except httpx.HTTPError:
            return None  # unreachable source reads as "no value" — never a fabricated number
        finally:
            if self._client is None:
                client.close()
        try:
            values = parse_residential_values(
                xml_text, residential=self.residential, buildable=self.buildable
            )
        except Exception:  # noqa: BLE001 — malformed XML must degrade, not crash a scoring run
            return None
        return round(median(values), 2) if values else None
