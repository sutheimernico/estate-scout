"""Tests for the CLI: deterministic finance commands + the response renderer."""

import json

from typer.testing import CliRunner

from estatescout.assistant.assistant import DISCLAIMER, AssistantResponse
from estatescout.cli import finance_app, render_response

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
