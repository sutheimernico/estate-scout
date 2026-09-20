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

from .assistant.assistant import DISCLAIMER, MIN_RAG_SCORE, Assistant
from .assistant.chat import OllamaChat, OllamaUnavailable
from .assistant.tools import dispatch, listing_tools
from .rag.embedder import OllamaEmbedder
from .rag.index import RagIndex, load_or_build
from .scout.model import Listing
from .scout.store import DEFAULT_DB, ListingStore

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


class ListingOut(ListingIn):
    id: int
    price_per_sqm: float


def _to_out(listing: Listing) -> ListingOut:
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
    )


# Built once per process, invalidated via the on-disk corpus fingerprint (rag.index).
_index_cache: RagIndex | None = None


def get_assistant() -> Iterator[Assistant]:
    """Build the live Ollama-backed assistant. Overridden in tests with a fake."""
    global _index_cache
    embedder = OllamaEmbedder()
    if _index_cache is None:
        try:
            _index_cache = load_or_build(embedder)
        except OllamaUnavailable as e:
            raise HTTPException(status_code=503, detail=str(e)) from None
    store = ListingStore(DEFAULT_DB)
    try:
        yield Assistant(
            OllamaChat(),
            index=_index_cache,
            embedder=embedder,
            min_score=MIN_RAG_SCORE,
            extra_tools=listing_tools(store),
        )
    finally:
        store.close()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


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
    return [_to_out(x) for x in store.list()]


# Serve the built React chat tab from frontend/dist, if it has been built. Mounted last so the
# /api/* routes above always take precedence. Absent build → API-only (honest degradation).
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
