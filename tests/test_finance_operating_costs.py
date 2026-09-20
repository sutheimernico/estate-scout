"""Tests for the config-anchored Bewirtschaftungskosten estimator."""

import pytest

from estatescout.finance.operating_costs import operating_costs


def test_worked_example_100sqm_1000eur_rent():
    # 100 m² × 12 €/m²/a = 1200; 1 unit × 350 €/a = 350; 12_000 € rent × 2 % = 240
    res = operating_costs(100.0, 1_000.0)
    assert res.instandhaltung == pytest.approx(1_200.0)
    assert res.verwaltung == pytest.approx(350.0)
    assert res.mietausfallwagnis == pytest.approx(240.0)
    assert res.total_annual == pytest.approx(1_790.0)


def test_units_scale_the_management_fee():
    res = operating_costs(200.0, 2_000.0, units=3)
    assert res.verwaltung == pytest.approx(1_050.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        operating_costs(0, 1_000.0)
    with pytest.raises(ValueError):
        operating_costs(100.0, 0)
    with pytest.raises(ValueError):
        operating_costs(100.0, 1_000.0, units=0)
