"""Tests for the FastAPI surface (TestClient, assistant injected as a fake — no Ollama)."""

import pytest
from fastapi.testclient import TestClient

from estatescout.api import app, get_assistant
from estatescout.assistant.assistant import Assistant
from estatescout.assistant.chat import FakeChat, OllamaUnavailable

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_finance_annuity_endpoint():
    body = {"principal": 300_000, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0}
    r = client.post("/api/finance/annuity", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["result"]["monthly_payment"] == 1_400.0
    assert data["disclaimer"]


def test_finance_purchase_costs_endpoint():
    body = {"purchase_price": 300_000, "bundesland": "NRW"}
    r = client.post("/api/finance/purchase_costs", json=body)
    assert r.status_code == 200
    assert r.json()["result"]["grunderwerbsteuer"] == 19_500.0


def test_finance_unknown_calc_is_400():
    r = client.post("/api/finance/nope", json={})
    assert r.status_code == 400


def test_finance_missing_required_is_400():
    r = client.post("/api/finance/annuity", json={"principal": 300_000})
    assert r.status_code == 400


def test_ask_endpoint_with_injected_assistant():
    def fake_assistant() -> Assistant:
        scripted = [{"role": "assistant", "content": "Ein Kaufpreisfaktor ist ..."}]
        return Assistant(FakeChat(scripted))

    app.dependency_overrides[get_assistant] = fake_assistant
    try:
        r = client.post("/api/ask", json={"question": "Was ist ein Kaufpreisfaktor?"})
        assert r.status_code == 200
        data = r.json()
        assert data["answer"].startswith("Ein Kaufpreisfaktor")
        assert data["disclaimer"]
    finally:
        app.dependency_overrides.clear()


def test_ask_endpoint_returns_503_when_ollama_down():
    class DownModel:
        def chat(self, messages, tools=None):
            raise OllamaUnavailable("down")

    app.dependency_overrides[get_assistant] = lambda: Assistant(DownModel())
    try:
        r = client.post("/api/ask", json={"question": "hallo"})
        assert r.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("calc", ["annuity", "purchase_costs", "affordability", "yield_metrics"])
def test_all_finance_calcs_are_routable(calc):
    # missing args → 400 (not 404): the route exists for every calculator
    assert client.post(f"/api/finance/{calc}", json={}).status_code == 400
