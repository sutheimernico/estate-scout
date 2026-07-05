# estate-scout

A local, free real-estate **knowledge assistant + finance calculators** for the German market
(Niedersachsen / NRW). Ask it anything about buying residential property and financing it; the
numbers come from tested code, not from the language model.

**Honest harness — not tax, investment, or financing advice.** No listing scraping. Runs entirely
on your machine via [Ollama](https://ollama.com); no paid APIs.

## Why the numbers are trustworthy

A local 7B model cannot be trusted with arithmetic. So it doesn't do any: every number
(Annuitätendarlehen rate, Kaufnebenkosten, Leistbarkeit, Mietrendite) is computed by tested Python
in `finance/`. The assistant understands your question, calls the right calculator, and explains the
result. Tax rates and thresholds live in versioned config, each tagged with source + date.

## Status

Stage 1 (knowledge + finance assistant) is under construction by the autonomous build loop. See
`PLAN.md` for the backlog and `docs/superpowers/specs/` for the design. Later stages (scouting
funnel, per-object evaluation, copilot, dashboard) are sketched but not built.

## Quickstart (after `uv sync`)

```bash
# Deterministic calculators (no LLM needed)
uv run python scripts/finance.py annuity --price 350000 --equity 70000 --rate 3.6 --repayment 2.0

# Ask the assistant (needs Ollama running + a tool-calling model)
ollama serve & ollama pull qwen2.5:7b
uv run python scripts/ask.py "Welche Nebenkosten fallen beim Kauf in Niedersachsen an?"
```

The assistant model is configurable via `OLLAMA_MODEL` (default a local tool-calling model).

## Development

```bash
uv sync
uv run pytest -q        # tests (the finance core is fully covered — the trust anchor)
uv run ruff check .     # lint
```

## License

MIT — see `LICENSE`.
