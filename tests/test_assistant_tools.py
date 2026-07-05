"""Tests for the LLM-facing finance tool layer (schemas + dispatcher)."""

import pytest

from estatescout.assistant.tools import TOOLS, dispatch, tool_specs


def test_tool_specs_cover_all_calculators():
    specs = tool_specs()
    names = {s["function"]["name"] for s in specs}
    assert names == {"annuity", "purchase_costs", "affordability", "yield_metrics"}
    for s in specs:
        assert s["type"] == "function"
        assert "required" in s["function"]["parameters"]


def test_dispatch_annuity_converts_percent_to_fraction():
    out = dispatch(
        "annuity",
        {"principal": 300_000, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0},
    )
    assert out["monthly_payment"] == pytest.approx(1_400.0)  # 300_000 * 0.056 / 12
    assert out["remaining_debt_by_year"][0]["year"] == 1


def test_dispatch_purchase_costs():
    out = dispatch("purchase_costs", {"purchase_price": 300_000, "bundesland": "NI"})
    assert out["grunderwerbsteuer"] == pytest.approx(15_000.0)
    assert out["ancillary_quota_percent"] == pytest.approx(10.57)


def test_dispatch_affordability_worked_example():
    out = dispatch(
        "affordability",
        {
            "net_monthly_income": 4_000,
            "equity": 60_000,
            "annual_rate_percent": 3.6,
            "initial_repayment_percent": 2.0,
            "bundesland": "NI",
        },
    )
    assert out["max_monthly_payment"] == pytest.approx(1_400.0)
    assert out["max_loan"] == pytest.approx(300_000.0)


def test_dispatch_yield():
    out = dispatch(
        "yield_metrics", {"purchase_price": 300_000, "monthly_cold_rent": 1_000}
    )
    assert out["gross_yield_percent"] == pytest.approx(4.0)
    assert out["kaufpreisfaktor"] == pytest.approx(25.0)


def test_dispatch_unknown_tool_raises():
    with pytest.raises(ValueError, match="unknown tool"):
        dispatch("does_not_exist", {})


def test_dispatch_missing_required_arg_raises():
    with pytest.raises(ValueError, match="missing required"):
        dispatch("annuity", {"principal": 300_000})


def test_every_tool_has_a_runner():
    assert all(callable(t.run) for t in TOOLS.values())
