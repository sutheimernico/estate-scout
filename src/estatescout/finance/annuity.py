"""Annuitätendarlehen — the constant-payment German mortgage.

The annual annuity equals ``principal * (annual_rate + initial_repayment)``; the monthly
payment is that divided by 12 and stays constant over the term. Each month the interest
share (``remaining * annual_rate / 12``) shrinks and the repayment share grows, so the
loan amortizes faster over time. Rates are passed as fractions (0.036 = 3.6 %).

Pure and deterministic — no LLM, no I/O. This is a trust-anchor module: every number the
assistant ever surfaces about a loan originates here.
"""

from dataclasses import dataclass

_EPS = 1e-9


@dataclass(frozen=True)
class MonthRow:
    """One month of the amortization schedule (full precision, not rounded)."""

    month: int
    interest: float
    principal: float
    remaining: float


@dataclass(frozen=True)
class YearRow:
    """Per-year aggregation of the schedule, for compact display."""

    year: int
    interest_paid: float
    principal_paid: float
    remaining_debt: float


@dataclass(frozen=True)
class AnnuityResult:
    monthly_payment: float
    total_interest: float
    total_paid: float
    months_to_payoff: int
    yearly_schedule: list[YearRow]


def amortize(
    principal: float,
    annual_rate: float,
    initial_repayment: float,
    *,
    max_years: int = 60,
) -> list[MonthRow]:
    """Month-by-month amortization of an Annuitätendarlehen.

    Args:
        principal: loan amount in EUR (> 0).
        annual_rate: nominal annual interest rate as a fraction (>= 0), e.g. 0.036.
        initial_repayment: anfängliche Tilgung as a fraction (> 0), e.g. 0.02.
        max_years: safety cap; a loan that has not amortized by then raises.

    Returns:
        One :class:`MonthRow` per month until the debt reaches zero. The final month's
        payment is the (usually smaller) partial payment that clears the remaining debt.
    """
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")
    if initial_repayment <= 0:
        raise ValueError("initial_repayment must be > 0 (a loan with no repayment never amortizes)")

    monthly_rate = annual_rate / 12.0
    payment = principal * (annual_rate + initial_repayment) / 12.0

    rows: list[MonthRow] = []
    remaining = principal
    max_months = max_years * 12
    for month in range(1, max_months + 1):
        interest = remaining * monthly_rate
        principal_part = payment - interest
        if principal_part >= remaining:  # final, partial payment clears the loan
            principal_part = remaining
        remaining -= principal_part
        if remaining < _EPS:
            remaining = 0.0
        rows.append(MonthRow(month=month, interest=interest, principal=principal_part,
                             remaining=remaining))
        if remaining == 0.0:
            return rows

    raise ValueError(f"loan does not amortize within {max_years} years")


def annuity(
    principal: float,
    annual_rate: float,
    initial_repayment: float,
    *,
    max_years: int = 60,
) -> AnnuityResult:
    """Summarize an Annuitätendarlehen: monthly payment, totals, per-year schedule.

    See :func:`amortize` for the argument semantics.
    """
    rows = amortize(principal, annual_rate, initial_repayment, max_years=max_years)
    payment = principal * (annual_rate + initial_repayment) / 12.0

    yearly: list[YearRow] = []
    for start in range(0, len(rows), 12):
        chunk = rows[start : start + 12]
        yearly.append(
            YearRow(
                year=start // 12 + 1,
                interest_paid=sum(r.interest for r in chunk),
                principal_paid=sum(r.principal for r in chunk),
                remaining_debt=chunk[-1].remaining,
            )
        )

    total_interest = sum(r.interest for r in rows)
    total_paid = sum(r.interest + r.principal for r in rows)
    return AnnuityResult(
        monthly_payment=payment,
        total_interest=total_interest,
        total_paid=total_paid,
        months_to_payoff=len(rows),
        yearly_schedule=yearly,
    )
