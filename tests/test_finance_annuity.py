"""Trust-anchor tests for the Annuitätendarlehen calculator.

Reference values are hand-computed. German convention: the annual annuity equals
principal * (nominal interest rate + initial repayment rate); the monthly payment is
that / 12 and stays constant while the interest share shrinks and the repayment grows.
"""

import pytest

from estatescout.finance.annuity import amortize, annuity


def test_monthly_payment_formula():
    res = annuity(principal=300_000, annual_rate=0.036, initial_repayment=0.02)
    # 300_000 * (0.036 + 0.02) / 12 = 16_800 / 12 = 1_400.0
    assert res.monthly_payment == pytest.approx(1_400.0)


def test_first_two_months_exact():
    rows = amortize(principal=300_000, annual_rate=0.036, initial_repayment=0.02)
    m1 = rows[0]
    assert m1.month == 1
    assert m1.interest == pytest.approx(900.0)  # 300_000 * 0.036/12
    assert m1.principal == pytest.approx(500.0)  # 1_400 - 900
    assert m1.remaining == pytest.approx(299_500.0)
    m2 = rows[1]
    assert m2.interest == pytest.approx(898.5)  # 299_500 * 0.003
    assert m2.principal == pytest.approx(501.5)
    assert m2.remaining == pytest.approx(298_998.5)


def test_principal_fully_repaid_and_interest_consistent():
    res = annuity(principal=250_000, annual_rate=0.04, initial_repayment=0.025)
    total_principal = sum(y.principal_paid for y in res.yearly_schedule)
    assert total_principal == pytest.approx(250_000, abs=0.01)
    assert res.yearly_schedule[-1].remaining_debt == pytest.approx(0.0, abs=0.01)
    assert res.total_interest == pytest.approx(res.total_paid - 250_000, abs=0.01)


def test_remaining_strictly_decreasing_to_zero():
    rows = amortize(principal=200_000, annual_rate=0.03, initial_repayment=0.02)
    remainings = [r.remaining for r in rows]
    assert all(a > b for a, b in zip(remainings, remainings[1:], strict=False))
    assert remainings[-1] == pytest.approx(0.0, abs=0.01)


def test_zero_interest_is_pure_repayment():
    res = annuity(principal=120_000, annual_rate=0.0, initial_repayment=0.10)
    assert res.monthly_payment == pytest.approx(1_000.0)  # 120_000 * 0.10 / 12
    assert res.months_to_payoff == 120  # 120_000 / 1_000
    assert res.total_interest == pytest.approx(0.0, abs=1e-6)


def test_non_amortizing_loan_raises():
    with pytest.raises(ValueError):
        annuity(principal=100_000, annual_rate=0.05, initial_repayment=0.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        annuity(principal=-1, annual_rate=0.03, initial_repayment=0.02)
    with pytest.raises(ValueError):
        annuity(principal=100_000, annual_rate=-0.01, initial_repayment=0.02)
    with pytest.raises(ValueError):
        annuity(
            principal=100_000, annual_rate=0.03, initial_repayment=0.02, annual_sondertilgung=-1
        )


def test_sondertilgung_zero_matches_base():
    base = annuity(principal=300_000, annual_rate=0.036, initial_repayment=0.02)
    with_zero = annuity(
        principal=300_000, annual_rate=0.036, initial_repayment=0.02, annual_sondertilgung=0.0
    )
    assert with_zero.months_to_payoff == base.months_to_payoff
    assert with_zero.total_interest == pytest.approx(base.total_interest)


def test_sondertilgung_shortens_term_and_cuts_interest():
    base = annuity(principal=300_000, annual_rate=0.036, initial_repayment=0.02)
    fast = annuity(
        principal=300_000, annual_rate=0.036, initial_repayment=0.02, annual_sondertilgung=6_000
    )
    assert fast.months_to_payoff < base.months_to_payoff
    assert fast.total_interest < base.total_interest


def test_sondertilgung_still_repays_exact_principal():
    res = annuity(
        principal=250_000, annual_rate=0.04, initial_repayment=0.025, annual_sondertilgung=5_000
    )
    total_principal = sum(
        y.principal_paid + y.sondertilgung_paid for y in res.yearly_schedule
    )
    assert total_principal == pytest.approx(250_000, abs=0.01)
    assert res.yearly_schedule[-1].remaining_debt == pytest.approx(0.0, abs=0.01)
