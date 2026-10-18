"""Code-level check that numbers quoted in the model's prose come from a tool result.

The system prompt asks the model to repeat tool figures exactly, but prompt rules do not bind
free text: a live run turned 181,209.86 into "181.210,86". This module compares every number in
the answer with the tool results (and with the numbers the user gave), so the UI can flag a
figure the code did not produce. It never rewrites the answer — it only reports.
"""

import re
from collections.abc import Iterable

# Digits with optional '.', ',' or (narrow) no-break space group/decimal separators.
_NUMBER = re.compile(r"\d(?:[\d.,  ]*\d)?")
_THOUSANDS_DOT = re.compile(r"^\d{1,3}(\.\d{3})+$")
_THOUSANDS_COMMA = re.compile(r"^\d{1,3}(,\d{3})+$")


def _parse(token: str) -> tuple[float, int] | None:
    """Return (value, decimals shown) for a German-style number token, or None."""
    t = token.replace(" ", "").replace(" ", "")
    if "." in t and "," in t:
        # The separator that comes last is the decimal mark (German "1.234,56", English "1,234.56").
        dec = "," if t.rfind(",") > t.rfind(".") else "."
        grp = "." if dec == "," else ","
        whole, _, frac = t.rpartition(dec)
        whole = whole.replace(grp, "")
    elif "," in t:
        if _THOUSANDS_COMMA.match(t):
            whole, frac = t.replace(",", ""), ""
        else:
            whole, _, frac = t.rpartition(",")
    elif "." in t:
        if _THOUSANDS_DOT.match(t):
            whole, frac = t.replace(".", ""), ""
        else:
            whole, _, frac = t.rpartition(".")
    else:
        whole, frac = t, ""
    if not whole.isdigit() or (frac and not frac.isdigit()):
        return None
    return float(f"{whole}.{frac or '0'}"), len(frac)


def numbers_in_text(text: str) -> list[tuple[str, float, int]]:
    """Every parseable number in ``text`` as (token, value, decimals shown)."""
    out = []
    for m in _NUMBER.finditer(text):
        parsed = _parse(m.group())
        if parsed is not None:
            out.append((m.group(), parsed[0], parsed[1]))
    return out


def _walk(obj: object) -> Iterable[float]:
    if isinstance(obj, bool):
        return
    if isinstance(obj, int | float):
        yield float(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list | tuple):
        for v in obj:
            yield from _walk(v)


def _trivial(token: str, value: float) -> bool:
    """Bare small integers (counts, months, list numbers) and calendar years are not checked."""
    bare = token.isdigit()
    return bare and (value < 10 or 1900 <= value <= 2100)


def unverified_numbers(
    answer: str, tool_calls: list[dict], question: str = ""
) -> list[str]:
    """Numbers in ``answer`` that match no tool result, tool argument or number in the question.

    A prose number matches a source value when they agree to the precision the prose shows
    (so "181.210" matches 181209.86 but "181.210,86" does not). Fractions are also compared
    as percentages, because tools return 0.036 where the prose says "3,6 %".
    """
    if not tool_calls:
        return []  # nothing to compare against; knowledge answers cite documents instead
    allowed: set[float] = set()
    for call in tool_calls:
        for source in (call.get("result"), call.get("args")):
            for v in _walk(source):
                allowed.update((v, v * 100.0))
    allowed.update(value for _, value, _ in numbers_in_text(question))

    flagged: list[str] = []
    for token, value, decimals in numbers_in_text(answer):
        if _trivial(token, value):
            continue
        tolerance = 0.5 * 10 ** (-decimals) + 1e-9
        if not any(abs(value - a) <= tolerance for a in allowed) and token not in flagged:
            flagged.append(token)
    return flagged
