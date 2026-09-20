"""FastAPI surface: deterministic finance endpoints + the assistant chat endpoint.

`POST /api/finance/{calc}` runs a calculator directly (no LLM). `POST /api/ask` runs the
tool-calling assistant. The assistant is provided via a dependency so tests can inject a fake
(no Ollama). Every response carries the disclaimer.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .assistant.assistant import DISCLAIMER, Assistant
from .assistant.chat import OllamaUnavailable
from .assistant.factory import build_assistant
from .assistant.tools import dispatch
from .finance.rates_live import market_rate
from .scout.enrich import (
    BodenrichtwertProvider,
    Enrichment,
    RegionSignalProvider,
    configured_providers,
    enrich,
)
from .scout.enrich import to_dict as enrichment_to_dict
from .scout.model import Listing
from .scout.scoring import ScoreReport, score_listing
from .scout.scoring import to_dict as score_to_dict
from .scout.store import DEFAULT_DB, ListingStore, StoredEnrichment

app = FastAPI(title="estate-scout", description="Local real-estate knowledge & finance assistant.")


class FinanceResponse(BaseModel):
    result: dict
    disclaimer: str = DISCLAIMER


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    tool_calls: list[dict] = []
    sources: list[str] = []
    disclaimer: str = DISCLAIMER


class ListingIn(BaseModel):
    price: float
    living_area_sqm: float
    bundesland: str
    plz: str = ""
    ort: str = ""
    rooms: float | None = None
    year_built: int | None = None
    object_type: str = "wohnung"
    features: list[str] = []
    source_url: str = ""


class RegionSignalOut(BaseModel):
    population_trend_pct: float | None = None
    vacancy_rate_pct: float | None = None


class EnrichmentOut(BaseModel):
    bodenrichtwert_eur_per_sqm: float | None = None
    region: RegionSignalOut | None = None
    # signal -> "provider_missing" | "no_data"; never a fabricated value
    unavailable: dict[str, str] = {}
    enriched_at: str | None = None


class SubScoreOut(BaseModel):
    name: str
    value: int | None = None
    weight: float
    detail: dict = {}
    reason: str | None = None


class ScoreOut(BaseModel):
    total: int | None = None  # null means "not computable", never a fabricated 0
    subscores: list[SubScoreOut] = []
    weights_used: dict[str, float] = {}
    confidence: float = 0.0
    inputs_available: int = 0
    inputs_expected: int = 0
    reasons: dict[str, str] = {}
    as_of: str = ""


class ScoreSummary(BaseModel):
    """What the listings table needs — the drilldown fetches the full report."""

    total: int | None = None
    confidence: float = 0.0


class ListingOut(ListingIn):
    id: int
    price_per_sqm: float
    enrichment: EnrichmentOut | None = None
    score: ScoreSummary | None = None  # only for enriched listings


def _enrichment_out(enrichment: Enrichment, enriched_at: str | None) -> EnrichmentOut:
    return EnrichmentOut(**enrichment_to_dict(enrichment), enriched_at=enriched_at)


def _score_of(listing: Listing, stored: StoredEnrichment | None, rent: float | None):
    """Score against the stored enrichment. Unenriched listings get no score at all."""
    if stored is None:
        return None
    return score_listing(listing, stored.enrichment, monthly_cold_rent=rent)


def _to_out(listing: Listing, stored: StoredEnrichment | None = None) -> ListingOut:
    report = _score_of(listing, stored, None)
    return ListingOut(
        id=listing.id or 0,
        price=listing.price,
        living_area_sqm=listing.living_area_sqm,
        bundesland=listing.bundesland,
        plz=listing.plz,
        ort=listing.ort,
        rooms=listing.rooms,
        year_built=listing.year_built,
        object_type=listing.object_type,
        features=list(listing.features),
        source_url=listing.source_url,
        price_per_sqm=round(listing.price_per_sqm, 2),
        enrichment=(
            None if stored is None else _enrichment_out(stored.enrichment, stored.enriched_at)
        ),
        score=(
            None
            if report is None
            else ScoreSummary(total=report.total, confidence=round(report.confidence, 3))
        ),
    )


def get_assistant() -> Iterator[Assistant]:
    """Provide the live Ollama-backed assistant. Overridden in tests with a fake."""
    store = ListingStore(DEFAULT_DB)
    try:
        assistant = build_assistant(store)
    except OllamaUnavailable as e:
        store.close()
        raise HTTPException(status_code=503, detail=str(e)) from None
    try:
        yield assistant
    finally:
        store.close()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


class MarketRateOut(BaseModel):
    annual_rate_percent: float
    as_of: str
    source: str
    origin: str  # bundesbank_live | bundesbank_cache | static_fallback
    disclaimer: str = DISCLAIMER


@app.get("/api/market-rate", response_model=MarketRateOut)
def get_market_rate() -> MarketRateOut:
    """Current average mortgage rate, labelled with where the number came from."""
    rate = market_rate()
    return MarketRateOut(
        annual_rate_percent=rate.annual_rate_percent,
        as_of=rate.as_of,
        source=rate.source,
        origin=rate.origin,
    )


@app.post("/api/finance/{calc}", response_model=FinanceResponse)
def finance(calc: str, args: Annotated[dict, Body()]) -> FinanceResponse:
    try:
        result = dispatch(calc, args)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return FinanceResponse(result=result)


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest, assistant: Annotated[Assistant, Depends(get_assistant)]) -> AskResponse:
    try:
        resp = assistant.ask(req.question)
    except OllamaUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from None
    return AskResponse(
        answer=resp.answer,
        tool_calls=resp.tool_calls,
        sources=resp.sources,
        disclaimer=resp.disclaimer,
    )


def get_store() -> Iterator[ListingStore]:
    """Provide a listing store per request (overridden in tests). Closes after the response."""
    store = ListingStore(DEFAULT_DB)
    try:
        yield store
    finally:
        store.close()


@app.post("/api/listings", response_model=ListingOut, status_code=201)
def create_listing(
    data: ListingIn, store: Annotated[ListingStore, Depends(get_store)]
) -> ListingOut:
    try:
        listing = Listing(
            price=data.price,
            living_area_sqm=data.living_area_sqm,
            bundesland=data.bundesland,
            plz=data.plz,
            ort=data.ort,
            rooms=data.rooms,
            year_built=data.year_built,
            object_type=data.object_type,
            features=tuple(data.features),
            source_url=data.source_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return _to_out(store.add(listing))


@app.get("/api/listings", response_model=list[ListingOut])
def list_listings(store: Annotated[ListingStore, Depends(get_store)]) -> list[ListingOut]:
    enriched = store.enrichment_map()
    return [_to_out(x, enriched.get(x.id or 0)) for x in store.list()]


def get_providers() -> tuple[BodenrichtwertProvider | None, RegionSignalProvider | None]:
    """Enrichment providers for this deployment (overridden in tests with static fakes)."""
    return configured_providers()


Providers = Annotated[
    tuple[BodenrichtwertProvider | None, RegionSignalProvider | None], Depends(get_providers)
]


@app.post("/api/listings/{listing_id}/enrich", response_model=EnrichmentOut)
def enrich_listing(
    listing_id: int,
    store: Annotated[ListingStore, Depends(get_store)],
    providers: Providers,
) -> EnrichmentOut:
    """Run the configured providers for one listing, persist and return the result."""
    listing = store.get(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail=f"listing {listing_id} not found")
    bodenrichtwert, region = providers
    result = enrich(listing, bodenrichtwert=bodenrichtwert, region=region)
    store.set_enrichment(listing_id, result)
    stored = store.get_enrichment(listing_id)
    return _enrichment_out(result, stored.enriched_at if stored else None)


def _score_out(report: ScoreReport) -> ScoreOut:
    return ScoreOut(**score_to_dict(report))


@app.get("/api/listings/{listing_id}/score", response_model=ScoreOut)
def get_listing_score(
    listing_id: int,
    store: Annotated[ListingStore, Depends(get_store)],
    monthly_cold_rent: float | None = None,
) -> ScoreOut:
    """Score a listing from its stored enrichment. Pass a rent to unlock the yield block."""
    listing = store.get(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail=f"listing {listing_id} not found")
    stored = store.get_enrichment(listing_id)
    if stored is None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"listing {listing_id} has no enrichment yet — "
                f"POST /api/listings/{listing_id}/enrich first"
            ),
        )
    return _score_out(
        score_listing(listing, stored.enrichment, monthly_cold_rent=monthly_cold_rent)
    )


@app.delete("/api/listings/{listing_id}", status_code=204)
def delete_listing(listing_id: int, store: Annotated[ListingStore, Depends(get_store)]) -> None:
    if not store.delete(listing_id):
        raise HTTPException(status_code=404, detail=f"listing {listing_id} not found")


# Serve the built React chat tab from frontend/dist, if it has been built. Mounted last so the
# /api/* routes above always take precedence. Absent build → API-only (honest degradation).
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
