"""Tests for the rental-yield metrics. Reference: 300_000 EUR, 1_000 EUR/mo cold rent."""

import pytest

from estatescout.finance.yield_metrics import yield_metrics


def test_gross_yield_and_kaufpreisfaktor():
    m = yield_metrics(300_000, 1_000)
    assert m.annual_cold_rent == pytest.approx(12_000.0)
    assert m.gross_yield == pytest.approx(0.04)  # 12_000 / 300_000
    assert m.kaufpreisfaktor == pytest.approx(25.0)  # 300_000 / 12_000


def test_gross_yield_is_reciprocal_of_kaufpreisfaktor():
    m = yield_metrics(415_000, 1_375)
    assert m.gross_yield == pytest.approx(1.0 / m.kaufpreisfaktor)


def test_net_yield_accounts_for_costs():
    m = yield_metrics(300_000, 1_000, annual_operating_costs=2_000, ancillary_costs=30_000)
    # (12_000 - 2_000) / (300_000 + 30_000) = 10_000 / 330_000
    assert m.net_yield == pytest.approx(10_000.0 / 330_000.0)
    assert m.net_yield < m.gross_yield


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        yield_metrics(0, 1_000)
    with pytest.raises(ValueError):
        yield_metrics(300_000, 0)
    with pytest.raises(ValueError):
        yield_metrics(300_000, 1_000, annual_operating_costs=-1)
