"""Tests for the FastAPI surface (TestClient, assistant injected as a fake — no Ollama)."""

import pytest
from fastapi.testclient import TestClient

from estatescout.api import app, get_assistant, get_providers, get_store
from estatescout.assistant.assistant import Assistant
from estatescout.assistant.chat import FakeChat, OllamaUnavailable
from estatescout.scout.store import ListingStore

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


def _override_store_to(db_path):
    # Open a fresh connection per request (same thread as the endpoint), persisting to a temp
    # file — mirrors production and avoids SQLite's thread-affinity on a shared connection.
    def _factory():
        store = ListingStore(db_path)
        try:
            yield store
        finally:
            store.close()

    return _factory


def test_listings_create_and_list(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    try:
        r = client.post(
            "/api/listings",
            json={"price": 300_000, "living_area_sqm": 100, "bundesland": "NI", "ort": "Lingen"},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["id"] >= 1
        assert body["price_per_sqm"] == 3_000.0
        listed = client.get("/api/listings").json()
        assert any(x["ort"] == "Lingen" for x in listed)
    finally:
        app.dependency_overrides.clear()


def test_listings_invalid_input_is_400(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    try:
        r = client.post(
            "/api/listings",
            json={"price": -1, "living_area_sqm": 100, "bundesland": "NI"},
        )
        assert r.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_finance_wrong_type_is_400():
    body = {"principal": "abc", "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0}
    assert client.post("/api/finance/annuity", json=body).status_code == 400


def test_ask_returns_503_when_embedding_unavailable(monkeypatch):
    from estatescout.assistant import factory
    from estatescout.errors import OllamaUnavailable

    monkeypatch.setattr(factory, "_index_cache", None)

    def boom(embedder):
        raise OllamaUnavailable("down")

    monkeypatch.setattr(factory, "load_or_build", boom)
    assert client.post("/api/ask", json={"question": "hallo"}).status_code == 503


def test_finance_endpoint_does_not_expose_listing_tools():
    assert client.post("/api/finance/list_listings", json={}).status_code == 400


def test_listings_delete(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    try:
        created = client.post(
            "/api/listings",
            json={"price": 100_000, "living_area_sqm": 50, "bundesland": "NI"},
        ).json()
        assert client.delete(f"/api/listings/{created['id']}").status_code == 204
        assert client.delete(f"/api/listings/{created['id']}").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_listings_empty_store_returns_empty_list(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "empty.db"))
    try:
        r = client.get("/api/listings")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.clear()


def _fake_providers():
    from estatescout.scout.enrich import RegionSignal, StaticBodenrichtwert, StaticRegionSignal

    return lambda: (
        StaticBodenrichtwert({"49074": 420.0}),
        StaticRegionSignal({"49074": RegionSignal(population_trend_pct=1.2, vacancy_rate_pct=2.1)}),
    )


def _create(price=300_000, area=100, plz="49074"):
    return client.post(
        "/api/listings",
        json={"price": price, "living_area_sqm": area, "bundesland": "NI", "plz": plz},
    ).json()


def test_enrich_stores_and_returns_the_result(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    app.dependency_overrides[get_providers] = _fake_providers()
    try:
        created = _create()
        r = client.post(f"/api/listings/{created['id']}/enrich")
        assert r.status_code == 200
        body = r.json()
        assert body["bodenrichtwert_eur_per_sqm"] == 420.0
        assert body["region"]["vacancy_rate_pct"] == 2.1
        assert body["unavailable"] == {}
        assert body["enriched_at"]

        # visible on the next listings read
        listed = client.get("/api/listings").json()[0]
        assert listed["enrichment"]["bodenrichtwert_eur_per_sqm"] == 420.0
    finally:
        app.dependency_overrides.clear()


def test_enrich_without_providers_reports_provider_missing(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    try:
        created = _create()
        body = client.post(f"/api/listings/{created['id']}/enrich").json()
        assert body["bodenrichtwert_eur_per_sqm"] is None
        assert body["unavailable"]["bodenrichtwert"] == "provider_missing"
    finally:
        app.dependency_overrides.clear()


def test_enrich_unknown_listing_is_404(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    try:
        assert client.post("/api/listings/4242/enrich").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_reenriching_refreshes_enriched_at(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    app.dependency_overrides[get_providers] = _fake_providers()
    try:
        created = _create()
        first = client.post(f"/api/listings/{created['id']}/enrich").json()["enriched_at"]
        second = client.post(f"/api/listings/{created['id']}/enrich").json()["enriched_at"]
        assert second >= first
    finally:
        app.dependency_overrides.clear()
