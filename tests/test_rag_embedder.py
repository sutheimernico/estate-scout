"""Tests for the embedding seam (FakeEmbedder + OllamaEmbedder via MockTransport)."""

import json
import math

import httpx
import pytest

from estatescout.rag.embedder import Embedder, FakeEmbedder, OllamaEmbedder


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)


def test_fake_embedder_satisfies_protocol():
    assert isinstance(FakeEmbedder(), Embedder)


def test_fake_embedder_is_deterministic_and_normalized():
    e = FakeEmbedder(dim=128)
    v1 = e.embed(["Grunderwerbsteuer in Niedersachsen"])[0]
    v2 = e.embed(["Grunderwerbsteuer in Niedersachsen"])[0]
    assert v1 == v2
    assert len(v1) == 128
    assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0, rel_tol=1e-9)


def test_fake_embedder_word_overlap_raises_similarity():
    e = FakeEmbedder()
    query = e.embed(["Wie hoch ist die Grunderwerbsteuer in Niedersachsen?"])[0]
    related = e.embed(["Die Grunderwerbsteuer in Niedersachsen beträgt fünf Prozent."])[0]
    unrelated = e.embed(["Der Kater schläft den ganzen Tag auf dem Sofa."])[0]
    assert _cosine(query, related) > _cosine(query, unrelated)


def test_ollama_embedder_posts_and_parses():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"embedding": [0.1, 0.2, 0.3]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    emb = OllamaEmbedder(model="test-model", host="http://testhost:11434", client=client)
    result = emb.embed(["hello"])
    assert result == [[0.1, 0.2, 0.3]]
    assert seen["path"] == "/api/embeddings"
    assert seen["payload"] == {"model": "test-model", "prompt": "hello"}


def test_ollama_embedder_maps_connect_error_to_unavailable():
    from estatescout.errors import OllamaUnavailable

    def raise_connect(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(raise_connect))
    with pytest.raises(OllamaUnavailable):
        OllamaEmbedder(client=client).embed(["hallo"])
