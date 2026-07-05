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
