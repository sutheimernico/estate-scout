"""Shared error types (kept dependency-free so rag/ and assistant/ can both use them).

Each class carries a German, actionable message: the API forwards ``str(error)`` to the UI.
"""


class OllamaUnavailable(RuntimeError):
    """The local Ollama server cannot be reached — callers degrade honestly."""


class OllamaModelMissing(RuntimeError):
    """Ollama runs, but the requested model has not been pulled."""

    def __init__(self, model: str):
        self.model = model
        super().__init__(
            f"Das Modell „{model}“ fehlt in Ollama. Installiere es mit: ollama pull {model}"
        )


class OllamaTimeout(RuntimeError):
    """Ollama is reachable but did not answer in time (typically a slow CPU run)."""

    def __init__(self, model: str, seconds: float):
        self.model = model
        super().__init__(
            f"Das Modell „{model}“ antwortet zu langsam (Zeitlimit {seconds:.0f} s). "
            "Nochmal versuchen, ein kleineres Modell wählen (OLLAMA_MODEL) oder "
            "OLLAMA_TIMEOUT erhöhen."
        )


class OllamaFailed(RuntimeError):
    """Ollama answered with an unexpected error status."""
