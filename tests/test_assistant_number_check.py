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


def test_knowledge_answers_are_checked_against_the_excerpts():
    excerpt = ["Die Grunderwerbsteuer in Niedersachsen beträgt 5,0 % des Kaufpreises."]
    assert unverified_numbers("Das sind 5,0 % in Niedersachsen.", [], context=excerpt) == []
    # 6,5 % is true for NRW but appears in no excerpt the model was shown
    assert unverified_numbers("Das sind 6,5 % in Niedersachsen.", [], context=excerpt) == ["6,5"]


def test_a_knowledge_answer_with_no_excerpts_may_not_invent_figures():
    assert unverified_numbers("Die Grunderwerbsteuer beträgt 6,5 %.", []) == ["6,5"]


def test_times_100_is_not_a_free_pass():
    # 1.400 must not make 140.000 acceptable
    assert unverified_numbers("Die Rate beträgt 140.000 €.", [CALL]) == ["140.000"]


def test_percent_fraction_conversion_follows_the_unit_in_the_key():
    call = {
        "name": "t",
        "args": {},
        "result": {"annual_rate": 0.036, "net_yield_percent": 4.2, "monthly_payment": 0.5},
    }
    assert unverified_numbers("Zins 3,6 %, Rendite 4,2 %.", [call]) == []
    # 0.5 is a payment, not a fraction: 50 has no source
    assert unverified_numbers("Rate 50 €.", [call]) == ["50"]
    # a percent field is not a fraction: 420 (= 4.2 × 100) is unsupported
    assert unverified_numbers("Rendite 420 %.", [call]) == ["420"]


NEGATIVE = {"name": "equity_return", "args": {}, "result": {"cashflow_before_tax": -5520.0}}


def test_an_explicit_minus_needs_a_negative_source():
    assert unverified_numbers("Der Cashflow beträgt −5.520 €.", [NEGATIVE]) == []
    assert unverified_numbers("Der Cashflow beträgt -5.520 €.", [NEGATIVE]) == []
    # the model flipped the sign of a positive figure
    positive = {"name": "x", "args": {}, "result": {"cashflow_before_tax": 5520.0}}
    assert unverified_numbers("Der Cashflow beträgt -5.520 €.", [positive]) == ["5.520"]
    assert unverified_numbers("Der Cashflow beträgt +5.520 €.", [NEGATIVE]) == ["5.520"]


def test_unsigned_prose_matches_by_magnitude():
    assert unverified_numbers("Ein Verlust von 5.520 € pro Jahr.", [NEGATIVE]) == []


def test_ranges_and_dates_are_not_read_as_signs():
    assert unverified_numbers("Zwischen 1.400 und 1.400-1.400 €", [CALL]) == []


def test_small_counts_and_years_are_ignored():
    assert unverified_numbers("Es gibt 3 Optionen, Stand 2026.", [CALL]) == []


def test_unparseable_tokens_do_not_crash():
    unverified_numbers("Version 1.2.3 und 1,2,3 und 1..2", [CALL])  # must simply not raise
