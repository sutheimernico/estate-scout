"""Tests for the first-year Eigenkapitalrendite (cash-on-cash) calculator."""

import pytest

from estatescout.finance.equity_return import equity_return


def test_worked_example_positive_cashflow():
    # loan = 300k + 30k − 60k = 270k; debt service = 270k × 5.6 % = 15_120
    # NOI = 1_500 × 12 − 2_400 = 15_600; CF = 480; CoC = 480 / 60_000 = 0.8 %
    res = equity_return(
        300_000, 1_500.0, 60_000, 0.036, 0.02,
        ancillary_costs=30_000, annual_operating_costs=2_400,
    )
    assert res.loan == pytest.approx(270_000.0)
    assert res.annual_debt_service == pytest.approx(15_120.0)
    assert res.net_operating_income == pytest.approx(15_600.0)
    assert res.cashflow_before_tax == pytest.approx(480.0)
    assert res.cash_on_cash == pytest.approx(0.008)


def test_negative_cashflow_yields_negative_return():
    # same object, weaker rent: NOI = 12_000 − 2_400 = 9_600; CF = −5_520
    res = equity_return(
        300_000, 1_000.0, 60_000, 0.036, 0.02,
        ancillary_costs=30_000, annual_operating_costs=2_400,
    )
    assert res.cashflow_before_tax == pytest.approx(-5_520.0)
    assert res.cash_on_cash < 0


def test_full_equity_purchase_has_no_debt_service():
    res = equity_return(100_000, 500.0, 110_000, 0.036, 0.02, ancillary_costs=10_000)
    assert res.loan == pytest.approx(0.0)
    assert res.annual_debt_service == pytest.approx(0.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        equity_return(100_000, 500.0, 0, 0.036, 0.02)  # no equity
    with pytest.raises(ValueError):
        equity_return(100_000, 500.0, 200_000, 0.036, 0.02)  # equity > investment
    with pytest.raises(ValueError, match="looks like percent"):
        equity_return(100_000, 500.0, 20_000, 3.6, 0.02)
