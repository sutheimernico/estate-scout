# Plan: Stage 2 Scoring Engine + Make It Shine

**Date:** 2026-07-20 · **Status:** awaiting go · **Executor:** any capable agent (written to be self-contained — no session context required)
**Relation to existing plan:** `2026-07-07-stage1-hardening-and-ux.md` (18 tasks, also awaiting go) covers backend robustness, two new calculators, chat polish, calc forms, and a basic listings tab. **This plan does not duplicate it.** It is independently executable: where it depends on pieces of the older plan (DELETE route, `Listings.tsx`), a gate task checks for their presence and builds a minimal version if missing. If both plans get a go, run the 2026-07-07 plan first.

## Context (verified 2026-07-20 by code review)

estate-scout is a local real-estate knowledge + finance assistant: deterministic finance calculators (`src/estatescout/finance/` — the trust anchor, hand-verified tests), RAG over 7 curated German knowledge docs (`src/estatescout/rag/`), an Ollama tool-calling assistant (`src/estatescout/assistant/`, qwen2.5:7b), Typer CLI + FastAPI (`src/estatescout/cli.py`, `api.py`), and a single-tab React chat frontend (`frontend/`). Stage 2 (scout funnel) is half-wired: `Listing` model + SQLite store + manual intake exist; `scout/enrich.py` (Bodenrichtwert + RegionSignal via provider protocols with static/user-maintained implementations) is implemented and tested but **not reachable from API or CLI**; `ListingStore.delete()` (`src/estatescout/scout/store.py:98`) has no route. **The scoring engine (Phase 8) and scout UI (Phase 9) do not exist at all** — the core pitch "transparent 0–100 scoring" is unimplemented.

Suite state: 97 passed (`uv run pytest`, 1.18s), `uv run ruff check .` clean. All tests use fakes (`FakeChat`, `FakeEmbedder`); the real Ollama paths (`assistant/chat.py:OllamaChat`, `rag/embedder.py:OllamaEmbedder`) were live-verified exactly once, manually.

Hard project principles (from PROJECT.md / ADR-0001 — do not violate):
- No scraping of listing portals. Listings are user-provided. No contact/personal data fields on `Listing` (guardrail is tested).
- The LLM never computes numbers — it routes to deterministic tools and explains results.
- Honest degradation: missing data is labeled `unavailable`, never fabricated. Every configured number carries `source` + `as_of` (see `config/rates.yaml` and `finance/config.py` fail-loud pattern).

## Goal

Turn "chatbot with calculators" into the product the name promises: a scout that **ranks user-provided listings with a transparent, explainable 0–100 score**, shows the breakdown visually, pulls at least one real external data source live, and can prove its LLM integration works with a repeatable live check.

Definition of done, in one sentence: a user adds a listing, gets an enriched, scored, visually broken-down assessment in the web UI, can ask the assistant about it, and every number in the score traces to a source.

## Execution rules

- Work on a new branch `feat/stage2-scoring` off the current working branch. Never commit to `main`. Small atomic commits, Conventional Commits, English.
- TDD: failing test first for every new behavior. Gate after every task: `uv run pytest && uv run ruff check .` green; frontend tasks additionally `npm test` (vitest) and `npm run build` in `frontend/`.
- Follow existing idioms: frozen dataclasses, provider `Protocol` seams with fakes for tests, config via YAML with `source`/`as_of` and fail-loud unknown keys, German UI texts, English code/comments.
- No new runtime dependencies without a note in the final outcome section. `httpx` is already present; prefer it.
- Do not read or print `.env`. No secrets in code.

---

## Phase A — Sharpen the foundation

### Task 1: Distinguish "provider missing" from "no data" in enrichment
**Files:** `src/estatescout/scout/enrich.py`, its tests.
Currently both cases collapse into `unavailable` (around `enrich.py:69-88`). The scoring engine's confidence computation needs the distinction.
- Introduce `class UnavailableReason(str, Enum): PROVIDER_MISSING = "provider_missing"; NO_DATA = "no_data"`.
- `Enrichment` records per-signal reason when a value is absent (e.g. `unavailable: dict[str, UnavailableReason]` replacing the current flat list — adapt to the actual current shape, keep it frozen).
- Update all call sites and tests; add tests for both reasons per provider.
**Accept:** enrichment result exposes, per signal, either a value or a typed reason; suite green.

