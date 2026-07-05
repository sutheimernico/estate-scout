# estate-scout — Autopilot log (one line per iteration)

- 2026-07-05 — Phase 0: scaffold (uv/ruff/pytest, LICENSE, docs, spec, PLAN/LOOP/PROJECT), repo on
  `autopilot/work`, register entry added. Gate green (1 smoke test), ruff clean.
- 2026-07-05 — Phase 1: `annuity` (Annuitätendarlehen) — `amortize` + `annuity` summary, 8 tests
  (exact first-two-months split, r=0 edge, non-amortizing + invalid-input guards). Gate green.
- 2026-07-05 — Phase 1: `annuity` optional `annual_sondertilgung` (contract option, ≠ § 489 BGB).
  4 tests (zero==base, shortens term/cuts interest, exact principal). Gate green (11 tests).
- 2026-07-05 — Phase 1: `config/rates.yaml` (16 GrESt rates + aliases, notary/GB, Makler,
  affordability, ref. Sollzins — all source+date) + `finance/config.py` loader. 5 tests, gate green.
- 2026-07-05 — Phase 1: `purchase_costs` (GrESt per Bundesland + notary/GB + optional Makler,
  min_equity). 4 tests (NI vs NRW, breakdown, Makler off, invalid). Gate green (20 tests).
- 2026-07-05 — Phase 1: `affordability` (max price from net-income budget, backs out ancillary
  quota per Bundesland). 5 tests. Gate green (25 tests).
- 2026-07-05 — Phase 1 COMPLETE: `yield_metrics` (gross/net yield + Kaufpreisfaktor), 4 tests.
  Finance core done: 5 calculators + config, 29 tests, ruff clean. Trust anchor complete.
- 2026-07-05 — Phase 2: curated knowledge corpus (7 docs under knowledge/, sources+dates inline)
  from the domain research. No code change, gate green (29 tests).
- 2026-07-05 — Phase 2: `rag/chunker.py` (heading-aware) + `rag/embedder.py` (Embedder Protocol,
  FakeEmbedder deterministic, OllamaEmbedder httpx-injectable). 8 tests. Gate green (37 tests).
- 2026-07-05 — Phase 2 COMPLETE: `rag/index.py` (load_corpus + RagIndex build/retrieve/save/load,
  cosine). 6 tests incl. 2 golden queries + cache round-trip. Gate green (43 tests). RAG done.
- 2026-07-05 — Phase 3: `assistant/tools.py` (4 tool schemas + dispatcher, percent→fraction
  adapters, arg validation, numbers from finance/). 8 tests. Gate green (51 tests).
- 2026-07-05 — Phase 3: `assistant/chat.py` (ChatModel Protocol, OllamaChat, FakeChat) +
  `assistant/assistant.py` (tool-calling loop, RAG context, error feedback). 7 tests. Gate green (58).
- 2026-07-05 — Phase 3 COMPLETE: SYSTEM_PROMPT (honesty rules) + DISCLAIMER on every response.
  3 honesty tests. Assistant done. Gate green (61 tests).
- 2026-07-05 — Phase 4: CLI (`estatescout/cli.py` finance_app + ask + render_response,
  scripts/ shims). 6 tests + live smoke run of finance CLI. Gate green (67 tests).
- 2026-07-05 — Phase 4: FastAPI (`estatescout/api.py`: /api/finance/{calc} + /api/ask via
  injectable assistant dep, disclaimer, 503 on Ollama-down). 9 tests. Gate green (78 tests).
