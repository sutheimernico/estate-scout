"""Tests for the BORIS-NI Bodenrichtwert provider (no network — recorded fixture + MockTransport).

`tests/fixtures/boris_ni_lingen.xml` is a real response recorded from the public BORIS-NI WFS on
2026-09-20 (geometry stripped), so the parser is tested against the actual AdV schema.
"""

from pathlib import Path

import httpx
import pytest

from estatescout.scout.bodenrichtwert_wfs import (
    BUILDABLE,
    SOURCE,
    WfsBodenrichtwert,
    parse_residential_values,
)
from estatescout.scout.enrich import BodenrichtwertProvider
from estatescout.scout.model import Listing

FIXTURE = (Path(__file__).parent / "fixtures" / "boris_ni_lingen.xml").read_text(encoding="utf-8")


def _listing(ort: str = "Lingen") -> Listing:
    return Listing(price=300_000, living_area_sqm=100, bundesland="NI", plz="49808", ort=ort)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_satisfies_the_provider_protocol():
    assert isinstance(WfsBodenrichtwert(), BodenrichtwertProvider)


def test_parses_only_residential_buildable_zones_from_a_real_response():
    # the recorded slice holds W 46, WA 76, WA 135 plus five GB (non-residential) zones
    assert sorted(parse_residential_values(FIXTURE)) == [46.0, 76.0, 135.0]


def test_lookup_returns_the_median_of_the_residential_zones():
    provider = WfsBodenrichtwert(client=_client(lambda r: httpx.Response(200, text=FIXTURE)))
    assert provider.lookup(_listing()) == 76.0  # median of 46 / 76 / 135


def test_lookup_sends_a_wfs_post_with_the_town_in_the_filter():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["body"] = request.content.decode("utf-8")
        return httpx.Response(200, text=FIXTURE)

    WfsBodenrichtwert(client=_client(handler)).lookup(_listing("Lingen"))
    assert seen["method"] == "POST"  # GET with FILTER is blocked by the portal's WAF
    assert "*Lingen*" in seen["body"]
    assert "BR_BodenrichtwertZonal" in seen["body"]


def test_town_wildcards_cannot_be_injected_into_the_filter():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content.decode("utf-8")
        return httpx.Response(200, text=FIXTURE)

    WfsBodenrichtwert(client=_client(handler)).lookup(_listing("*A & B*"))
    # exactly one wildcard pair survives — the template's own, not the user's
    assert "<fes:Literal>*A &amp; B*</fes:Literal>" in seen["body"]
    assert "**" not in seen["body"]
    assert "<" not in "A &amp; B"  # the ampersand is escaped, the XML stays well formed


def test_unknown_town_gives_no_value_rather_than_a_guess():
    empty = (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" numberReturned="0"/>'
    )
    provider = WfsBodenrichtwert(client=_client(lambda r: httpx.Response(200, text=empty)))
    assert provider.lookup(_listing("Gibtsnicht")) is None


def test_listing_without_a_town_never_calls_the_service():
    def handler(request):
        raise AssertionError("must not hit the network without a town")

    assert WfsBodenrichtwert(client=_client(handler)).lookup(_listing("")) is None


def test_network_failure_degrades_to_no_value():
    def boom(request):
        raise httpx.ConnectError("refused", request=request)

    assert WfsBodenrichtwert(client=_client(boom)).lookup(_listing()) is None


def test_http_error_degrades_to_no_value():
    provider = WfsBodenrichtwert(client=_client(lambda r: httpx.Response(503, text="nope")))
    assert provider.lookup(_listing()) is None


def test_malformed_xml_degrades_to_no_value():
    provider = WfsBodenrichtwert(client=_client(lambda r: httpx.Response(200, text="<not xml")))
    assert provider.lookup(_listing()) is None


def test_the_town_result_is_cached_for_the_process():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(200, text=FIXTURE)

    provider = WfsBodenrichtwert(client=_client(handler))
    provider.lookup(_listing())
    provider.lookup(_listing())
    assert calls["n"] == 1


def test_licence_attribution_is_carried_with_the_provider():
    assert "Datenlizenz Deutschland" in SOURCE
    assert BUILDABLE == "B"


@pytest.mark.live
def test_live_boris_ni_returns_a_plausible_value():
    """Opt-in (`uv run pytest -m live`): hits the real public WFS."""
    value = WfsBodenrichtwert().lookup(_listing("Lingen"))
    assert value is not None and 10 < value < 5_000
