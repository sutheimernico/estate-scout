"""In-memory vector index over the knowledge corpus.

The corpus is small, so a NumPy cosine search over normalized chunk embeddings is enough —
no external vector DB (that comparison is scouting-rag's job). The embedding matrix is cached
to disk (regenerable, gitignored) so re-embedding only happens when the corpus changes.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .chunker import Chunk, chunk_markdown
from .embedder import Embedder

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_DIR = _REPO_ROOT / "knowledge"
DEFAULT_INDEX_DIR = _REPO_ROOT / "data" / "rag_index"


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    heading: str
    text: str
    score: float


def load_corpus(
    corpus_dir: Path | str = DEFAULT_CORPUS_DIR, *, max_chars: int = 1000
) -> list[Chunk]:
    """Read every ``*.md`` in the corpus dir and chunk it (sorted by filename for stability)."""
    corpus_dir = Path(corpus_dir)
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(text, path.name, max_chars=max_chars))
    return chunks


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class RagIndex:
    """Chunks + a row-normalized embedding matrix, with cosine retrieval."""

    def __init__(self, chunks: list[Chunk], matrix: np.ndarray):
        if len(chunks) != matrix.shape[0]:
            raise ValueError("chunks and matrix rows must align")
        if not chunks:
            raise ValueError("index is empty")
        self.chunks = chunks
        self.matrix = _normalize_rows(matrix.astype(np.float32))

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> "RagIndex":
        if not chunks:
            raise ValueError("cannot build an index from an empty corpus")
        vectors = embedder.embed([c.text for c in chunks])
        return cls(chunks, np.array(vectors, dtype=np.float32))

    def retrieve(
        self, query: str, embedder: Embedder, k: int = 4, *, min_score: float = -1.0
    ) -> list[RetrievedChunk]:
        """Top-k cosine hits. ``min_score`` drops weak hits (-1.0 = no filtering)."""
        if k <= 0:
            raise ValueError("k must be > 0")
        qv = np.array(embedder.embed([query])[0], dtype=np.float32)
        norm = np.linalg.norm(qv) or 1.0
        sims = self.matrix @ (qv / norm)
        top = np.argsort(sims)[::-1][:k]
        return [
            RetrievedChunk(
                source=self.chunks[i].source,
                heading=self.chunks[i].heading,
                text=self.chunks[i].text,
                score=float(sims[i]),
            )
            for i in top
            if sims[i] >= min_score
        ]

    def save(self, index_dir: Path | str = DEFAULT_INDEX_DIR) -> None:
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        np.save(index_dir / "embeddings.npy", self.matrix)
        payload = [{"source": c.source, "heading": c.heading, "text": c.text} for c in self.chunks]
        (index_dir / "chunks.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )

    @classmethod
    def load(cls, index_dir: Path | str = DEFAULT_INDEX_DIR) -> "RagIndex":
        index_dir = Path(index_dir)
        matrix = np.load(index_dir / "embeddings.npy")
        payload = json.loads((index_dir / "chunks.json").read_text(encoding="utf-8"))
        chunks = [Chunk(source=d["source"], heading=d["heading"], text=d["text"]) for d in payload]
        return cls(chunks, matrix)


def _fingerprint(chunks: list[Chunk], embedder: Embedder) -> str:
    """Corpus+embedder identity; any content or model change invalidates the cache."""
    h = hashlib.sha256()
    h.update(getattr(embedder, "model", type(embedder).__name__).encode("utf-8"))
    for c in chunks:
        h.update(c.source.encode("utf-8"))
        h.update(c.heading.encode("utf-8"))
        h.update(c.text.encode("utf-8"))
    return h.hexdigest()


def load_or_build(
    embedder: Embedder,
    *,
    corpus_dir: Path | str = DEFAULT_CORPUS_DIR,
    index_dir: Path | str = DEFAULT_INDEX_DIR,
) -> RagIndex:
    """Load the cached index if the corpus is unchanged; otherwise build and cache it."""
    index_dir = Path(index_dir)
    chunks = load_corpus(corpus_dir)
    fp = _fingerprint(chunks, embedder)
    meta_path = index_dir / "meta.json"
    if meta_path.exists():
        try:
            if json.loads(meta_path.read_text(encoding="utf-8")).get("fingerprint") == fp:
                return RagIndex.load(index_dir)
        except (OSError, ValueError):
            pass  # unreadable/corrupt cache → rebuild below
    index = RagIndex.build(chunks, embedder)
    index.save(index_dir)
    meta_path.write_text(json.dumps({"fingerprint": fp}), encoding="utf-8")
    return index