### Task 2: Single assistant factory
**Files:** new `src/estatescout/assistant/factory.py`; edit `src/estatescout/api.py` (`get_assistant()`, ~line 78) and `src/estatescout/cli.py` (`ask`, ~line 119).
Both currently duplicate `OllamaEmbedder` + `RagIndex.build` + `Assistant` wiring.
- Extract `build_assistant(...)` carrying all shared parameters (model name, embedder, k, timeouts); API and CLI both call it.
**Accept:** duplication gone, both entry points behave identically, existing tests green (add one test that the factory wires RAG + tools).

### Task 3: Coverage reporting with a floor
**Files:** `pyproject.toml` (dev group), possibly `tests/`.
- Add `pytest-cov`. Measure current coverage of `src/estatescout`. Set `fail_under` to the measured integer value (do not inflate; do not chase 100%).
- Add the currently missing cheap tests: `GET /api/listings` with empty store; store-level delete behavior (route comes in Task 4).
**Accept:** `uv run pytest --cov` enforced via config, floor documented in the outcome section.

---

## Phase B — Wire the scout funnel end to end

### Task 4 (gate): DELETE listing route + assistant listing tool
**Files:** `src/estatescout/api.py`, `src/estatescout/cli.py`, `src/estatescout/assistant/tools.py`, tests.
The 2026-07-07 plan contains these; they may or may not exist by execution time. **Check first; skip whatever already exists.**
- `DELETE /api/listings/{id}` (404 on unknown id) + CLI `scout delete <id>` with confirmation flag.
- Assistant tool `list_listings` so the chat can see stored listings.
**Accept:** delete reachable from API and CLI with tests; assistant can enumerate listings via `FakeChat`-scripted test.

### Task 5: Enrichment route + persistence
**Files:** `src/estatescout/scout/store.py` (schema migration), `api.py`, `cli.py`, tests.
- Persist enrichment on the listing row (JSON column `enrichment` + `enriched_at`; write a small in-place SQLite migration guarded by `PRAGMA user_version`, mirroring however the store currently handles schema setup).
- `POST /api/listings/{id}/enrich` runs configured providers, stores and returns the result (including typed unavailable-reasons from Task 1). CLI `scout enrich <id>`.
**Accept:** enrich → stored → visible on subsequent `GET /api/listings`; re-running updates `enriched_at`; tests cover happy path, unknown id, provider-missing.

---

## Phase C — The scoring engine (the missing heart)

### Task 6: Deterministic scoring engine
**Files:** new `src/estatescout/scout/scoring.py`, new `config/scoring.yaml`, tests with hand-computed reference values (same convention as `finance/` tests).
Design decisions (fixed — do not re-open):
- **Sub-scores (0–100 each):**
  - `yield_score` from gross rental yield via existing `finance/yield_metrics.py`: 0% → 0, ≥6% → 100, linear in between. Requires listing price + cold rent; if rent absent → sub-score unavailable.
  - `price_score` from €/m² vs. Bodenrichtwert reference (enrichment): ratio ≤0.8 → 100, ≥1.5 → 0, linear in between. If Bodenrichtwert unavailable → sub-score unavailable. (Bodenrichtwert is land value, not a purchase-price comparable — name the constant `PRICE_VS_LAND_VALUE` and explain the heuristic in a docstring; it is a transparency-first proxy, which is the honest framing.)
  - `region_score` from `RegionSignal` (vacancy etc.): map the signal's numeric field(s) linearly onto 0–100 using bounds defined in `scoring.yaml`; take the exact available fields from the current `RegionSignal` dataclass in `scout/enrich.py`.
