# Bodenrichtwert: which source, and why

**Decision date:** 2026-09-20 · **Branch taken:** 1 (BORIS Niedersachsen WFS) · Plan:
`docs/superpowers/plans/2026-07-20-stage2-scoring-and-shine.md`, Task 12.

## The decision, top-down

1. **BORIS-NI (Niedersachsen) WFS — taken.** `https://opendata.lgln.niedersachsen.de/doorman/noauth/boris_wfs`
   serves OGC WFS 2.0 with the feature type `boris:BR_BodenrichtwertZonal`. Verified on
   2026-09-20: `GetCapabilities` and `GetFeature` answer **without registration and without a
   key**, licensed **Datenlizenz Deutschland Namensnennung 2.0** (`dl-de/by-2.0`), attribution
   "© GDI-NI". That satisfies both the "free, keyless" constraint and ADR-0001 (documented
   machine interface, no HTML scraping).
2. Other Bundesländer — not needed, branch 1 works. Niedersachsen is the owner's focus region;
   Berlin, Hamburg and NRW publish comparable WFS endpoints if the scope ever widens.
3. CSV import provider — **not built.** The plan says stop at the first branch that works.

## How it is queried

`src/estatescout/scout/bodenrichtwert_wfs.py` posts a WFS 2.0 `GetFeature` with an FES
`PropertyIsLike` filter on `boris:gemeinde/boris:BR_Gemeinde/boris:name`, using the listing's
`ort`.

**The POST binding is required.** A `GET` carrying `FILTER=` or `CQL_FILTER=` is rejected by the
portal's web application firewall with an HTML "Zurückgewiesene Anfrage" 400 page (verified
2026-09-20), not by the WFS itself. Plain `GET` without a filter works, so the block is the
firewall's query-string inspection.

From the returned zones the provider keeps residential building land
(`nutzung/art` ∈ `W, WA, WR, WB` and `entwicklungszustand == B`) and returns the **median**.

## What this number is, and what it is not

- It is a **municipality-level median**, not the zone of the specific address. A `Listing`
  records a PLZ and a town, never coordinates, so a point-in-polygon query is impossible
  without geocoding — which would add a second external service for little gain.
- It is **land value** (EUR per m² of land), not property value. The scoring engine uses it
  only as a relative proxy; see `scoring.PRICE_VS_LAND_VALUE` and the docstring there.
- Unreachable service, unknown town or no residential zone all yield `None`. Nothing is
  estimated, interpolated or carried over from another town.

## Configuration

`config/providers.yaml`:

```yaml
bodenrichtwert:
  provider: wfs_ni     # none | static | wfs_ni
```

`none` is the honest default for a region the WFS does not cover — the enrichment then records
`provider_missing` and the score reports the gap. `static` uses a `{plz: EUR/m²}` table the user
maintains by hand from BORIS or the Gutachterausschuss.

The test suite never touches the network: `tests/conftest.py` pins the provider config to
`none`, the parser is tested against a recorded real response
(`tests/fixtures/boris_ni_lingen.xml`), and the one live check is opt-in
(`uv run pytest -m live`).

## Open

- **Region signal** (population trend, vacancy rate) still has no keyless machine interface in
  this project. Zensus/Destatis publish the data but not in a form this app reads yet, so
  `region_signal.provider` stays `none` and the score reports `provider_missing` — honestly,
  rather than with an invented number.
