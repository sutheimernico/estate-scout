#!/usr/bin/env python
"""Golden end-to-end checks against a REAL local Ollama. Invoked by scripts/verify_live.sh.

Closes the "green suite, never-verified integration" gap: the pytest suite is hermetic by
design (every Ollama call is faked), so nothing in CI proves that ``OllamaChat`` and
``OllamaEmbedder`` actually work against the real server. This script does — and skips
cleanly (exit 0) when Ollama is down, because honest degradation is not a failure.

Exit codes: 0 = all checks passed (or cleanly skipped), 1 = at least one check failed.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from estatescout.assistant.assistant import MIN_RAG_SCORE, Assistant  # noqa: E402
from estatescout.assistant.chat import OllamaChat  # noqa: E402
from estatescout.assistant.tools import listing_tools  # noqa: E402
from estatescout.errors import OllamaUnavailable  # noqa: E402
from estatescout.rag.embedder import OllamaEmbedder  # noqa: E402
from estatescout.rag.index import load_or_build  # noqa: E402
from estatescout.scout.enrich import Enrichment, RegionSignal  # noqa: E402
from estatescout.scout.model import Listing  # noqa: E402
from estatescout.scout.scoring import score_listing  # noqa: E402
from estatescout.scout.store import ListingStore  # noqa: E402

TIMEOUT = float(os.getenv("VERIFY_TIMEOUT", "900"))

_results: list[tuple[str, bool, str]] = []


def check(name: str, fn) -> bool:
    started = time.monotonic()
    try:
        detail = fn()
        ok = True
    except Exception as e:  # noqa: BLE001 — a failing check must never abort the whole run
        detail, ok = f"{type(e).__name__}: {e}", False
    took = time.monotonic() - started
    print(f"[{'PASS' if ok else 'FAIL'}] {name} ({took:.1f}s) — {detail}", flush=True)
    _results.append((name, ok, str(detail)))
    return ok


def main() -> int:
    print("estate-scout live verification (real Ollama, no fakes)\n")

    # 1. Embedder — also the gate for the RAG checks below.
    embedder = OllamaEmbedder(timeout=TIMEOUT)
    index = None

    def _embed():
        vector = embedder.embed(["Grunderwerbsteuer in Niedersachsen"])[0]
        return f"{len(vector)}-dim vector from {embedder.model}"

    embed_ok = check("embedder: OllamaEmbedder.embed", _embed)

    if embed_ok:

        def _index():
            nonlocal index
            index = load_or_build(embedder)
            return f"{len(index.chunks)} chunks indexed"

        check("rag: corpus index (cached)", _index)
    else:
        print("[SKIP] rag: corpus index — embedder unavailable", flush=True)

    # 2. Deterministic scoring — no LLM, must always hold.
    def _score():
        listing = Listing(price=300_000, living_area_sqm=100, bundesland="NI", plz="49074")
        enrichment = Enrichment(
            bodenrichtwert_eur_per_sqm=2_500.0,
            region=RegionSignal(population_trend_pct=0.5, vacancy_rate_pct=3.0),
        )
        report = score_listing(listing, enrichment, monthly_cold_rent=1_000.0)
        if report.total != 59:
            raise AssertionError(f"expected the golden total 59, got {report.total}")
        return f"total {report.total}/100, confidence {report.confidence:.0%}"

    check("scoring: golden listing", _score)

    # 3. Chat + tool calling against the real model.
    store = ListingStore(":memory:")
    store.add(Listing(price=300_000, living_area_sqm=100, bundesland="NI", ort="Lingen"))
    model = OllamaChat(timeout=TIMEOUT)
    assistant = Assistant(
        model,
        index=index,
        embedder=embedder if index is not None else None,
        min_score=MIN_RAG_SCORE,
        extra_tools=listing_tools(store),
    )

    def _tool_call():
        resp = assistant.ask(
            "Was zahle ich monatlich für 300.000 Euro Darlehen bei 3,6 % Zins und 2 % Tilgung?"
        )
        names = [t["name"] for t in resp.tool_calls]
        if "annuity" not in names:
            raise AssertionError(f"model did not call the annuity tool (called: {names or 'none'})")
        payment = next(t for t in resp.tool_calls if t["name"] == "annuity")["result"].get(
            "monthly_payment"
        )
        if payment != 1_400.0:
            raise AssertionError(f"annuity returned {payment}, expected 1400.0 from finance/")
        return f"annuity -> {payment} EUR/month; answer: {resp.answer[:70]!r}"

    check("assistant: finance tool call", _tool_call)

    if index is not None:

        def _rag():
            resp = assistant.ask("Welche Nebenkosten fallen beim Kauf in Niedersachsen an?")
            if not resp.sources:
                raise AssertionError("no knowledge sources were retrieved")
            return f"sources {resp.sources}; answer: {resp.answer[:70]!r}"

        check("assistant: RAG answer with sources", _rag)
    else:
        print("[SKIP] assistant: RAG answer — no index", flush=True)

    store.close()

    failed = [name for name, ok, _ in _results if not ok]
    print(f"\n{len(_results) - len(failed)}/{len(_results)} checks passed")
    if failed:
        print("failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OllamaUnavailable as e:
        print(f"\nOllama is not reachable ({e}) — skipping the live verification.")
        print("Start it with 'ollama serve' and pull the models, then run this again.")
        sys.exit(0)
