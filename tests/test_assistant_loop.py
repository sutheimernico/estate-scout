"""Tests for the assistant loop: tool round-trip, RAG context, error feedback, degradation."""

import pytest

from estatescout.assistant.assistant import Assistant
from estatescout.assistant.chat import FakeChat, OllamaUnavailable
from estatescout.rag.chunker import Chunk
from estatescout.rag.embedder import FakeEmbedder
from estatescout.rag.index import RagIndex


def _tool_call(name: str, args: dict) -> dict:
    call = {"function": {"name": name, "arguments": args}}
    return {"role": "assistant", "content": "", "tool_calls": [call]}


def _final(text: str) -> dict:
    return {"role": "assistant", "content": text}


def test_calc_intent_runs_tool_and_number_matches():
    model = FakeChat(
        [
            _tool_call(
                "annuity",
                {
                    "principal": 300_000,
                    "annual_rate_percent": 3.6,
                    "initial_repayment_percent": 2.0,
                },
            ),
            _final("Deine Monatsrate liegt bei 1.400 €."),
        ]
    )
    resp = Assistant(model).ask("Was zahle ich monatlich?")
    assert resp.answer == "Deine Monatsrate liegt bei 1.400 €."
    assert resp.tool_calls[0]["name"] == "annuity"
    # the surfaced number comes from finance/, not the model
    assert resp.tool_calls[0]["result"]["monthly_payment"] == pytest.approx(1_400.0)


def test_knowledge_intent_injects_rag_context_and_reports_sources():
    chunks = [
        Chunk("03-finanzierung.md", "Tilgung", "Tilgung Annuität Darlehen Zins Rate Restschuld"),
        Chunk("04-kaufnebenkosten.md", "Makler", "Makler Notar Grunderwerbsteuer Kaufnebenkosten"),
    ]
    index = RagIndex.build(chunks, FakeEmbedder())
    model = FakeChat([_final("Die Tilgung reduziert die Restschuld (03-finanzierung.md).")])
    resp = Assistant(model, index=index, embedder=FakeEmbedder()).ask(
        "Wie funktioniert die Tilgung beim Darlehen?"
    )
    assert "03-finanzierung.md" in resp.sources
    context_msgs = [
        m
        for m in model.calls[0]["messages"]
        if "Auszüge aus der Wissensbasis" in m.get("content", "")
    ]
    assert context_msgs, "RAG context should be injected into the prompt"


def test_invalid_tool_args_are_fed_back_as_error():
    model = FakeChat(
        [
            _tool_call("annuity", {"principal": 300_000}),  # missing required rate/repayment
            _final("Mir fehlen Zinssatz und Tilgung — kannst du die angeben?"),
        ]
    )
    resp = Assistant(model).ask("Rechne mal.")
    assert "error" in resp.tool_calls[0]["result"]
    assert "missing required" in resp.tool_calls[0]["result"]["error"]


def test_ollama_unavailable_propagates():
    class DownModel:
        def chat(self, messages, tools=None):
            raise OllamaUnavailable("down")

    with pytest.raises(OllamaUnavailable):
        Assistant(DownModel()).ask("hi")


def test_malformed_tool_call_is_skipped_and_answer_still_returned():
    model = FakeChat(
        [
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"nope": True}}]},
            _final("Das hat nicht geklappt — magst du die Frage umformulieren?"),
        ]
    )
    resp = Assistant(model).ask("kaputt?")
    assert resp.answer.startswith("Das hat nicht geklappt")
    assert resp.tool_calls == []


def test_string_tool_arguments_are_parsed_as_json():
    call = {
        "function": {
            "name": "annuity",
            "arguments": '{"principal": 300000, "annual_rate_percent": 3.6,'
            ' "initial_repayment_percent": 2.0}',
        }
    }
    model = FakeChat(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            _final("Die Rate beträgt 1.400 €."),
        ]
    )
    resp = Assistant(model).ask("Rate?")
    assert resp.tool_calls[0]["result"]["monthly_payment"] == pytest.approx(1_400.0)


