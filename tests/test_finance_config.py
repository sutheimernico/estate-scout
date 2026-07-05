"""Tests for the versioned reference-config loader."""

import pytest

from estatescout.finance.config import grunderwerbsteuer_rate, load_config


def test_config_loads_with_expected_blocks():
    cfg = load_config()
    for block in ("grunderwerbsteuer", "notary_and_land_registry", "makler", "affordability"):
        assert block in cfg
    assert cfg["grunderwerbsteuer"]["as_of"]
    assert cfg["grunderwerbsteuer"]["source"]


def test_focus_region_rates():
    assert grunderwerbsteuer_rate("NI") == pytest.approx(0.050)
    assert grunderwerbsteuer_rate("NW") == pytest.approx(0.065)


def test_lookup_by_full_name_and_alias_case_insensitive():
    assert grunderwerbsteuer_rate("Niedersachsen") == pytest.approx(0.050)
    assert grunderwerbsteuer_rate("nrw") == pytest.approx(0.065)
    assert grunderwerbsteuer_rate("Nordrhein-Westfalen") == pytest.approx(0.065)


def test_unknown_bundesland_raises():
    with pytest.raises(ValueError, match="unknown Bundesland"):
        grunderwerbsteuer_rate("Atlantis")


def test_missing_config_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/rates.yaml")
