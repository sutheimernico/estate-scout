# estate-scout — Plan (AUTOPILOT-driven build backlog)

**Source of truth for design:** `docs/superpowers/specs/2026-07-05-estate-scout-stage1-design.md`
Personal rules (`~/.claude/CLAUDE.md`) + global loop rules (`~/private/AUTOPILOT.md`) apply.

This file is the binding backlog for the autonomous loop. Each iteration picks the SINGLE
highest-value open `- [ ]` task, does it on `autopilot/work`, runs the gate, commits only if green,
checks the box, and appends one line to `AUTOPILOT_LOG.md`.

## Iron principles (never overridden)

- **Local & free only.** Ollama + free public data sources. No paid APIs, no cloud. A task needing a
  paid resource or a Nico-only input goes to "Needs Nico", never faked.
- **Numbers only from `finance/`.** The LLM never computes numbers; it calls tested calculators and
  explains the results. This is the whole point — never let the model do arithmetic.
- **Gate is objective:** `uv run pytest -q` green AND `uv run ruff check .` clean. Never commit red.
- **One change per iteration.** No bundling. No speculative abstractions (YAGNI).
- **No fabricated facts.** Tax rates / interest levels / market figures carry source + date; a
  missing config value errors loudly rather than defaulting.
- **New logic ships with a test.** No live Ollama/network in tests — use the fake LLM/embedder seam.
- **Not advice.** Every output surface carries the disclaimer.

## The vision (stages — only Stage 1 is detailed)

1. **Knowledge & Finance Assistant** — ✅ COMPLETE 2026-07-06. RAG over curated domain knowledge +
   deterministic finance calculators + local tool-calling assistant, CLI/API/React chat.
2. **Scouting funnel** (per ADR-0001, NO scraping) — user-assisted intake of objects + public-data
   enrichment (Bodenrichtwert/Zensus/trend) → transparent price-vs-location + finance scoring. ←
   CURRENT (Phases 6–9 below).
3. **Per-object evaluation** — folded into Stage 2 (the intake + score IS the per-object verdict).
4. **Copilot** — scheduled runs + notifications (equity-scout pattern), over the user's saved objects.
5. **Unified dashboard** — one React app across all pillars, dark scout identity.

Data-source decision is settled in `docs/adr/0001-stage2-data-source.md`. The auto-scan-every-listing
ambition is a Needs-Nico gap (no legal auto-source); the loop builds the honest funnel around it.

---

## Phase 0 — Scaffold

- [x] Repo skeleton: uv project (`pyproject.toml`), ruff + pytest gate, `.gitignore`, MIT `LICENSE`,
      `README`, `PROJECT.md`, `PLAN.md`, `LOOP.md`, `AUTOPILOT_LOG.md`, spec under
      `docs/superpowers/specs/`, package layout `src/estatescout/{finance,rag,assistant}`. Repo on
      `autopilot/work`, `main` unborn until Nico merges. Register entry in `~/private/AUTOPILOT.md`.
      DONE 2026-07-05: uv sync + smoke test green, ruff clean, register entry added.
Acceptance: `uv run pytest -q` green (even with a trivial smoke test) + `uv run ruff check .` clean. — MET.

## Phase 1 — Finance core (`finance/`) — TDD, the trust anchor

Goal: pure, typed, fully unit-tested calculators. No LLM. Cross-check against hand-computed values.

- [x] `annuity`: monthly payment = P·(rate + initial_repayment)/12 (German convention), amortization
      schedule (per-year remaining debt, interest/principal split), total interest, payoff duration
      from an initial-repayment %. DONE 2026-07-05: `finance/annuity.py` (`amortize` + `annuity`), 8
      tests incl. exact first-two-months split, r=0 pure-repayment, non-amortizing + invalid inputs.
- [x] `annuity` extension: optional annual `sondertilgung` (extra repayment) shortens the schedule.
      DONE 2026-07-05: `annual_sondertilgung` (EUR/year, applied after each full year, capped at
      remaining), separate `sondertilgung` field on Month/YearRow. 4 tests (zero==base, shortens
      term + cuts interest, exact principal repaid incl. sonder). Note: distinct from § 489 BGB.
- [x] `purchase_costs`: Grunderwerbsteuer (rate per Bundesland from `config/`) + notary+Grundbuch %
      + Makler % → total costs, ancillary-cost quota, equity-needed. DONE 2026-07-05:
      `finance/purchase_costs.py` (optional Makler share for Bestellerprinzip, `min_equity` =
      ancillary). 4 tests (NI vs NRW, full breakdown, Makler excluded, invalid inputs).
- [x] `affordability`: max purchase price from net income, equity, interest, initial repayment,
      payment-to-income cap. DONE 2026-07-05: `finance/affordability.py` (budget→loan→price, backs
      out the ancillary quota per Bundesland; obligations + running costs subtracted). 5 tests
      (income cap, worked example max_loan=300k, monotonicity, obligations reduce, invalid inputs).