def test_type_error_inside_tool_is_fed_back_not_raised():
    # bypasses dispatch coercion paths: unknown-string arg for a number that float() accepts
    # is coerced, so force a KeyError-ish structure instead: arguments as a list
    call = {"function": {"name": "annuity", "arguments": [1, 2, 3]}}
    model = FakeChat(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            _final("Mir fehlen die Angaben."),
        ]
    )
    resp = Assistant(model).ask("Rechne.")
    assert "error" in resp.tool_calls[0]["result"]


def test_no_context_message_when_all_hits_below_threshold():
    chunks = [Chunk("a.md", "h", "Bananenbrot Rezept Zucker Backofen")]
    index = RagIndex.build(chunks, FakeEmbedder())
    model = FakeChat([_final("Dazu enthält die Wissensbasis nichts.")])
    resp = Assistant(model, index=index, embedder=FakeEmbedder(), min_score=0.5).ask(
        "Wie hoch ist die Grunderwerbsteuer?"
    )
    assert resp.sources == []
    sent = model.calls[0]["messages"]
    assert not any("Auszüge aus der Wissensbasis" in m.get("content", "") for m in sent)


def test_assistant_lists_saved_listings_via_extra_tool():
    from estatescout.assistant.tools import listing_tools
    from estatescout.scout.model import Listing
    from estatescout.scout.store import ListingStore

    store = ListingStore(":memory:")
    store.add(Listing(price=300_000, living_area_sqm=100, bundesland="NI", ort="Lingen"))
    model = FakeChat(
        [
            {"role": "assistant", "content": "",
             "tool_calls": [{"function": {"name": "list_listings", "arguments": {}}}]},
            _final("Du hast 1 Objekt gespeichert: Lingen, 300.000 €."),
        ]
    )
    resp = Assistant(model, extra_tools=listing_tools(store)).ask("Welche Objekte habe ich?")
    assert resp.tool_calls[0]["result"]["count"] == 1
    assert resp.tool_calls[0]["result"]["listings"][0]["ort"] == "Lingen"
    sent_tools = model.calls[0]["tools"]
    assert any(t["function"]["name"] == "list_listings" for t in sent_tools)


def test_assistant_explains_a_score_it_did_not_compute():
    """The model receives the finished ScoreReport and only puts it into words."""
    from estatescout.assistant.tools import listing_tools
    from estatescout.scout.enrich import Enrichment, RegionSignal
    from estatescout.scout.model import Listing
    from estatescout.scout.store import ListingStore

    store = ListingStore(":memory:")
    saved = store.add(Listing(price=300_000, living_area_sqm=100, bundesland="NI", plz="49074"))
    store.set_enrichment(
        saved.id,
        Enrichment(
            bodenrichtwert_eur_per_sqm=2_500.0,
            region=RegionSignal(population_trend_pct=0.5, vacancy_rate_pct=3.0),
        ),
    )
    model = FakeChat(
        [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "score_listing",
                            "arguments": {"listing_id": saved.id, "monthly_cold_rent": 1000},
                        }
                    }
                ],
            },
            _final("Das Objekt kommt auf 59 von 100 — die Rendite trägt am meisten."),
        ]
    )
    resp = Assistant(model, extra_tools=listing_tools(store)).ask("Wie gut ist Objekt 1?")
    result = resp.tool_calls[0]["result"]
    assert result["total"] == 59  # computed by scoring.py, not by the model
    assert [s["value"] for s in result["subscores"]] == [67, 43, 73]
    assert "59" in resp.answer


def test_score_tool_refuses_an_unenriched_listing():
    from estatescout.assistant.tools import listing_tools
    from estatescout.scout.model import Listing
    from estatescout.scout.store import ListingStore

    store = ListingStore(":memory:")
    saved = store.add(Listing(price=300_000, living_area_sqm=100, bundesland="NI"))
    tools = listing_tools(store)
    assert "not been enriched" in tools["score_listing"].run({"listing_id": saved.id})["error"]
    assert "no listing" in tools["score_listing"].run({"listing_id": 999})["error"]
