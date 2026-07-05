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

1. **Knowledge & Finance Assistant** ← THIS STAGE. RAG over curated domain knowledge + deterministic
   finance calculators + local tool-calling assistant, CLI/API/React chat.
2. **Scouting funnel** — ingest legally-available listings/market data → score price-vs-location →
   recommend. GATED on the data-source finding (see the research brief + ADR-0001); no scraping.
3. **Per-object evaluation** — paste an exposé → extract fields (user confirms) → run calculators →
   verdict. The bridge between Stage 1 and the funnel.
4. **Copilot** — scheduled runs + notifications (equity-scout pattern), inherits the funnel's data.
5. **Unified dashboard** — one React app across all pillars, dark scout identity.

Stages 2–5 are sketched in `docs/adr/` as they are designed; do not expand them here until Stage 1
is done and the data-source question is settled.

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
- [ ] `affordability`: max purchase price from net income, equity, interest, initial repayment,
      payment-to-income cap. Tests: monotonicity (more income → higher max), rate cap respected.
- [ ] `yield_metrics`: gross yield = annual rent / price; net yield after ancillary + running costs;
      Kaufpreisfaktor = price / annual rent. Tests: reciprocal relation, worked example.
- [x] `config/` loader: versioned YAML (Grunderwerbsteuer per Bundesland, notary/Makler %,
      rule-of-thumb thresholds), each value tagged source+date. Populated from the domain research;
      loudly errors on unknown keys. DONE 2026-07-05: `config/rates.yaml` (all 16 GrESt rates +
      full-name/NRW aliases, notary/GB, Makler, affordability, reference Sollzins — each source+date)
      + `finance/config.py` (`load_config`, `grunderwerbsteuer_rate` by code/name). 5 tests.
Acceptance: every calculator unit-tested against hand-computed references; gate green.

## Phase 2 — RAG knowledge base (`knowledge/` + `rag/`)

Goal: curated corpus + local naive-vector retrieval with citations.

- [ ] Write the curated Markdown corpus from the domain research (valuation, location signals +
      data sources, financing math, risks, legal), each doc citing its public source + date.
- [ ] Embedder seam: `Embedder` Protocol; `OllamaEmbedder` (httpx `/api/embeddings`) + `FakeEmbedder`
      for network-free tests. Chunker (heading-aware, bounded chunk size).
- [ ] Index: embed the corpus once → cached NumPy matrix under `data/rag_index/` (gitignored,
      regenerable); `retrieve(query, k)` → top-k chunks + source. Tests: fake embedder, golden Q&A
      hits expected source doc, cache round-trip.
Acceptance: golden Q&A retrieval passes with the fake embedder; gate green.

## Phase 3 — Assistant (`assistant/`) — Ollama tool calling

Goal: route questions to RAG or a finance tool; numbers only from tools.

- [ ] Tool schemas for the `finance/` functions (JSON schema per calculator) + a dispatcher mapping
      tool name → function, with argument validation.
- [ ] LLM seam: `ChatModel` Protocol; `OllamaChat` (httpx `/api/chat` with `tools`) + `FakeChat`
      scripted for tests. Assistant loop: user msg → model (may request tool) → run tool → feed
      result back → final grounded answer. RAG retrieval injected as context for knowledge questions.
- [ ] System prompt encoding the honesty rules (numbers only from tools, cite sources, disclaimer).
      Tests (fake model): calc intent → correct tool + args, surfaced number == tool result;
      knowledge intent → RAG context used; Ollama-down → clear degradation.
Acceptance: tool-routing tests green against the fake model; gate green.

## Phase 4 — Interfaces (CLI + FastAPI)

- [ ] CLI (`scripts/`, typer): `ask "…"` + direct `annuity`/`costs`/`afford`/`yield` commands
      (structured output). Tests: direct commands deterministic; `ask` wired to the assistant.
- [ ] FastAPI: `POST /api/ask`, `POST /api/finance/{calc}` (Pydantic models), disclaimer in
      responses, SQLite chat history (optional). Tests: TestClient over each endpoint, validation
      errors, Ollama-down path.
Acceptance: CLI + API exercised in tests; a real local `ask` run verified against Ollama; gate green.

## Phase 5 — React chat tab (dark scout identity)

- [ ] Vite + React chat UI: message stream, calc answers render the amortization table beside the
      text, disclaimer footer. Built assets served by FastAPI.
- [ ] `npm run build` health + a thin component/render check. Portfolio coupling: add estate-scout
      to `~/private/portfolio` once presentable.
Acceptance: `npm run build` passes; API serves the built tab; a manual chat round-trip works.

---

## Needs Nico

- Merge `autopilot/work` → `main` (Nico reviews; `main` stays unborn until then).
- Remote / GitHub visibility for estate-scout (none yet) — decide when Stage 1 is presentable.
- Stage 2 (funnel) data-source go/no-go once the research + ADR-0001 land: which legal source, if
  any, is worth building a funnel on.
