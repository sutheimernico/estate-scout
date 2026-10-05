# estate-scout — LOOP (per-iteration prompt for the autonomous build agent)

You are a fresh agent. You do ONE high-value thing, verify it, commit it, and exit. Progress lives
on disk (this file, `PROJECT.md`/`PLAN.md`, git history, `AUTOPILOT_LOG.md`) — never in context.

## Per-iteration protocol

1. Read the global loop rules, then this `LOOP.md`, then `PLAN.md` + `PROJECT.md`.
2. Confirm you are on branch `autopilot/work` (if not, stop).
3. Pick the SINGLE highest-value open `- [ ]` task (top-to-bottom, earlier phases first). If a phase
   boundary is reached, run the once-per-phase self-challenge/SOTA step first (write an ADR under
   `docs/adr/` if it changes the plan).
4. Do that one task. Small, reviewable diff. Read existing code before writing; match conventions.
   New logic ships with a test. Ollama/network access stays behind a seam and is faked in tests.
5. Run the gate: `uv run pytest -q` (green) AND `uv run ruff check .` (clean). If red, fix or revert.
6. On green: commit (Conventional Commits, English, imperative), check off the task in `PLAN.md`,
   append a one-line note to `AUTOPILOT_LOG.md`. Then exit.
7. If a task needs a paid resource or a owner-only input: move it to "Needs Owner", pick another, or
   exit. Never sign up for anything paid. Never fabricate facts, numbers, or metrics.

## Project-specific hard constraints (never override)

- **Numbers only from `finance/`.** The LLM never computes numbers — it calls a tested calculator
  and explains the result. Any surfaced number must originate from a tool result.
- **Local & free.** Ollama for the LLM/embeddings; free public data sources only. No paid APIs.
- **No fabricated facts.** Grunderwerbsteuer rates, interest levels, market figures carry source +
  date. A missing config value errors loudly rather than defaulting.
- **Not advice.** Every output surface carries the disclaimer (no tax/investment/financing advice).
- **No scraping.** Listing portals (ImmoScout24/Immowelt/Kleinanzeigen) are off-limits — their AGB
  forbid it. Stage 2 uses only legal sources (see ADR-0001, once written).
- **Determinism in tests.** No live Ollama/network in tests; use the `Fake*` seams.
- **Pin new deps** with a one-line justification; simplest solution that meets the task (YAGNI).

## Gate (objective done-check)

`uv run pytest -q` green + `uv run ruff check .` clean. Commit only a green gate.

## Where things are

- Spec: `docs/superpowers/specs/2026-07-05-estate-scout-stage1-design.md`
- Code: `src/estatescout/{finance,rag,assistant}/` (one responsibility per file) · Tests: `tests/`
- CLIs: `scripts/` · Corpus: `knowledge/` · Config: `config/` · RAG cache: `data/rag_index/`
  (gitignored)
- Run locally: `uv run python scripts/<name>.py` · Ollama model via `OLLAMA_MODEL` env.