- **Total:** weighted mean of *available* sub-scores, weights renormalized over available ones. Defaults in `scoring.yaml`: yield 0.4, price 0.4, region 0.2 (each entry with `source: "own heuristic"` and `as_of`).
- **Confidence:** `available_inputs / expected_inputs` as a 0–1 float, plus the typed reasons from Task 1 passed through. `provider_missing` and `no_data` both reduce confidence but are reported distinctly.
- **Output:** frozen `ScoreReport` dataclass: `total: int | None` (None if zero sub-scores available — never fabricate), `subscores`, `weights_used`, `confidence`, `reasons`, `as_of`.
- All thresholds/weights come from `scoring.yaml` via the fail-loud config loader pattern in `finance/config.py`.
**Accept:** hand-computed reference tests for full data, partial data (renormalization), and no data (total=None); property: total always within min/max of available sub-scores.

### Task 7: Score exposed everywhere
**Files:** `api.py`, `cli.py`, `assistant/tools.py`, tests.
- `GET /api/listings/{id}/score` (computes from stored enrichment; 409 with hint if never enriched) and score summary embedded in `GET /api/listings` items.
- CLI `scout score <id>` printing the breakdown as a table.
- Assistant tool `score_listing` returning the `ScoreReport` for the LLM to *explain* (never recompute).
**Accept:** API/CLI/assistant all read the same engine; scripted assistant test shows the model explaining a score it did not compute.

---

## Phase D — Scout UI (make it visible)

### Task 8 (gate): Listings tab exists
**Files:** `frontend/src/`.
The 2026-07-07 plan builds `Listings.tsx` (table + intake + delete) and tab navigation. **Check first.** If absent, build a minimal version: tab nav (Chat / Objekte), listings table from `GET /api/listings`, add-listing form, delete button. German UI labels.
**Accept:** listings CRUD usable in the browser; vitest cases for table render + empty state.

### Task 9: Score drilldown panel
**Files:** `frontend/src/` (extend listings tab).
- Score column (badge with total + confidence indicator) in the table; row click opens a drilldown: horizontal bars per sub-score, weights shown, confidence badge, and an honest "nicht verfügbar"-list showing each missing signal with its reason (provider fehlt vs. keine Daten).
- "Enrich + Score" button per row calling Task 5/7 endpoints, with loading and error states (API 503 path included).
- React note (per your growth area): keep server state in one place — a small `useListings()` hook owning fetch/refresh, components stay presentational.
**Accept:** full flow in browser: add listing → enrich → score → drilldown renders breakdown; vitest covers drilldown rendering with partial data and the 503 error path (this also closes the untested frontend error path found in review).

### Task 10: Tool-call transparency panel in chat
**Files:** `api.py` (`/api/ask` response), `frontend/src/` chat components, tests.
The data already flows through the assistant's dispatch loop — surface it.
- Extend the ask response with `tool_trace: [{tool, args, result}]` (backend change + test with scripted `FakeChat`).
- In the chat UI, render an expandable "Werkzeuge (n)" section under each assistant message listing each call with args and result, collapsed by default.
**Accept:** a finance question in the chat visibly shows which tool ran with which inputs — the "honest harness" claim becomes demonstrable in the UI.

---

## Phase E — Real data + living proof

### Task 11: Live mortgage-rate provider (Bundesbank) with honest fallback
**Files:** new `src/estatescout/finance/rates_live.py`, `config/rates.yaml`, tests (httpx mocked; no live call in suite).
- Implement a provider fetching the current German housing-loan interest rate from the Bundesbank SDMX REST API (`api.statistiken.bundesbank.de`, no auth). Locate the exact series id for "Effektivzinssätze Banken DE / Wohnungsbaukredite an private Haushalte, Neugeschäft" in the MFI interest-rate statistics (browse the SDMX dataflow if needed); record the chosen id + URL as constants with a comment.
- TTL cache (24h, on-disk JSON in the existing data dir), tagged `source: "Bundesbank SDMX <series-id>"` + `as_of` from the series. On any failure: fall back to `rates.yaml` values **and mark the origin** (`source` clearly shows static fallback) — never silently stale.
- Wire as the default rate source for calculators that consume a market rate, keeping an explicit override parameter.
**Accept:** mocked tests for fetch/cache/fallback; one manual live check documented in the outcome section; every rate in any API response carries its source tag.

