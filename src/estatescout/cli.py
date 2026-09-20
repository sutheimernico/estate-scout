"""Command-line interface.

`finance_app` exposes the deterministic calculators (no LLM needed) and reuses the same tool
adapters the assistant uses, so CLI numbers and assistant numbers are identical. `ask` wires the
local Ollama assistant and degrades honestly when Ollama is unreachable.
"""

import json

import typer

from .assistant.tools import dispatch
from .scout.model import Listing
from .scout.store import DEFAULT_DB, ListingStore

finance_app = typer.Typer(
    help="Deterministic real-estate finance calculators.", no_args_is_help=True
)


def _echo(result: dict | list) -> None:
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


@finance_app.command()
def opcosts(
    area: float = typer.Option(..., help="living area in m²"),
    rent: float = typer.Option(..., help="monthly Kaltmiete in EUR"),
    units: int = typer.Option(1, help="number of residential units"),
) -> None:
    """Annual Bewirtschaftungskosten estimate (Instandhaltung, Verwaltung, Mietausfall)."""
    _echo(
        dispatch(
            "operating_costs",
            {"living_area_sqm": area, "monthly_cold_rent": rent, "units": units},
        )
    )


@finance_app.command(name="equity")
def equity_cmd(
    price: float = typer.Option(..., help="purchase price in EUR"),
    rent: float = typer.Option(..., help="monthly Kaltmiete in EUR"),
    equity: float = typer.Option(..., help="invested equity in EUR"),
    rate: float = typer.Option(..., help="nominal interest p.a. in %"),
    repayment: float = typer.Option(..., help="anfängliche Tilgung in %"),
    ancillary: float = typer.Option(0.0, help="Kaufnebenkosten in EUR"),
    operating: float = typer.Option(0.0, help="Bewirtschaftungskosten EUR/year"),
) -> None:
    """First-year Eigenkapitalrendite (cash-on-cash) of a financed buy-to-let."""
    _echo(
        dispatch(
            "equity_return",
            {
                "purchase_price": price,
                "monthly_cold_rent": rent,
                "equity": equity,
                "annual_rate_percent": rate,
                "initial_repayment_percent": repayment,
                "ancillary_costs": ancillary,
                "annual_operating_costs": operating,
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
    from .assistant.chat import OllamaUnavailable
    from .assistant.factory import build_assistant

    store = ListingStore(DEFAULT_DB)
    try:
        resp = build_assistant(store).ask(question)
    except OllamaUnavailable:
        typer.echo(
            "Ollama ist nicht erreichbar. Starte 'ollama serve' und ziehe ein Modell "
            "(z.B. 'ollama pull qwen2.5:7b' + 'ollama pull nomic-embed-text').\n"
            "Die Rechner funktionieren ohne LLM: 'uv run python scripts/finance.py --help'."
        )
        raise typer.Exit(code=1) from None
    finally:
        store.close()
    typer.echo(render_response(resp))


scout_app = typer.Typer(help="Manage saved property objects (manual intake — no scraping).",
                        no_args_is_help=True)


@scout_app.command("add")
def add_listing(
    price: float = typer.Option(..., help="purchase price in EUR"),
    area: float = typer.Option(..., help="living area in m²"),
    bundesland: str = typer.Option(..., help="e.g. 'Niedersachsen' or 'NRW'"),
    ort: str = typer.Option("", help="city/town"),
    rooms: float | None = typer.Option(None, help="number of rooms"),
    year: int | None = typer.Option(None, help="year built"),
    object_type: str = typer.Option("wohnung", help="wohnung | haus | grundstueck"),
    source: str = typer.Option("", help="source URL"),
    db: str = typer.Option(str(DEFAULT_DB), help="SQLite path"),
) -> None:
    """Add a property object you found. Object attributes only — never seller contact data."""
    store = ListingStore(db)
    try:
        saved = store.add(
            Listing(
                price=price,
                living_area_sqm=area,
                bundesland=bundesland,
                ort=ort,
                rooms=rooms,
                year_built=year,
                object_type=object_type,
                source_url=source,
            )
        )
    except ValueError as e:
        typer.echo(f"Ungültige Eingabe: {e}")
        raise typer.Exit(code=1) from None
    finally:
        store.close()
    _echo(
        {
            "id": saved.id,
            "price": saved.price,
            "bundesland": saved.bundesland,
            "ort": saved.ort,
            "price_per_sqm": round(saved.price_per_sqm, 2),
        }
    )


@scout_app.command("list")
def list_listings(db: str = typer.Option(str(DEFAULT_DB), help="SQLite path")) -> None:
    """List saved property objects."""
    store = ListingStore(db)
    try:
        items = store.list()
    finally:
        store.close()
    _echo(
        [
            {
                "id": it.id,
                "price": it.price,
                "bundesland": it.bundesland,
                "ort": it.ort,
                "price_per_sqm": round(it.price_per_sqm, 2),
            }
            for it in items
        ]
    )


@scout_app.command("delete")
def delete_listing_cmd(
    listing_id: int = typer.Argument(..., help="listing id (see 'scout list')"),
    db: str = typer.Option(str(DEFAULT_DB), help="SQLite path"),
) -> None:
    """Delete a saved object by id."""
    store = ListingStore(db)
    try:
        ok = store.delete(listing_id)
    finally:
        store.close()
    if not ok:
        typer.echo(f"Kein Objekt mit id {listing_id}.")
        raise typer.Exit(code=1)
    typer.echo(f"Objekt {listing_id} gelöscht.")
