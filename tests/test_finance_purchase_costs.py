"""Tests for the Kaufnebenkosten calculator. Reference values hand-computed on 300_000 EUR."""

import pytest

from estatescout.finance.purchase_costs import purchase_costs


def test_grunderwerbsteuer_differs_by_bundesland():
    ni = purchase_costs(300_000, "NI")
    nrw = purchase_costs(300_000, "NRW")
    assert ni.grunderwerbsteuer == pytest.approx(15_000.0)  # 300_000 * 0.050
    assert nrw.grunderwerbsteuer == pytest.approx(19_500.0)  # 300_000 * 0.065
    assert nrw.total_ancillary > ni.total_ancillary


def test_full_breakdown_ni_with_default_makler():
    c = purchase_costs(300_000, "Niedersachsen")
    assert c.notary == pytest.approx(4_500.0)  # 300_000 * 0.015
    assert c.land_registry == pytest.approx(1_500.0)  # 300_000 * 0.005
    assert c.makler == pytest.approx(10_710.0)  # 300_000 * 0.0357
    # 15_000 + 4_500 + 1_500 + 10_710 = 31_710
    assert c.total_ancillary == pytest.approx(31_710.0)
    assert c.total_investment == pytest.approx(331_710.0)
    assert c.ancillary_quota == pytest.approx(31_710.0 / 300_000)
    assert c.min_equity == pytest.approx(c.total_ancillary)


def test_makler_can_be_excluded():
    c = purchase_costs(300_000, "NI", makler_rate=0.0)
    assert c.makler == 0.0
    # 15_000 + 4_500 + 1_500 = 21_000
    assert c.total_ancillary == pytest.approx(21_000.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        purchase_costs(0, "NI")
    with pytest.raises(ValueError):
        purchase_costs(300_000, "NI", makler_rate=-0.01)
    with pytest.raises(ValueError, match="unknown Bundesland"):
        purchase_costs(300_000, "Atlantis")