### Task 12: Bodenrichtwert — one real source, decision tree fixed
**Files:** new provider in `src/estatescout/scout/`, config, tests, `docs/` note.
Do not re-open the "which source" question; follow this tree top-down and stop at the first branch that works:
1. **BORIS-NI (Niedersachsen) WFS/OGC-API**: if machine-readable access without registration works (GetFeature on coordinates/Gemeinde returning Bodenrichtwert), implement `WfsBodenrichtwert` (httpx, mocked tests + one recorded real response as fixture).
2. **Any other Bundesland with open WFS/OGC Bodenrichtwert access** (check BORIS-D portal links): same implementation, document which one.
3. **Fallback — CSV import provider**: `CsvBodenrichtwert` reading a documented CSV format (`gemeinde,plz,brw_eur_m2,as_of,source_url`), plus a short `docs/bodenrichtwert-import.md` describing where a user downloads official data manually. This branch is still a win: it replaces the hardcoded dict with a real, user-extendable data path.
- Whichever branch: provider plugs into the existing `BodenrichtwertProvider` protocol; `unavailable` reasons keep working; scraping HTML is **not** an option on any branch (ADR-0001).
**Accept:** provider selected by config; tests green without network; `docs/` note states which branch was taken and why.

### Task 13: Repeatable live verification
**Files:** new `scripts/verify_live.sh`, optional pytest marker `live`, README section.
- Script runs a fixed set of golden queries end-to-end against real Ollama (embedder + chat + one finance tool call + one RAG answer + enrich/score of a fixture listing), prints PASS/FAIL per check, exits non-zero on failure, and **skips cleanly with a clear message when Ollama is down** (that is honest degradation, not failure).
- Mark any pytest-based live tests `@pytest.mark.live`, excluded by default (`addopts`-level), so `uv run pytest` stays hermetic.
**Accept:** running the script with Ollama up exercises `OllamaChat` and `OllamaEmbedder` for real — closing the "green suite, never-verified integration" gap; README documents the command.

### Task 14 (stretch — only if A–E done and green): Nightly re-score digest
**Files:** new `scripts/nightly_rescore.py`, `deploy/` systemd user units, docs.
- Script: re-enrich + re-score all stored listings, compare to previous stored scores, append a German Markdown digest (`docs/digests/YYYY-MM-DD.md`) listing score deltas with the changed inputs ("Score 62→70: Zins gefallen 3.9%→3.6%").
- Provide systemd user service+timer files and an install one-liner in docs. Do **not** enable the timer — installation is Nico's call.
**Accept:** running the script twice with a rate change between runs produces a delta digest; unit tests on the delta logic.

---

## Verification before completion

1. Full gates: `uv run pytest` (all green, coverage floor holds), `uv run ruff check .`, `cd frontend && npm test && npm run build`.
2. Manual browser pass: add → enrich → score → drilldown; chat shows tool trace; error states render on stopped backend.
3. `scripts/verify_live.sh` run once with Ollama up; output pasted into the outcome section.
4. Append an **Outcome** section to this file: what was built, deviations + why, new dependencies, coverage floor, which Bodenrichtwert branch was taken, open items.
5. Update `README.md` and `PLAN.md` phase status (Phases 8–9 done).

## Needs Nico (not executable by the agent)
- Go for this plan (and decision whether 2026-07-07 hardening runs first — recommended).
- Publish step: GitHub remote + public + portfolio link (highest-leverage zero-code item from the review; follow `~/.claude/CLAUDE.md` publish checklist — requires Nico's confirmations).
- Optional: enable the nightly timer (Task 14); pick the Bundesland he actually cares about for Task 12 if not Niedersachsen.
