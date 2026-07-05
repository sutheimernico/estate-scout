"""Tests for the affordability (max purchase price) calculator."""

import pytest

from estatescout.finance.affordability import affordability


def test_payment_budget_respects_income_cap():
    a = affordability(
        net_monthly_income=4_000, equity=60_000, annual_rate=0.036,
        initial_repayment=0.02, bundesland="NI", max_rate_to_net_income=0.35,
    )
    assert a.max_monthly_payment == pytest.approx(1_400.0)  # 4_000 * 0.35


def test_worked_example_max_loan_and_price():
    # budget 1_400/mo, (rate+repayment)=0.056 -> max_loan = 1_400*12/0.056 = 300_000
    # NI quota (makler off) = 0.05 + 0.015 + 0.005 = 0.07 -> price = (300_000+60_000)/1.07
    a = affordability(
        net_monthly_income=4_000, equity=60_000, annual_rate=0.036,
        initial_repayment=0.02, bundesland="NI", max_rate_to_net_income=0.35,
        makler_rate=0.0,
    )
    assert a.max_loan == pytest.approx(300_000.0)
    assert a.ancillary_quota == pytest.approx(0.07)
    assert a.max_purchase_price == pytest.approx(360_000.0 / 1.07)


def test_more_income_allows_higher_price():
    kw = dict(equity=50_000, annual_rate=0.035, initial_repayment=0.02, bundesland="NW")
    low = affordability(net_monthly_income=3_000, **kw)
    high = affordability(net_monthly_income=5_000, **kw)
    assert high.max_purchase_price > low.max_purchase_price


def test_obligations_and_running_costs_reduce_budget():
    base = affordability(
        net_monthly_income=4_000, equity=0, annual_rate=0.035,
        initial_repayment=0.02, bundesland="NI",
    )
    reduced = affordability(
        net_monthly_income=4_000, equity=0, annual_rate=0.035,
        initial_repayment=0.02, bundesland="NI",
        existing_obligations=300, running_costs_monthly=200,
    )
    assert reduced.max_monthly_payment == pytest.approx(base.max_monthly_payment - 500)
    assert reduced.max_purchase_price < base.max_purchase_price


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        affordability(net_monthly_income=0, equity=0, annual_rate=0.03,
                      initial_repayment=0.02, bundesland="NI")
    with pytest.raises(ValueError):
        affordability(net_monthly_income=4_000, equity=0, annual_rate=0.03,
                      initial_repayment=0.0, bundesland="NI")
    with pytest.raises(ValueError, match="no payment budget"):
        affordability(net_monthly_income=1_000, equity=0, annual_rate=0.03,
                      initial_repayment=0.02, bundesland="NI",
                      max_rate_to_net_income=0.35, existing_obligations=1_000)
