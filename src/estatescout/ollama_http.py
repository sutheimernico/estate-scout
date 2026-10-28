"""One POST helper for both Ollama seams, so every failure maps to the same typed errors."""

import httpx

from estatescout.errors import (
    OllamaFailed,
    OllamaModelMissing,
    OllamaTimeout,
    OllamaUnavailable,
)


def _error_text(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except ValueError:
        return resp.text[:200]
    return str(body.get("error", "")) if isinstance(body, dict) else ""


def post_json(
    client: httpx.Client, url: str, payload: dict, *, model: str, host: str, timeout: float
) -> dict:
    """POST to Ollama and return the JSON body; raise a typed, actionable error otherwise.

    Distinguishes "not reachable" (connect error) from "too slow" (timeout) from "model not
    pulled" (404 naming the model) — the three need different fixes from the user.
    """
    try:
        resp = client.post(url, json=payload)
    except httpx.TimeoutException as err:
        raise OllamaTimeout(model, timeout) from err
    except httpx.HTTPError as err:  # ConnectError and friends
        raise OllamaUnavailable(
            f"Ollama ist nicht erreichbar unter {host}. Starte den Server mit: ollama serve"
        ) from err
    if resp.status_code == 404 and "not found" in _error_text(resp).lower():
        raise OllamaModelMissing(model)
    if resp.is_error:
        raise OllamaFailed(
            f"Ollama meldet Fehler {resp.status_code}: {_error_text(resp) or 'ohne Details'}"
        )
    result: dict = resp.json()
    return result
