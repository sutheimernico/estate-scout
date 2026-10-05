# estate-scout — Stage 1: Knowledge & Finance Assistant (Design)

**Date:** 2026-07-05
**Status:** Approved (brainstorming) — binding design for Stage 1.
**Author:** autopilot loop for the owner.

## 1. Purpose & framing

A local, free, **honest harness** for real-estate decisions: a knowledge assistant you can
ask anything about German residential property + financing, backed by **deterministic finance
calculators** whose numbers are always correct. Long-term vision (multiple stages) is a full
"real-estate scout" in the family of the owner's other `*-scout` projects; this spec covers **Stage 1
only**.

Explicitly NOT: investment/tax/financing advice, listing scraping, price forecasts. Every surface
carries a disclaimer. Runs entirely on the owner's machine (Ollama), no paid APIs.

## 2. The core honesty constraint

A local 7B model cannot be trusted with arithmetic. Therefore **all numbers come from tested
Python code** (`finance/`), never from the LLM. The LLM understands the question, calls the right
calculator as a tool, and explains the returned numbers in words. This is the architectural spine.

## 3. Architecture — three isolated layers

### 3.1 Finance core (`finance/`)
Pure, typed, unit-tested functions. No LLM dependency. The single source of truth for every number.

- `annuity` — Annuitätendarlehen: monthly payment, amortization schedule (remaining debt per
  year), total interest, payoff duration; supports optional `sondertilgung`.
- `purchase_costs` — Kaufnebenkosten: Grunderwerbsteuer (rate **per Bundesland**, from config),
  notary + Grundbuch, Makler → total ancillary-cost quota and equity needed.
- `affordability` — max purchase price from net income, equity, rate, interest, initial repayment,
  and a payment-to-income rule of thumb.
- `yield_metrics` — gross/net rental yield, Kaufpreisfaktor (price-to-annual-rent multiplier).

Region- and time-sensitive constants (Grunderwerbsteuer per Bundesland, notary/Makler %, rule-of-
thumb thresholds) live in **versioned YAML config** under `config/`, each value tagged with source
+ date because they age. Functions read config, never hardcode.

### 3.2 RAG knowledge base (`knowledge/` + `rag/`)
Curated German real-estate domain knowledge as a Markdown corpus (seeded from the domain research),
each doc citing its public source. Indexed locally: Ollama embeddings → in-memory NumPy cosine
similarity over a cached embedding matrix (the corpus is small; FAISS/Qdrant would be
over-engineering here — that comparison is `scouting-rag`'s job). Retrieval returns top-k chunks
with their source doc for citation. Naive vector retrieval only; honestly labelled as such.

### 3.3 Assistant (`assistant/`)
Orchestrates the Ollama chat model with **tool calling**:
- knowledge questions → RAG retrieval → answer grounded in retrieved chunks (with citations);
- calculation intents → the model calls a `finance/` function via a tool schema, receives the
  exact result, and explains it. The model never emits computed numbers of its own.
- Model configurable via `OLLAMA_MODEL` (default a tool-calling-capable local model, e.g.
  `qwen2.5:7b` or `llama3.1:8b`, both present locally).
- System prompt hard-codes the "numbers only from tools" rule; architecture enforces it (numbers
  are read from tool results, not parsed out of prose).

## 4. Interfaces

- **CLI** (`scripts/`): `ask "…"` (assistant chat) + direct calculator commands (`annuity`,
  `costs`, `afford`, `yield`) for deterministic, scriptable, testable use.
- **FastAPI**: `POST /api/ask` (chat), `POST /api/finance/{calc}` (direct calculators); SQLite for
  optional chat history. Serves the built React tab.
- **React chat tab** (closing step of the stage): slim chat in the dark "scout" identity; when an
  answer includes a calculation, render the structured numbers (amortization table) next to the
  LLM text.

## 5. Data flow

`question → assistant (LLM) → { RAG retrieval | tool call into finance/ } → structured result +
explanation → interface`. Numbers always pass through `finance/`; the LLM only routes and explains.

## 6. Error handling & honesty guardrails

- Ollama unreachable → clear message; the calculators (CLI/API) keep working (honest degradation,
  as in equity-scout).
- Invalid/malformed tool call → validate and re-ask, never guess numbers.
- Every surface carries the disclaimer: not tax/investment/financing advice; tax rates and interest
  levels age — source + date shown.
- No number is ever fabricated; if a config value is missing, the calculator errors loudly rather
  than assuming a default.

## 7. Testing

- `finance/` **fully unit-tested** — this is the trust anchor; TDD, no compromises. Cross-checked
  against hand-computed reference values.
- RAG: a small golden Q&A set (retrieval hits the expected source doc).
- Assistant: tool-routing tests against a **faked** LLM (no live Ollama in tests); asserts the right
  tool is called with the right args and that surfaced numbers equal the tool result.
- Gate: `uv run pytest -q` green + `uv run ruff check .` clean.

## 8. Stack & reuse

Python + uv, FastAPI + SQLite, Ollama, React (Vite). Reuse: the Ollama-assistant pattern from
`equity-scout`, the local-RAG pattern from `scouting-rag`, the dark scout dashboard identity.

## 9. Out of scope for Stage 1 (YAGNI)

Listing scraping · per-object exposé extraction · auto-scouting · scheduling/notifications · a RAG
technique comparison (that is `scouting-rag`). These are later stages, sketched in `PLAN.md`.
