"""LLM-facing tool layer over the deterministic finance calculators.

Each finance function is exposed as an Ollama/OpenAI-style tool schema plus an adapter that
runs it. The tool interface uses human-natural units (percent for rates) and the adapter
converts to the finance core's fractions — this reduces the classic LLM mistake of passing
3.6 where 0.036 is meant. Every number in a tool result comes from `finance/`; the model
only chooses the tool and its arguments, then explains the returned numbers.
"""

from collections.abc import Callable
from dataclasses import dataclass

from estatescout.finance.affordability import affordability
from estatescout.finance.annuity import annuity
from estatescout.finance.equity_return import equity_return
from estatescout.finance.operating_costs import operating_costs
from estatescout.finance.purchase_costs import purchase_costs
from estatescout.finance.rates_live import market_rate
from estatescout.finance.yield_metrics import yield_metrics
from estatescout.scout.scoring import score_listing
from estatescout.scout.scoring import to_dict as score_to_dict
from estatescout.scout.store import ListingStore


def _eur(x: float) -> float:
    return round(x, 2)


def _pct(x: float) -> float:
    return round(x * 100, 3)


def _p(description: str, typ: str = "number") -> dict:
    """Shorthand for a JSON-schema property."""
    return {"type": typ, "description": description}


@dataclass(frozen=True)
class Tool:
    spec: dict  # JSON schema passed to the model
    run: Callable[[dict], dict]  # tool args -> JSON-serializable result (numbers from finance/)


def _run_annuity(a: dict) -> dict:
    res = annuity(
        a["principal"],
        a["annual_rate_percent"] / 100,
        a["initial_repayment_percent"] / 100,
        annual_sondertilgung=a.get("annual_sondertilgung", 0.0),
    )
    return {
        "monthly_payment": _eur(res.monthly_payment),
        "total_interest": _eur(res.total_interest),
        "total_paid": _eur(res.total_paid),
        "months_to_payoff": res.months_to_payoff,
        "years_to_payoff": round(res.months_to_payoff / 12, 1),
        "remaining_debt_by_year": [
            {"year": y.year, "remaining_debt": _eur(y.remaining_debt)} for y in res.yearly_schedule
        ],
    }


def _run_purchase_costs(a: dict) -> dict:
    makler = a.get("makler_rate_percent")
    res = purchase_costs(
        a["purchase_price"],
        a["bundesland"],
        makler_rate=(makler / 100 if makler is not None else None),
    )
    return {
        "bundesland": res.bundesland,
        "grunderwerbsteuer": _eur(res.grunderwerbsteuer),
        "notary": _eur(res.notary),
        "land_registry": _eur(res.land_registry),
        "makler": _eur(res.makler),
        "total_ancillary": _eur(res.total_ancillary),
        "total_investment": _eur(res.total_investment),
        "ancillary_quota_percent": _pct(res.ancillary_quota),
        "min_equity": _eur(res.min_equity),
    }


def _run_affordability(a: dict) -> dict:
    res = affordability(
        a["net_monthly_income"],
        a["equity"],
        a["annual_rate_percent"] / 100,
        a["initial_repayment_percent"] / 100,
        a["bundesland"],
        existing_obligations=a.get("existing_obligations", 0.0),
        running_costs_monthly=a.get("running_costs_monthly", 0.0),
    )
    return {
        "max_monthly_payment": _eur(res.max_monthly_payment),
        "max_loan": _eur(res.max_loan),
        "max_purchase_price": _eur(res.max_purchase_price),
        "ancillary_quota_percent": _pct(res.ancillary_quota),
        "equity": _eur(res.equity),
    }


def _run_yield(a: dict) -> dict:
    res = yield_metrics(
        a["purchase_price"],
        a["monthly_cold_rent"],
        annual_operating_costs=a.get("annual_operating_costs", 0.0),
        ancillary_costs=a.get("ancillary_costs", 0.0),
    )
    return {
        "annual_cold_rent": _eur(res.annual_cold_rent),
        "gross_yield_percent": _pct(res.gross_yield),
        "net_yield_percent": _pct(res.net_yield),
        "kaufpreisfaktor": round(res.kaufpreisfaktor, 1),
    }


def _run_operating_costs(a: dict) -> dict:
    res = operating_costs(
        a["living_area_sqm"],
        a["monthly_cold_rent"],
        units=int(a.get("units", 1)),
    )
    return {
        "instandhaltung": _eur(res.instandhaltung),
        "verwaltung": _eur(res.verwaltung),
        "mietausfallwagnis": _eur(res.mietausfallwagnis),
        "total_annual": _eur(res.total_annual),
    }


