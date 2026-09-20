"""Tests for the live Bundesbank mortgage-rate provider (httpx mocked — no network in the suite)."""

import json
import time

import httpx
import pytest

from estatescout.finance.rates_live import (
    ORIGIN_CACHE,
    ORIGIN_FALLBACK,
    ORIGIN_LIVE,
    market_rate,
)

# A trimmed copy of the real Bundesbank CSV response (fetched 2026-09-20).
CSV = (
    "DATAFLOW;BBK_STD_FREQ;BBK_STD_AREA;TIME_PERIOD;OBS_VALUE;BBK_UNIT;BBK_TITLE\n"
    "BBK:BBIM1(1.0);M;DE;2026-07;3.94;% p.a.;"
    "Effektivzinssätze Banken DE / Neugeschäft / Wohnungsbaukredite an private Haushalte\n"
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_live_fetch_returns_the_rate_with_its_provenance(tmp_path):
    rate = market_rate(
        client=_client(lambda r: httpx.Response(200, text=CSV)),
        cache_path=tmp_path / "cache.json",
    )
    assert rate.annual_rate_percent == pytest.approx(3.94)
    assert rate.as_of == "2026-07"
    assert rate.origin == ORIGIN_LIVE
    assert "Bundesbank" in rate.source
    assert "BBIM1/M.DE.B.A2C.A.R.A.2250.EUR.N" in rate.source


def test_the_request_goes_to_the_documented_series(tmp_path):
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, text=CSV)

    market_rate(client=_client(handler), cache_path=tmp_path / "cache.json")
    assert "BBIM1/M.DE.B.A2C.A.R.A.2250.EUR.N" in seen["url"]
    assert "lastNObservations=1" in seen["url"]


def test_second_call_is_served_from_the_cache(tmp_path):
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, text=CSV)

    cache = tmp_path / "cache.json"
    market_rate(client=_client(handler), cache_path=cache)
    second = market_rate(client=_client(handler), cache_path=cache)
    assert calls["n"] == 1
    assert second.origin == ORIGIN_CACHE
    assert second.annual_rate_percent == pytest.approx(3.94)


def test_an_expired_cache_is_refetched(tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps(
            {
                "annual_rate_percent": 1.11,
                "source": "old",
                "as_of": "2020-01",
                "fetched_at": time.time() - 10_000,
            }
        ),
        encoding="utf-8",
    )
    rate = market_rate(
        client=_client(lambda r: httpx.Response(200, text=CSV)),
        cache_path=cache,
        ttl_seconds=3_600,
    )
    assert rate.annual_rate_percent == pytest.approx(3.94)
    assert rate.origin == ORIGIN_LIVE


def test_a_corrupt_cache_is_ignored_not_fatal(tmp_path):
    cache = tmp_path / "cache.json"
    cache.write_text("{not json", encoding="utf-8")
    rate = market_rate(client=_client(lambda r: httpx.Response(200, text=CSV)), cache_path=cache)
    assert rate.origin == ORIGIN_LIVE


def test_network_failure_falls_back_to_config_and_says_so(tmp_path):
    def boom(request):
        raise httpx.ConnectError("refused", request=request)

    rate = market_rate(client=_client(boom), cache_path=tmp_path / "cache.json")
    assert rate.origin == ORIGIN_FALLBACK
    assert "static fallback" in rate.source
    assert rate.annual_rate_percent > 0


def test_http_error_falls_back(tmp_path):
    rate = market_rate(
        client=_client(lambda r: httpx.Response(500, text="boom")),
        cache_path=tmp_path / "cache.json",
    )
    assert rate.origin == ORIGIN_FALLBACK


def test_empty_response_falls_back(tmp_path):
    header_only = "DATAFLOW;TIME_PERIOD;OBS_VALUE\n"
    rate = market_rate(
        client=_client(lambda r: httpx.Response(200, text=header_only)),
        cache_path=tmp_path / "cache.json",
    )
    assert rate.origin == ORIGIN_FALLBACK


def test_the_fallback_value_is_configured_with_source_and_date():
    from estatescout.finance.config import load_config

    block = load_config()["market_rate"]
    assert block["as_of"]
    assert "Bundesbank" in block["source"]
    assert 0 < float(block["fallback_annual_rate_percent"]) < 25


@pytest.mark.live
def test_live_bundesbank_answers_with_a_plausible_rate(tmp_path):
    """Opt-in (`uv run pytest -m live`): hits the real public Bundesbank API."""
    rate = market_rate(cache_path=tmp_path / "cache.json")
    assert rate.origin == ORIGIN_LIVE
    assert 0.1 < rate.annual_rate_percent < 15


def test_the_assistant_tool_reports_the_origin(monkeypatch):
    """The model must be able to tell a live rate from a stale fallback."""
    from estatescout.assistant import tools as tools_mod
    from estatescout.finance.rates_live import MarketRate

    monkeypatch.setattr(
        tools_mod,
        "market_rate",
        lambda: MarketRate(3.94, "Deutsche Bundesbank, BBIM1/...", "2026-07", ORIGIN_LIVE),
    )
    out = tools_mod.dispatch("market_rate", {})
    assert out == {
        "annual_rate_percent": 3.94,
        "as_of": "2026-07",
        "source": "Deutsche Bundesbank, BBIM1/...",
        "origin": ORIGIN_LIVE,
    }
