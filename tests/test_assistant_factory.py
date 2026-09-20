"""Tests for the shared assistant wiring (API and CLI must build the same assistant)."""

import pytest

from estatescout.assistant import factory
from estatescout.assistant.assistant import MIN_RAG_SCORE
from estatescout.rag.chunker import Chunk
from estatescout.rag.embedder import FakeEmbedder
from estatescout.rag.index import RagIndex
from estatescout.scout.model import Listing
from estatescout.scout.store import ListingStore


@pytest.fixture
def fake_index(monkeypatch):
    """Replace the (networked) index build with a tiny in-memory index."""
    index = RagIndex.build([Chunk("a.md", "h", "Grunderwerbsteuer Niedersachsen")], FakeEmbedder())
    monkeypatch.setattr(factory, "_index_cache", None)
    monkeypatch.setattr(factory, "load_or_build", lambda embedder: index)
    return index


def test_build_assistant_wires_rag_and_finance_tools(fake_index):
    assistant = factory.build_assistant()
    assert assistant.index is fake_index
    assert assistant.min_score == MIN_RAG_SCORE
    assert "annuity" in assistant._tools
    assert "list_listings" not in assistant._tools  # no store passed


def test_build_assistant_adds_listing_tools_when_a_store_is_given(fake_index):
    store = ListingStore(":memory:")
    store.add(Listing(price=300_000, living_area_sqm=100, bundesland="NI", ort="Lingen"))
    assistant = factory.build_assistant(store)
    assert "list_listings" in assistant._tools
    assert assistant._tools["list_listings"].run({})["count"] == 1


def test_build_assistant_reuses_the_index_across_calls(monkeypatch):
    index = RagIndex.build([Chunk("a.md", "h", "Zins Tilgung")], FakeEmbedder())
    calls = {"n": 0}

    def counting(embedder):
        calls["n"] += 1
        return index

    monkeypatch.setattr(factory, "_index_cache", None)
    monkeypatch.setattr(factory, "load_or_build", counting)
    factory.build_assistant()
    factory.build_assistant()
    assert calls["n"] == 1
