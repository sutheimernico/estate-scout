"""The prose-number guard: numbers the model quotes must trace back to tool results."""

import pytest

from estatescout.assistant.number_check import numbers_in_text, unverified_numbers

CALL = {
    "name": "annuity",
    "args": {"principal": 300_000, "annual_rate_percent": 3.6},
    "result": {"monthly_payment": 1400.0, "remaining_debt": 181209.86, "annual_rate": 0.036},
}


@pytest.mark.parametrize(
    "text,expected",
    [
        ("181.209,86 €", [(181209.86, 2)]),
        ("181,209.86", [(181209.86, 2)]),
        ("1.400 €", [(1400.0, 0)]),
        ("3,6 %", [(3.6, 1)]),
        ("300.000 und 2,5", [(300000.0, 0), (2.5, 1)]),
    ],
)
def test_parses_german_and_english_formats(text, expected):
    assert [(v, d) for _, v, d in numbers_in_text(text)] == expected


def test_exact_tool_figures_pass():
    answer = "Rate 1.400,00 €, Restschuld 181.209,86 € bei 3,6 % Zins."
    assert unverified_numbers(answer, [CALL]) == []


def test_rounded_figure_passes_at_its_own_precision():
    assert unverified_numbers("Restschuld rund 181.210 €", [CALL]) == []


def test_the_live_garble_is_caught():
    # live finding: 181,209.86 was quoted as "181.210,86"
    assert unverified_numbers("Restschuld: 181.210,86 €", [CALL]) == ["181.210,86"]


def test_model_arithmetic_is_caught():
    assert unverified_numbers("Das sind 16.800 € im Jahr.", [CALL]) == ["16.800"]


def test_numbers_from_the_question_are_allowed():
    assert unverified_numbers("Bei 250.000 € Preis ...", [CALL], question="250.000 € Haus") == []


def test_no_tool_calls_means_nothing_to_check():
    assert unverified_numbers("Die Grunderwerbsteuer beträgt 5 %.", []) == []


def test_small_counts_and_years_are_ignored():
    assert unverified_numbers("Es gibt 3 Optionen, Stand 2026.", [CALL]) == []


def test_unparseable_tokens_do_not_crash():
    unverified_numbers("Version 1.2.3 und 1,2,3 und 1..2", [CALL])  # must simply not raise
