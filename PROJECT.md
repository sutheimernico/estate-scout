# estate-scout — Project

Local, free, honest real-estate assistant for Nico (aspiring real-estate investor, Niedersachsen /
NRW). A knowledge assistant you can ask anything about German residential property + financing,
backed by deterministic finance calculators whose numbers are always correct.

One of Nico's `*-scout` portfolio projects. Built by the autonomous loop (`AUTOPILOT.md` +
`LOOP.md`), staged so each stage ships something usable.

## Stages

1. **Knowledge & Finance Assistant** (current) — RAG over curated domain knowledge + deterministic
   finance calculators (Annuitätendarlehen, Kaufnebenkosten, Leistbarkeit, Mietrendite) + a local
   tool-calling assistant (Ollama). CLI + FastAPI + a React chat tab.
2. Scouting funnel (listings/market → score → recommend) — legal sources only, gated on research.
3. Per-object exposé evaluation — the bridge to the funnel.
4. Copilot (scheduling + notifications).
5. Unified dashboard.

## Core design constraint

Numbers come only from tested Python (`finance/`); the LLM routes and explains, never computes. A
local 7B model cannot be trusted with arithmetic — so it isn't.

## Framing

Honest harness. Not tax/investment/financing advice. No listing scraping. Runs on Nico's machine
(Ollama), no paid APIs. Every surface carries the disclaimer.

## Layout

- `src/estatescout/finance/` — deterministic calculators (trust anchor, fully tested)
- `src/estatescout/rag/` — local RAG over `knowledge/` (Ollama embeddings + NumPy cosine)
- `src/estatescout/assistant/` — Ollama tool-calling orchestration
- `scripts/` — CLI entry points · `config/` — versioned rates/thresholds (source+date)
- `docs/superpowers/specs/` — design · `docs/adr/` — decisions
- Gate: `uv run pytest -q` + `uv run ruff check .`
