"""Embedding seam: a protocol, a local Ollama implementation, and a deterministic fake.

The corpus is small, so embeddings feed an in-memory NumPy cosine search (see ``index``).
Tests use :class:`FakeEmbedder` (no network); production uses :class:`OllamaEmbedder`.
"""

import hashlib
import math
import os
import re
from typing import Protocol, runtime_checkable

import httpx

_TOKEN = re.compile(r"\w+", re.UNICODE)


@runtime_checkable
class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class FakeEmbedder:
    """Deterministic hashing bag-of-words embedder for network-free tests.

    Not semantic, but stable across processes (hashlib, not salted ``hash()``) and
    word-overlap monotone: texts sharing tokens get a higher cosine similarity. That is
    enough to exercise retrieval and cache logic deterministically.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in _tokenize(text):
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)  # noqa: S324 (not security)
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


class OllamaEmbedder:
    """Embeds via a local Ollama server (``POST /api/embeddings``).

    The httpx client is injectable so tests can supply a ``MockTransport`` (no network).
    """

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
    ):
        self.model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self._client = client
        self._timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._client or httpx.Client(timeout=self._timeout)
        try:
            out: list[list[float]] = []
            for text in texts:
                resp = client.post(
                    f"{self.host}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                resp.raise_for_status()
                out.append(resp.json()["embedding"])
            return out
        finally:
            if self._client is None:
                client.close()