- [x] `yield_metrics`: gross yield = annual rent / price; net yield after ancillary + running costs;
      Kaufpreisfaktor = price / annual rent. DONE 2026-07-05: `finance/yield_metrics.py`. 4 tests
      (gross+KPF worked example, reciprocal relation, net accounts for costs, invalid inputs).
- [x] `config/` loader: versioned YAML (Grunderwerbsteuer per Bundesland, notary/Makler %,
      rule-of-thumb thresholds), each value tagged source+date. Populated from the domain research;
      loudly errors on unknown keys. DONE 2026-07-05: `config/rates.yaml` (all 16 GrESt rates +
      full-name/NRW aliases, notary/GB, Makler, affordability, reference Sollzins — each source+date)
      + `finance/config.py` (`load_config`, `grunderwerbsteuer_rate` by code/name). 5 tests.
Acceptance: every calculator unit-tested against hand-computed references; gate green. — MET
2026-07-05: 5 calculators (annuity+sondertilgung, purchase_costs, affordability, yield_metrics) +
config loader, 29 tests, ruff clean. The trust anchor is complete.

## Phase 2 — RAG knowledge base (`knowledge/` + `rag/`)

Goal: curated corpus + local naive-vector retrieval with citations.

- [x] Write the curated Markdown corpus from the domain research (valuation, location signals +
      data sources, financing math, risks, legal), each doc citing its public source + date.
      SEED: `docs/research/2026-07-05-domain-research.md`. DONE 2026-07-05: 7 focused docs under
      `knowledge/` (00 Überblick, 01 Bewertung, 02 Lage+Datenquellen, 03 Finanzierung, 04
      Kaufnebenkosten, 05 Risiken+Recht, 06 Datenzugriff-Listings), sources + dates inline.
- [x] Embedder seam: `Embedder` Protocol; `OllamaEmbedder` (httpx `/api/embeddings`) + `FakeEmbedder`
      for network-free tests. Chunker (heading-aware, bounded chunk size). DONE 2026-07-05:
      `rag/chunker.py` (heading-aware, paragraph split at max_chars) + `rag/embedder.py`
      (`Embedder` Protocol, deterministic hashing `FakeEmbedder`, `OllamaEmbedder` w/ injectable
      httpx client). 8 tests (chunk headings/split, fake determinism/overlap, Ollama MockTransport).
- [x] Index: embed the corpus once → cached NumPy matrix under `data/rag_index/` (gitignored,
      regenerable); `retrieve(query, k)` → top-k chunks + source. DONE 2026-07-05: `rag/index.py`
      (`load_corpus`, `RagIndex.build/retrieve/save/load`, row-normalized cosine). 6 tests
      (corpus load, 2 golden queries hit expected source, cache round-trip, empty/k guards).
Acceptance: golden Q&A retrieval passes with the fake embedder; gate green. — MET 2026-07-05
(43 tests, ruff clean). Note: real semantic retrieval needs `ollama pull nomic-embed-text`.

## Phase 3 — Assistant (`assistant/`) — Ollama tool calling

Goal: route questions to RAG or a finance tool; numbers only from tools.

- [x] Tool schemas for the `finance/` functions (JSON schema per calculator) + a dispatcher mapping
      tool name → function, with argument validation. DONE 2026-07-05: `assistant/tools.py` (4
      OpenAI-style tool specs; adapters take percent, convert to fractions; `dispatch` validates
      required args; results rounded, numbers straight from finance/). 8 tests.
- [x] LLM seam: `ChatModel` Protocol; `OllamaChat` (httpx `/api/chat` with `tools`) + `FakeChat`
      scripted for tests. Assistant loop: user msg → model (may request tool) → run tool → feed
      result back → final grounded answer. RAG retrieval injected as context for knowledge questions.
      DONE 2026-07-05: `assistant/chat.py` (Protocol, OllamaChat w/ OllamaUnavailable, FakeChat) +
      `assistant/assistant.py` (loop, RAG context injection, tool-error fed back). 7 tests
      (script order, MockTransport post, ConnectError→Unavailable, calc round-trip, RAG context,
      error feedback, degradation propagates).
- [x] System prompt encoding the honesty rules (numbers only from tools, cite sources, disclaimer).
      Tests (fake model): calc intent → correct tool + args, surfaced number == tool result;
      knowledge intent → RAG context used; Ollama-down → clear degradation. DONE 2026-07-05:
      `SYSTEM_PROMPT` (4 rules) + `DISCLAIMER` wired onto every `AssistantResponse`. 3 tests.
Acceptance: tool-routing tests green against the fake model; gate green. — MET 2026-07-05
(61 tests, ruff clean). Real Ollama run deferred to Phase 4 (needs a tool-calling model pulled).

## Phase 4 — Interfaces (CLI + FastAPI)

- [x] CLI (`scripts/`, typer): `ask "…"` + direct `annuity`/`costs`/`afford`/`yield` commands
      (structured output). DONE 2026-07-05: `estatescout/cli.py` (finance_app reuses tool dispatch;
      `ask` wires OllamaChat+RAG, degrades on OllamaUnavailable; `render_response`). Thin
      `scripts/finance.py` + `scripts/ask.py`. 6 tests (4 calc commands via CliRunner, unknown-BL
      error, render_response). Verified live: `scripts/finance.py annuity` prints correct schedule.
