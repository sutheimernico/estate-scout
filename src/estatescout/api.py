"""FastAPI surface: deterministic finance endpoints + the assistant chat endpoint.

`POST /api/finance/{calc}` runs a calculator directly (no LLM). `POST /api/ask` runs the
tool-calling assistant. The assistant is provided via a dependency so tests can inject a fake
(no Ollama). Every response carries the disclaimer.
"""

from pathlib import Path
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .assistant.assistant import DISCLAIMER, Assistant
from .assistant.chat import OllamaChat, OllamaUnavailable
from .assistant.tools import dispatch
from .rag.embedder import OllamaEmbedder
from .rag.index import RagIndex, load_corpus

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


def get_assistant() -> Assistant:
    """Build the live Ollama-backed assistant. Overridden in tests with a fake."""
    embedder = OllamaEmbedder()
    index = RagIndex.build(load_corpus(), embedder)
    return Assistant(OllamaChat(), index=index, embedder=embedder)


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


# Serve the built React chat tab from frontend/dist, if it has been built. Mounted last so the
# /api/* routes above always take precedence. Absent build → API-only (honest degradation).
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
