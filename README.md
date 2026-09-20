# estate-scout

A local, free real-estate **knowledge assistant + finance calculators** for the German market
(Niedersachsen / NRW). Ask it anything about buying residential property and financing it; the
numbers come from tested code, not from the language model.

**Honest harness — not tax, investment, or financing advice.** No listing scraping. Runs entirely
on your machine via [Ollama](https://ollama.com); no paid APIs.

## Why the numbers are trustworthy

A local 7B model cannot be trusted with arithmetic. So it doesn't do any: every number
(Annuitätendarlehen rate, Kaufnebenkosten, Leistbarkeit, Mietrendite, Bewirtschaftungskosten,
Eigenkapitalrendite) is computed by tested Python in `finance/`. The assistant understands your
question, calls the right calculator, and explains the result. Tax rates and thresholds live in
versioned config, each tagged with source + date.

## The score

Saved objects get a transparent **0–100 assessment** built from three visible blocks:

| Block          | What it measures                                            | Weight |
| -------------- | ----------------------------------------------------------- | ------ |
| Rendite        | gross rental yield (0 % → 0, ≥ 6 % → 100)                     | 0.4    |
| Preisniveau    | €/m² living space ÷ local Bodenrichtwert (≤ 0.8 → 100, ≥ 1.5 → 0) | 0.4    |
| Lage           | population trend and vacancy rate                             | 0.2    |

Weights and thresholds live in `config/scoring.yaml` with `source` + `as_of` — they are own
heuristics, in config precisely so they can be argued with. The total is the weighted mean of the
blocks that could actually be computed, with the weights renormalized over those; **if no block is
computable the total is `null`, never a fabricated 0.** A confidence figure reports how many of the
four raw signals were available, and every gap names its reason (`provider_missing` = no data
source configured, `no_data` = the source knows nothing about this object, `rent_missing` = you did
not supply a Kaltmiete).

The Bodenrichtwert is the **median residential land value of the Gemeinde** from the public BORIS
Niedersachsen WFS (keyless, Datenlizenz Deutschland Namensnennung 2.0, © GDI-NI) — a transparent
proxy for "expensive for the area", not a valuation. See `docs/bodenrichtwert-quelle.md`.

```bash
uv run python scripts/scout.py enrich 1          # pull the public reference data
uv run python scripts/scout.py score 1 --rent 1000
```

## Live data

`GET /api/market-rate` and the assistant's `market_rate` tool report the current average effective
interest rate for new German housing loans, straight from the Deutsche Bundesbank SDMX API
(`BBIM1/M.DE.B.A2C.A.R.A.2250.EUR.N`, keyless, cached 24 h). If the call fails, the static value
from `config/rates.yaml` is returned **and labelled as a fallback** — a stale number is never
passed off as today's. The calculators themselves stay pure and offline; the live rate is a
suggestion, never a silent default.

## Verifying the LLM integration

The test suite is hermetic on purpose (every Ollama call is faked), so it cannot prove the real
integration works. This does:

```bash
./scripts/verify_live.sh     # real Ollama: embedder, RAG, tool call, scoring
```

It prints PASS/FAIL per check, exits non-zero on a real failure, and exits 0 with a clear message
when Ollama simply is not running. Opt-in pytest checks against real public APIs (BORIS-NI,
Bundesbank):

```bash
uv run pytest -m live
```

## Status

Stage 1 (knowledge + finance assistant) and the Stage-2 scoring funnel are built: manual intake →
enrichment → transparent score → drilldown, in CLI, API and UI. See `PLAN.md` for what is left and
`docs/superpowers/plans/` for the executed plans. Later stages (per-object exposé evaluation,
copilot, dashboard) are sketched but not built.

## Quickstart (after `uv sync`)

```bash
# Deterministic calculators (no LLM needed)
uv run python scripts/finance.py annuity --principal 280000 --rate 3.6 --repayment 2.0
uv run python scripts/finance.py costs --price 350000 --bundesland Niedersachsen
uv run python scripts/finance.py yield --price 350000 --rent 1200
uv run python scripts/finance.py opcosts --area 100 --rent 1200          # Bewirtschaftungskosten
uv run python scripts/finance.py equity --price 300000 --rent 1500 \
  --equity 60000 --rate 3.6 --repayment 2.0                              # Eigenkapitalrendite

# Saved objects (manual intake — no scraping)
uv run python scripts/scout.py add --price 300000 --area 100 --bundesland NI --ort Lingen
uv run python scripts/scout.py list
uv run python scripts/scout.py delete 1

# Ask the assistant (needs Ollama running + a tool-calling model + an embedding model)
ollama serve & ollama pull qwen2.5:7b && ollama pull nomic-embed-text
uv run python scripts/ask.py "Welche Nebenkosten fallen beim Kauf in Niedersachsen an?"
uv run python scripts/ask.py "Welche Objekte habe ich gespeichert?"   # uses the list_listings tool
```

The assistant model is configurable via `OLLAMA_MODEL` (default a local tool-calling model), the
embedding model via `OLLAMA_EMBED_MODEL`. The knowledge index is embedded once and cached on disk
(`data/rag_index/`, regenerable); it is rebuilt automatically when the corpus changes.

## Web UI

```bash
cd frontend && npm install && npm run build && cd ..
uv run uvicorn estatescout.api:app --port 8000   # → http://localhost:8000
```

Three tabs:

- **Chat** — ask anything; every calculator the assistant calls is rendered as its own result card,
  with the knowledge sources it cited.
- **Rechner** — the six calculators as direct forms, no LLM involved (works with Ollama down).
- **Objekte** — your saved objects: intake form, table with €/m² and score badge, a per-object
  drilldown (bar per block, the weight it actually carried, confidence, and an honest list of what
  was missing and why), and an "Anreichern + bewerten" action.

Each assistant answer carries a collapsed **"Werkzeuge (n)"** panel listing every calculator it
called with the exact arguments and the exact result — the honest-harness claim, inspectable.

## Development

```bash
uv sync
uv run pytest           # tests + coverage floor (single-file runs: add --no-cov)
uv run ruff check .     # lint
cd frontend && npm install && npm test && npm run build
```

`uv run pytest` enforces a measured coverage floor (`fail_under` in `pyproject.toml`) and excludes
the `live` marker, so the default run never touches the network.

## License

MIT — see `LICENSE`.
