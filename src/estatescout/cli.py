"""Command-line interface.

`finance_app` exposes the deterministic calculators (no LLM needed) and reuses the same tool
adapters the assistant uses, so CLI numbers and assistant numbers are identical. `ask` wires the
local Ollama assistant and degrades honestly when Ollama is unreachable.
"""

import json

import typer

from .assistant.tools import dispatch

finance_app = typer.Typer(
    help="Deterministic real-estate finance calculators.", no_args_is_help=True
)


def _echo(result: dict) -> None:
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@finance_app.command()
def annuity(
    principal: float = typer.Option(..., help="loan amount in EUR"),
    rate: float = typer.Option(..., help="nominal interest p.a. in %, e.g. 3.6"),
    repayment: float = typer.Option(..., help="anfängliche Tilgung in %, e.g. 2.0"),
    sondertilgung: float = typer.Option(0.0, help="optional extra repayment EUR/year"),
) -> None:
    """Annuitätendarlehen: monthly payment, total interest, payoff, remaining debt per year."""
    _echo(
        dispatch(
            "annuity",
            {
                "principal": principal,
                "annual_rate_percent": rate,
                "initial_repayment_percent": repayment,
                "annual_sondertilgung": sondertilgung,
            },
        )
    )


@finance_app.command()
def costs(
    price: float = typer.Option(..., help="purchase price in EUR"),
    bundesland: str = typer.Option(..., help="e.g. 'Niedersachsen' or 'NRW'"),
    makler: float | None = typer.Option(None, help="buyer Makler share in %; omit for default"),
) -> None:
    """Kaufnebenkosten: Grunderwerbsteuer, notary, Grundbuch, Makler, min equity."""
    args: dict = {"purchase_price": price, "bundesland": bundesland}
    if makler is not None:
        args["makler_rate_percent"] = makler
    _echo(dispatch("purchase_costs", args))


@finance_app.command()
def afford(
    income: float = typer.Option(..., help="net monthly household income in EUR"),
    equity: float = typer.Option(..., help="available equity in EUR"),
    rate: float = typer.Option(..., help="nominal interest p.a. in %"),
    repayment: float = typer.Option(..., help="anfängliche Tilgung in %"),
    bundesland: str = typer.Option(..., help="e.g. 'Niedersachsen' or 'NRW'"),
) -> None:
    """Maximum affordable purchase price from a net-income budget."""
    _echo(
        dispatch(
            "affordability",
            {
                "net_monthly_income": income,
                "equity": equity,
                "annual_rate_percent": rate,
                "initial_repayment_percent": repayment,
                "bundesland": bundesland,
            },
        )
    )


@finance_app.command(name="yield")
def yield_cmd(
    price: float = typer.Option(..., help="purchase price in EUR"),
    rent: float = typer.Option(..., help="monthly Kaltmiete in EUR"),
    operating: float = typer.Option(0.0, help="non-allocable running costs EUR/year"),
    ancillary: float = typer.Option(0.0, help="Kaufnebenkosten in EUR"),
) -> None:
    """Rental yield (gross/net) and Kaufpreisfaktor."""
    _echo(
        dispatch(
            "yield_metrics",
            {
                "purchase_price": price,
                "monthly_cold_rent": rent,
                "annual_operating_costs": operating,
                "ancillary_costs": ancillary,
            },
        )
    )


def render_response(resp) -> str:
    """Format an AssistantResponse for the terminal (pure — testable without Ollama)."""
    lines = [resp.answer.strip()]
    if resp.tool_calls:
        lines.append("")
        lines.append("Berechnungen (aus dem Finanzkern):")
        for tc in resp.tool_calls:
            lines.append(f"  - {tc['name']}: {json.dumps(tc['result'], ensure_ascii=False)}")
    if resp.sources:
        lines.append("")
        lines.append("Quellen: " + ", ".join(resp.sources))
    lines.append("")
    lines.append(resp.disclaimer)
    return "\n".join(lines)


def ask(question: str) -> None:
    """Ask a real-estate question; the assistant uses RAG for knowledge and tools for numbers."""
    from .assistant.assistant import Assistant
    from .assistant.chat import OllamaChat, OllamaUnavailable
    from .rag.embedder import OllamaEmbedder
    from .rag.index import RagIndex, load_corpus

    try:
        embedder = OllamaEmbedder()
        index = RagIndex.build(load_corpus(), embedder)
        resp = Assistant(OllamaChat(), index=index, embedder=embedder).ask(question)
    except OllamaUnavailable:
        typer.echo(
            "Ollama ist nicht erreichbar. Starte 'ollama serve' und ziehe ein Modell "
            "(z.B. 'ollama pull qwen2.5:7b' + 'ollama pull nomic-embed-text').\n"
            "Die Rechner funktionieren ohne LLM: 'uv run python scripts/finance.py --help'."
        )
        raise typer.Exit(code=1) from None
    typer.echo(render_response(resp))
