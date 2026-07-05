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
from estatescout.finance.purchase_costs import purchase_costs
from estatescout.finance.yield_metrics import yield_metrics


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
}


def tool_specs() -> list[dict]:
    """The tool schemas to pass to the model's ``tools`` parameter."""
    return [t.spec for t in TOOLS.values()]


def dispatch(name: str, args: dict) -> dict:
    """Validate required args and run the named finance tool. Numbers come from finance/."""
    if name not in TOOLS:
        raise ValueError(f"unknown tool '{name}' (known: {', '.join(sorted(TOOLS))})")
    tool = TOOLS[name]
    required = tool.spec["function"]["parameters"]["required"]
    missing = [r for r in required if r not in args]
    if missing:
        raise ValueError(f"tool '{name}' missing required args: {', '.join(missing)}")
    return tool.run(args)
