"""Tests for the RAG index: golden retrieval over the real corpus + cache round-trip.

Uses FakeEmbedder (bag-of-words, deterministic) — good enough that a query sharing
distinctive tokens with a corpus doc retrieves that doc.
"""

import pytest

from estatescout.rag.chunker import Chunk
from estatescout.rag.embedder import FakeEmbedder
from estatescout.rag.index import RagIndex, load_corpus


def test_load_corpus_reads_markdown_docs():
    chunks = load_corpus()
    assert chunks
    assert all(c.source.endswith(".md") for c in chunks)
    assert any(c.source == "04-kaufnebenkosten.md" for c in chunks)


def test_golden_retrieval_grunderwerbsteuer():
    index = RagIndex.build(load_corpus(), FakeEmbedder())
    hits = index.retrieve("Kaufnebenkosten Grunderwerbsteuer Notar Makler", FakeEmbedder(), k=3)
    assert "04-kaufnebenkosten.md" in {h.source for h in hits}


def test_golden_retrieval_scraping_legality():
    index = RagIndex.build(load_corpus(), FakeEmbedder())
    hits = index.retrieve("Scraping ImmoScout24 Cloudflare Bot-Schutz AGB", FakeEmbedder(), k=3)
    assert "06-datenzugriff-listings.md" in {h.source for h in hits}


def test_cache_round_trip(tmp_path):
    chunks = [
        Chunk("a.md", "Zinsen", "Zinsen Tilgung Annuität Darlehen Rate"),
        Chunk("b.md", "Lage", "Lage ÖPNV Nahversorgung Demografie Leerstand"),
    ]
    built = RagIndex.build(chunks, FakeEmbedder())
    built.save(tmp_path)
    loaded = RagIndex.load(tmp_path)
    assert loaded.matrix.shape == built.matrix.shape
    assert [c.source for c in loaded.chunks] == ["a.md", "b.md"]
    top = loaded.retrieve("Wie funktioniert Tilgung beim Darlehen?", FakeEmbedder(), k=1)
    assert top[0].source == "a.md"


def test_build_empty_corpus_raises():
    with pytest.raises(ValueError):
        RagIndex.build([], FakeEmbedder())


def test_retrieve_invalid_k_raises():
    index = RagIndex.build([Chunk("a.md", "H", "some text")], FakeEmbedder())
    with pytest.raises(ValueError):
        index.retrieve("q", FakeEmbedder(), k=0)


def test_retrieve_filters_hits_below_min_score():
    emb = FakeEmbedder()
    chunks = [
        Chunk(source="a.md", heading="h", text="Grunderwerbsteuer Niedersachsen Kaufnebenkosten"),
        Chunk(source="b.md", heading="h", text="Bananenbrot Rezept Zucker Backofen"),
    ]
    idx = RagIndex.build(chunks, emb)
    hits = idx.retrieve("Grunderwerbsteuer Niedersachsen Kaufnebenkosten", emb, k=2, min_score=0.5)
    assert [h.source for h in hits] == ["a.md"]
