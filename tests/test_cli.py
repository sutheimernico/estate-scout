"""Tests for the CLI: deterministic finance commands + the response renderer."""

import json

import pytest
from typer.testing import CliRunner

from estatescout.assistant.assistant import DISCLAIMER, AssistantResponse
from estatescout.cli import finance_app, render_response, scout_app

runner = CliRunner()


def _run(args: list[str]) -> dict:
    result = runner.invoke(finance_app, args)
    assert result.exit_code == 0, result.stdout
    return json.loads(result.stdout)


def test_cli_annuity():
    out = _run(["annuity", "--principal", "300000", "--rate", "3.6", "--repayment", "2.0"])
    assert out["monthly_payment"] == 1_400.0


def test_cli_costs_by_bundesland():
    out = _run(["costs", "--price", "300000", "--bundesland", "NRW"])
    assert out["grunderwerbsteuer"] == 19_500.0


def test_cli_afford():
    out = _run(
        [
            "afford", "--income", "4000", "--equity", "60000",
            "--rate", "3.6", "--repayment", "2.0", "--bundesland", "NI",
        ]
    )
    assert out["max_loan"] == 300_000.0


def test_cli_yield():
    out = _run(["yield", "--price", "300000", "--rent", "1000"])
    assert out["gross_yield_percent"] == 4.0
    assert out["kaufpreisfaktor"] == 25.0


def test_cli_unknown_bundesland_errors():
    result = runner.invoke(finance_app, ["costs", "--price", "300000", "--bundesland", "Atlantis"])
    assert result.exit_code != 0


def test_scout_add_and_list(tmp_path):
    db = str(tmp_path / "t.db")
    r = runner.invoke(
        scout_app,
        ["add", "--price", "300000", "--area", "100", "--bundesland", "Niedersachsen",
         "--ort", "Osnabrück", "--db", db],
    )
    assert r.exit_code == 0, r.stdout
    added = json.loads(r.stdout)
    assert added["bundesland"] == "NI"
    assert added["price_per_sqm"] == 3_000.0
    r2 = runner.invoke(scout_app, ["list", "--db", db])
    assert r2.exit_code == 0
    items = json.loads(r2.stdout)
    assert len(items) == 1
    assert items[0]["ort"] == "Osnabrück"


def test_scout_add_invalid_bundesland_errors(tmp_path):
    r = runner.invoke(
        scout_app,
        ["add", "--price", "300000", "--area", "100", "--bundesland", "Atlantis",
         "--db", str(tmp_path / "t.db")],
    )
    assert r.exit_code != 0


def test_render_response_includes_answer_numbers_sources_disclaimer():
    resp = AssistantResponse(
        answer="Deine Rate liegt bei 1.400 €.",
        tool_calls=[{"name": "annuity", "args": {}, "result": {"monthly_payment": 1_400.0}}],
        sources=["03-finanzierung.md"],
    )
    text = render_response(resp)
    assert "1.400" in text
    assert "annuity" in text
    assert "03-finanzierung.md" in text
    assert DISCLAIMER in text


def test_cli_opcosts():
    out = _run(["opcosts", "--area", "100", "--rent", "1000"])
    assert out["total_annual"] == pytest.approx(1_790.0)


def test_cli_equity_return():
    out = _run(
        ["equity", "--price", "300000", "--rent", "1500", "--equity", "60000",
         "--rate", "3.6", "--repayment", "2.0", "--ancillary", "30000",
         "--operating", "2400"]
    )
    assert out["cash_on_cash_percent"] == pytest.approx(0.8)


def test_scout_delete_removes_listing(tmp_path):
    db = str(tmp_path / "cli.db")
    add = runner.invoke(
        scout_app,
        ["add", "--price", "100000", "--area", "50", "--bundesland", "NI", "--db", db],
    )
    assert add.exit_code == 0, add.stdout
    listing_id = json.loads(add.stdout)["id"]
    assert runner.invoke(scout_app, ["delete", str(listing_id), "--db", db]).exit_code == 0
    assert runner.invoke(scout_app, ["delete", str(listing_id), "--db", db]).exit_code == 1