def _run_equity_return(a: dict) -> dict:
    res = equity_return(
        a["purchase_price"],
        a["monthly_cold_rent"],
        a["equity"],
        a["annual_rate_percent"] / 100,
        a["initial_repayment_percent"] / 100,
        ancillary_costs=a.get("ancillary_costs", 0.0),
        annual_operating_costs=a.get("annual_operating_costs", 0.0),
    )
    return {
        "loan": _eur(res.loan),
        "annual_debt_service": _eur(res.annual_debt_service),
        "net_operating_income": _eur(res.net_operating_income),
        "cashflow_before_tax": _eur(res.cashflow_before_tax),
        "cash_on_cash_percent": _pct(res.cash_on_cash),
    }


def _run_market_rate(a: dict) -> dict:
    res = market_rate()
    return {
        "annual_rate_percent": res.annual_rate_percent,
        "as_of": res.as_of,
        "source": res.source,
        "origin": res.origin,  # bundesbank_live | bundesbank_cache | static_fallback
    }


def _spec(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOLS: dict[str, Tool] = {
    "annuity": Tool(
        spec=_spec(
            "annuity",
            "Compute a German Annuitätendarlehen: constant monthly payment, total interest, "
            "payoff duration and the remaining debt per year.",
            {
                "principal": _p("loan amount in EUR"),
                "annual_rate_percent": _p("nominal interest p.a. in %, e.g. 3.6"),
                "initial_repayment_percent": _p("anfängliche Tilgung in %, e.g. 2.0"),
                "annual_sondertilgung": _p("optional extra repayment EUR/year"),
            },
            ["principal", "annual_rate_percent", "initial_repayment_percent"],
        ),
        run=_run_annuity,
    ),
    "purchase_costs": Tool(
        spec=_spec(
            "purchase_costs",
            "Break down German Kaufnebenkosten (Grunderwerbsteuer per Bundesland, notary, "
            "Grundbuch, Makler) and the minimum equity needed.",
            {
                "purchase_price": _p("property price in EUR"),
                "bundesland": _p("e.g. 'Niedersachsen' or 'NRW'", "string"),
                "makler_rate_percent": _p("buyer Makler share in %; omit for default, 0 for none"),
            },
            ["purchase_price", "bundesland"],
        ),
        run=_run_purchase_costs,
    ),
    "affordability": Tool(
        spec=_spec(
            "affordability",
            "Maximum affordable purchase price from net monthly income, equity, interest and "
            "repayment, accounting for ancillary costs per Bundesland.",
            {
                "net_monthly_income": _p("net monthly household income EUR"),
                "equity": _p("available equity in EUR"),
                "annual_rate_percent": _p("nominal interest p.a. in %"),
                "initial_repayment_percent": _p("anfängliche Tilgung in %"),
                "bundesland": _p("e.g. 'Niedersachsen' or 'NRW'", "string"),
                "existing_obligations": _p("other monthly loan payments EUR"),
                "running_costs_monthly": _p("estimated monthly running costs EUR"),
            },
            [
                "net_monthly_income",
                "equity",
                "annual_rate_percent",
                "initial_repayment_percent",
                "bundesland",
            ],
        ),
        run=_run_affordability,
    ),
    "yield_metrics": Tool(
        spec=_spec(
            "yield_metrics",
            "Rental yield of a buy-to-let: gross/net yield and Kaufpreisfaktor "
            "(price-to-annual-rent multiplier).",
            {
                "purchase_price": _p("property price in EUR"),
                "monthly_cold_rent": _p("monthly Kaltmiete in EUR"),
                "annual_operating_costs": _p("non-allocable running costs EUR/year"),
                "ancillary_costs": _p("Kaufnebenkosten in EUR"),
            },
            ["purchase_price", "monthly_cold_rent"],
        ),
        run=_run_yield,
    ),
    "operating_costs": Tool(
        spec=_spec(
            "operating_costs",
            "Estimate a landlord's annual Bewirtschaftungskosten (Instandhaltung, Verwaltung, "
            "Mietausfallwagnis) from config-anchored practice values.",
            {
                "living_area_sqm": _p("living area in m²"),
                "monthly_cold_rent": _p("monthly Kaltmiete in EUR"),
                "units": _p("number of residential units, default 1"),
            },
            ["living_area_sqm", "monthly_cold_rent"],
        ),
        run=_run_operating_costs,
    ),
    "equity_return": Tool(
        spec=_spec(
            "equity_return",
            "First-year Eigenkapitalrendite (cash-on-cash) of a financed buy-to-let: cashflow "
            "after debt service relative to invested equity.",
            {
                "purchase_price": _p("property price in EUR"),
                "monthly_cold_rent": _p("monthly Kaltmiete in EUR"),
                "equity": _p("invested equity in EUR"),
                "annual_rate_percent": _p("nominal interest p.a. in %, e.g. 3.6"),
                "initial_repayment_percent": _p("anfängliche Tilgung in %, e.g. 2.0"),
                "ancillary_costs": _p("Kaufnebenkosten in EUR"),
                "annual_operating_costs": _p("Bewirtschaftungskosten EUR/year"),
            },
            [
                "purchase_price",
                "monthly_cold_rent",
                "equity",
                "annual_rate_percent",
                "initial_repayment_percent",
            ],
        ),
        run=_run_equity_return,
    ),
    "market_rate": Tool(
        spec=_spec(
            "market_rate",
            "Current average effective interest rate for new German housing loans to private "
            "households (Deutsche Bundesbank). Use it when the user asks what rates are right "
            "now or has no rate of their own. Always report the returned 'as_of' and 'source', "
            "and say so if 'origin' is 'static_fallback' (then the figure may be stale).",
            {},
            [],
        ),
        run=_run_market_rate,
    ),
}


def tool_specs() -> list[dict]:
    """The tool schemas to pass to the model's ``tools`` parameter."""
    return [t.spec for t in TOOLS.values()]


def _clean_args(name: str, tool: Tool, args: dict) -> dict:
    """Drop explicit nulls, coerce numeric strings, and type-check against the tool spec.

    Local 7B models routinely send numbers as strings or explicit nulls — coerce what is
    safe, reject the rest loudly so the caller (API 400 / loop error-feedback) can react.
    """
    props = tool.spec["function"]["parameters"]["properties"]
    cleaned: dict = {}
    for key, value in args.items():
        if value is None:
            continue  # explicit null == absent; required-check below reports it
        expected = props.get(key, {}).get("type")
        if expected == "number":
            if isinstance(value, bool):
                raise ValueError(f"tool '{name}' argument '{key}' must be a number, got {value!r}")
            if not isinstance(value, int | float):
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"tool '{name}' argument '{key}' must be a number, got {value!r}"
                    ) from None
        elif expected == "string" and not isinstance(value, str):
            raise ValueError(f"tool '{name}' argument '{key}' must be a string, got {value!r}")
        cleaned[key] = value
    return cleaned


