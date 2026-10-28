"""Typed request/response models for the six finance calculators.

One source of truth for three consumers: FastAPI (request validation + the OpenAPI schema),
the LLM tool specs (derived from the input models via ``model_json_schema()``, see
``assistant.tools``) and the frontend types (hand-written to match, see ``frontend/src/api.ts``).
Units are human-natural (percent for rates); the adapters in ``assistant.tools`` convert to the
fractions the finance core expects.
"""

from pydantic import BaseModel, Field


class AnnuityIn(BaseModel):
    principal: float = Field(description="loan amount in EUR")
    annual_rate_percent: float = Field(
        description="nominal interest (Sollzins) p.a. in %, e.g. 3.6"
    )
    initial_repayment_percent: float = Field(description="anfängliche Tilgung in %, e.g. 2.0")
    annual_sondertilgung: float | None = Field(
        default=None, description="optional extra repayment EUR/year"
    )
    zinsbindung_years: int | None = Field(
        default=None,
        description=(
            "optional fixed-rate period in years (Zinsbindung, e.g. 10); adds the Restschuld "
            "that is still owed when it ends"
        ),
    )


class RemainingDebtYear(BaseModel):
    year: int
    remaining_debt: float


class AnnuityOut(BaseModel):
    monthly_payment: float
    total_interest: float
    total_paid: float
    months_to_payoff: int
    years_to_payoff: float
    remaining_debt_by_year: list[RemainingDebtYear]
    # present only when a Zinsbindung was requested
    zinsbindung_years: int | None = None
    restschuld_after_zinsbindung: float | None = None
    interest_during_zinsbindung: float | None = None


class PurchaseCostsIn(BaseModel):
    purchase_price: float = Field(description="property price in EUR")
    bundesland: str = Field(description="e.g. 'Niedersachsen' or 'NRW'")
    makler_rate_percent: float | None = Field(
        default=None, description="buyer Makler share in %; omit for default, 0 for none"
    )


class PurchaseCostsOut(BaseModel):
    bundesland: str
    grunderwerbsteuer: float
    notary: float
    land_registry: float
    makler: float
    total_ancillary: float
    total_investment: float
    ancillary_quota_percent: float
    min_equity: float


class AffordabilityIn(BaseModel):
    net_monthly_income: float = Field(description="net monthly household income EUR")
    equity: float = Field(description="available equity in EUR")
    annual_rate_percent: float = Field(description="nominal interest p.a. in %")
    initial_repayment_percent: float = Field(description="anfängliche Tilgung in %")
    bundesland: str = Field(description="e.g. 'Niedersachsen' or 'NRW'")
    existing_obligations: float | None = Field(
        default=None, description="other monthly loan payments EUR"
    )
    running_costs_monthly: float | None = Field(
        default=None, description="estimated monthly running costs EUR"
    )


class AffordabilityOut(BaseModel):
    max_monthly_payment: float
    max_loan: float
    max_purchase_price: float
    ancillary_quota_percent: float
    equity: float


class YieldIn(BaseModel):
    purchase_price: float = Field(description="property price in EUR")
    monthly_cold_rent: float = Field(description="monthly Kaltmiete in EUR")
    annual_operating_costs: float | None = Field(
        default=None, description="non-allocable running costs EUR/year"
    )
    ancillary_costs: float | None = Field(default=None, description="Kaufnebenkosten in EUR")


class YieldOut(BaseModel):
    annual_cold_rent: float
    gross_yield_percent: float
    net_yield_percent: float
    kaufpreisfaktor: float


class OperatingCostsIn(BaseModel):
    living_area_sqm: float = Field(description="living area in m²")
    monthly_cold_rent: float = Field(description="monthly Kaltmiete in EUR")
    units: float | None = Field(default=None, description="number of residential units, default 1")


class OperatingCostsOut(BaseModel):
    instandhaltung: float
    verwaltung: float
    mietausfallwagnis: float
    total_annual: float


class EquityReturnIn(BaseModel):
    purchase_price: float = Field(description="property price in EUR")
    monthly_cold_rent: float = Field(description="monthly Kaltmiete in EUR")
    equity: float = Field(description="invested equity in EUR")
    annual_rate_percent: float = Field(description="nominal interest p.a. in %, e.g. 3.6")
    initial_repayment_percent: float = Field(description="anfängliche Tilgung in %, e.g. 2.0")
    ancillary_costs: float | None = Field(default=None, description="Kaufnebenkosten in EUR")
    annual_operating_costs: float | None = Field(
        default=None, description="Bewirtschaftungskosten EUR/year"
    )


class EquityReturnOut(BaseModel):
    loan: float
    annual_debt_service: float
    net_operating_income: float
    cashflow_before_tax: float
    cash_on_cash_percent: float
    year1_tilgung: float
    return_incl_tilgung_percent: float