- [x] FastAPI: `POST /api/ask`, `POST /api/finance/{calc}` (Pydantic models), disclaimer in
      responses, SQLite chat history (optional). DONE 2026-07-05: `estatescout/api.py` (finance +
      ask via injectable `get_assistant` dependency, disclaimer on every response, `/api/health`).
      SQLite chat history DEFERRED (YAGNI — no second use case yet). 9 tests (health, finance calcs,
      unknown/missing→400, ask via injected fake, Ollama-down→503, all calcs routable).
Acceptance: CLI + API exercised in tests; a real local `ask` run verified against Ollama; gate green.
— MET 2026-07-05: live qwen2.5:7b run called the `annuity` tool with correct args and surfaced
`monthly_payment = 1400.0 €` straight from `finance/` (number from code, not the model); grounded
answer correct. 78 tests, ruff clean.

## Phase 5 — React chat tab (dark scout identity)

- [x] Vite + React chat UI: message stream, calc answers render the amortization table beside the
      text, disclaimer footer. Built assets served by FastAPI. DONE 2026-07-06: `frontend/` (Vite +
      React + TS, dark amber "scout" theme, App chat + AmortizationTable + api client). `npm run
      build` green (tsc + vite). FastAPI mounts `frontend/dist` at `/` (existence-gated, /api takes
      precedence) — verified serving index.html + /api/health.
- [x] `npm run build` health + a thin component/render check. Portfolio coupling: add estate-scout
      to `~/private/portfolio` once presentable. DONE 2026-07-06: 3 vitest render tests (App header/
      disclaimer/empty-state, AmortizationTable formatting) green; `npm run build` green. Portfolio
      coupling DEFERRED to Needs Nico — premature before merge/remote/screenshots.
Acceptance: `npm run build` passes; API serves the built tab; a manual chat round-trip works. — MET
2026-07-06: build green, FastAPI verified serving index.html at `/` with `/api/*` taking precedence;
the live tool-calling round-trip was verified in Phase 4 (qwen2.5:7b → annuity → 1400 €).

---

# Stage 2 — Honest scouting funnel (per ADR-0001; NO scraping)

Goal: over objects the user brings in (manual/assisted intake — never scraped), enrich with public
data and score price-vs-location transparently, reusing the Stage-1 `finance/` core. Numbers stay
honest: a missing market figure lowers confidence, it is never invented.

## Phase 6 — Object model + manual intake

- [ ] `Listing` model (price, living_area_sqm, rooms, year_built, plz, ort, bundesland, object_type,
      features, source_url; **NO seller contact data** per ADR-0001/DSGVO) + validation (positive
      price/area, known Bundesland). TDD.
- [ ] SQLite listings store (objects only): add/list/get/delete, behind a small repository seam.
      TDD with a temp DB.
- [ ] Manual intake: CLI `add-listing` + API `POST /api/listings` / `GET /api/listings`. Tests
      (TestClient + CliRunner).

## Phase 7 — Public-data enrichment (provider seams + fakes)

- [ ] Bodenrichtwert seam: `BodenrichtwertProvider` Protocol + `FakeBodenrichtwert`; real adapter is
      best-effort (BORIS has no documented REST API → degrade to "unavailable", never guess). Attach
      the local Bodenrichtwert to a listing. Tests use the fake.
- [ ] Regional signal seam: population trend + vacancy (Zensus/GENESIS + Destatis) Protocol + fakes;
      attach to a listing's location, degrade honestly. Tests use the fake.

## Phase 8 — Transparent scoring engine

- [ ] Score a listing 0–100 from sub-scores with a visible per-factor contribution: price-vs-
      Bodenrichtwert / local €-per-m², Kaufpreisfaktor + yield (reuse `finance/`), location signals.
      Pure, TDD; missing inputs reduce a confidence field rather than being fabricated.
- [ ] Rank saved listings; CLI + `GET /api/listings/scored`. Tests.

## Phase 9 — Scout surface

- [ ] React "Scout" tab: table of scored objects + per-object drilldown (score breakdown + finance
      metrics) in the dark scout identity; `npm run build` + a render check.
Acceptance: a user can add objects, they get enriched (or an honest "unavailable") + transparently
scored, surfaced in CLI/API/UI; gates green (pytest + ruff + npm build).

---

## Needs Nico

- Merge `autopilot/work` → `main` (Nico reviews; `main` stays unborn until then).
- Remote / GitHub visibility for estate-scout (none yet) — decide when Stage 1 is presentable.
- Portfolio coupling: add estate-scout to `~/private/portfolio` once merged/public with a
  screenshot or short demo (deferred from Phase 5 — premature before then).
- Optional: `ollama pull nomic-embed-text` for real semantic RAG retrieval (the assistant works
  with any pulled model for embeddings, but a dedicated embed model is better).
- Stage 2 (funnel) data-source go/no-go once ADR-0001 lands: which legal source, if any, is worth
  building a funnel on (no scraping — see `knowledge/06-datenzugriff-listings.md`).
