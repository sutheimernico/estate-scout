"""One place that wires the live Ollama assistant — used by both the API and the CLI.

Keeping the wiring here means a change to the model, the retrieval threshold or the tool set
reaches every entry point at once. The RAG index is embedded once per process and cached on
disk by corpus fingerprint (see ``rag.index.load_or_build``).
"""

from estatescout.rag.embedder import OllamaEmbedder
from estatescout.rag.index import RagIndex, load_or_build
from estatescout.scout.store import ListingStore

from .assistant import MIN_RAG_SCORE, Assistant
from .chat import OllamaChat
from .tools import listing_tools

# Built once per process; invalidated by the on-disk corpus fingerprint, not by time.
_index_cache: RagIndex | None = None


def build_assistant(store: ListingStore | None = None) -> Assistant:
    """Build the Ollama-backed assistant. Raises ``OllamaUnavailable`` if the server is down.

    Args:
        store: when given, the assistant also gets the read-only ``list_listings`` tool over
            the user's saved objects. Callers own the store's lifetime.
    """
    global _index_cache
    embedder = OllamaEmbedder()
    if _index_cache is None:
        _index_cache = load_or_build(embedder)
    return Assistant(
        OllamaChat(),
        index=_index_cache,
        embedder=embedder,
        min_score=MIN_RAG_SCORE,
        extra_tools=listing_tools(store) if store is not None else None,
    )
