"""Shared error types (kept dependency-free so rag/ and assistant/ can both use them)."""


class OllamaUnavailable(RuntimeError):
    """Raised when the local Ollama server cannot be reached — callers degrade honestly."""
