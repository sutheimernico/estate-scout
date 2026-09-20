"""Tests for the LLM-facing finance tool layer (schemas + dispatcher)."""

import pytest

from estatescout.assistant.tools import TOOLS, dispatch, tool_specs


def test_tool_specs_cover_all_calculators():
    specs = tool_specs()
    names = {s["function"]["name"] for s in specs}
    assert names == {
        "annuity", "purchase_costs", "affordability", "yield_metrics",
        "operating_costs", "equity_return",
    }
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


def test_dispatch_coerces_numeric_strings():
    out = dispatch(
        "annuity",
        {"principal": "300000", "annual_rate_percent": "3.6", "initial_repayment_percent": 2.0},
    )
    assert out["monthly_payment"] == pytest.approx(1_400.0)


def test_dispatch_rejects_non_numeric_string():
    with pytest.raises(ValueError, match="must be a number"):
        dispatch(
            "annuity",
            {"principal": "dreihundert", "annual_rate_percent": 3.6,
             "initial_repayment_percent": 2.0},
        )


def test_dispatch_rejects_bool_for_number():
    with pytest.raises(ValueError, match="must be a number"):
        dispatch(
            "annuity",
            {"principal": True, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0},
        )


def test_dispatch_rejects_number_for_string():
    with pytest.raises(ValueError, match="must be a string"):
        dispatch("purchase_costs", {"purchase_price": 300_000, "bundesland": 42})


def test_dispatch_treats_explicit_null_as_absent():
    out = dispatch(
        "annuity",
        {"principal": 300_000, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0,
         "annual_sondertilgung": None},
    )
    assert out["monthly_payment"] == pytest.approx(1_400.0)


def test_dispatch_null_required_arg_counts_as_missing():
    with pytest.raises(ValueError, match="missing required"):
        dispatch(
            "annuity",
            {"principal": None, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0},
        )


def test_dispatch_operating_costs():
    out = dispatch("operating_costs", {"living_area_sqm": 100, "monthly_cold_rent": 1_000})
    assert out["total_annual"] == pytest.approx(1_790.0)


def test_dispatch_equity_return_converts_percent():
    out = dispatch(
        "equity_return",
        {"purchase_price": 300_000, "monthly_cold_rent": 1_500, "equity": 60_000,
         "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0,
         "ancillary_costs": 30_000, "annual_operating_costs": 2_400},
    )
    assert out["cashflow_before_tax"] == pytest.approx(480.0)
    assert out["cash_on_cash_percent"] == pytest.approx(0.8)