def dispatch(name: str, args: dict, *, tools: dict[str, Tool] | None = None) -> dict:
    """Validate, type-coerce and run the named tool. Numbers come from finance/."""
    tools_map = tools if tools is not None else TOOLS
    if name not in tools_map:
        raise ValueError(f"unknown tool '{name}' (known: {', '.join(sorted(tools_map))})")
    tool = tools_map[name]
    cleaned = _clean_args(name, tool, args)
    required = tool.spec["function"]["parameters"]["required"]
    missing = [r for r in required if r not in cleaned]
    if missing:
        raise ValueError(f"tool '{name}' missing required args: {', '.join(missing)}")
    return tool.run(cleaned)


def listing_tools(store: ListingStore) -> dict[str, Tool]:
    """Tools over the user's saved listings (Stage 2). Read-only for the model."""

    def _run_list(a: dict) -> dict:
        items = store.list()
        return {
            "count": len(items),
            "listings": [
                {
                    "id": it.id,
                    "ort": it.ort,
                    "bundesland": it.bundesland,
                    "object_type": it.object_type,
                    "price": _eur(it.price),
                    "living_area_sqm": it.living_area_sqm,
                    "price_per_sqm": _eur(it.price_per_sqm),
                    "rooms": it.rooms,
                    "year_built": it.year_built,
                }
                for it in items
            ],
        }

    def _run_score(a: dict) -> dict:
        listing_id = int(a["listing_id"])
        listing = store.get(listing_id)
        if listing is None:
            return {"error": f"no listing with id {listing_id}"}
        stored = store.get_enrichment(listing_id)
        if stored is None:
            return {
                "error": (
                    f"listing {listing_id} has not been enriched yet — "
                    "run the enrichment before scoring"
                )
            }
        report = score_listing(
            listing, stored.enrichment, monthly_cold_rent=a.get("monthly_cold_rent")
        )
        return score_to_dict(report)

    return {
        "list_listings": Tool(
            spec=_spec(
                "list_listings",
                "List the property objects the user has saved (id, location, price, size, "
                "price per m²). Use for any question about the user's own objects "
                "('meine Objekte').",
                {},
                [],
            ),
            run=_run_list,
        ),
        "score_listing": Tool(
            spec=_spec(
                "score_listing",
                "Return the transparent 0-100 assessment of one saved object: total, the "
                "three building blocks (yield/price/region) with their weights and inputs, "
                "the confidence and the reasons for anything missing. Explain the returned "
                "numbers; never compute a score yourself.",
                {
                    "listing_id": _p("id of the saved object (see list_listings)"),
                    "monthly_cold_rent": _p("expected monthly Kaltmiete in EUR, if known"),
                },
                ["listing_id"],
            ),
            run=_run_score,
        ),
    }
