"""Chat-model seam: a protocol, a local Ollama implementation, and a scripted fake.

Ollama's ``/api/chat`` returns tool calls with ``arguments`` already parsed to a dict (unlike
OpenAI, which returns a JSON string), so no argument parsing is needed here.
"""

import os
from typing import Protocol, runtime_checkable

import httpx


class OllamaUnavailable(RuntimeError):
    """Raised when the local Ollama server cannot be reached — callers degrade honestly."""


@runtime_checkable
class ChatModel(Protocol):
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Return the assistant message dict (may contain ``tool_calls``)."""
        ...


class OllamaChat:
    """Chats via a local Ollama server (``POST /api/chat``). httpx client is injectable."""

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = 120.0,
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self._client = client
        self._timeout = timeout

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        client = self._client or httpx.Client(timeout=self._timeout)
        try:
            payload: dict = {"model": self.model, "messages": messages, "stream": False}
            if tools:
                payload["tools"] = tools
            try:
                resp = client.post(f"{self.host}/api/chat", json=payload)
            except httpx.HTTPError as e:  # ConnectError, timeout, etc.
                raise OllamaUnavailable(f"Ollama not reachable at {self.host}: {e}") from e
            resp.raise_for_status()
            return resp.json()["message"]
        finally:
            if self._client is None:
                client.close()


class FakeChat:
    """Returns pre-scripted assistant messages in order; records what it was called with."""

    def __init__(self, scripted: list[dict]):
        self._scripted = list(scripted)
        self.calls: list[dict] = []

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        self.calls.append({"messages": list(messages), "tools": tools})
        if not self._scripted:
            raise AssertionError("FakeChat ran out of scripted responses")
        return self._scripted.pop(0)
