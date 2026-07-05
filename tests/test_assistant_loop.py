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
    context_msgs = [m for m in model.calls[0]["messages"] if "Auszüge" in m.get("content", "")]
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
