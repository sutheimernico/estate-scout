"""Code-level check that numbers quoted in the model's prose come from a tool result.

The system prompt asks the model to repeat tool figures exactly, but prompt rules do not bind
free text: a live run turned 181,209.86 into "181.210,86". This module compares every number in
the answer with the tool results, the numbers the user gave and the knowledge excerpts the
model was shown, so the UI can flag a figure the code did not produce. It never rewrites the
answer — it only reports.

Matching rules, deliberately strict:

- A prose number must equal a source value at the precision the prose shows.
- Percent and fraction are only converted where the *key name* says so (``..._percent`` holds a
  percent, ``..._rate`` / ``..._quota`` / ``..._yield`` holds a fraction). An arbitrary value is
  never accepted as "that times 100".
- Sign: a prose number with an explicit minus must match a negative source value, an explicit
  plus a positive one. Unsigned prose ("Verlust von 5.520 €") matches by magnitude, because
  German prose usually carries the sign in the wording.
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


def _signed_numbers(text: str) -> list[tuple[str, float, int, int]]:
    """(token, value, decimals, sign) per number; sign is -1/+1 if written, else 0."""
    out = []
    for m in _NUMBER.finditer(text):
        parsed = _parse(m.group())
        if parsed is None:
            continue
        sign = 0
        prev = text[m.start() - 1] if m.start() > 0 else ""
        before = text[m.start() - 2] if m.start() > 1 else ""
        if prev in "-−–" and prev and not (before.isalnum()):
            sign = -1
        elif prev == "+" and not before.isalnum():
            sign = 1
        out.append((m.group(), parsed[0], parsed[1], sign))
    return out


def numbers_in_text(text: str) -> list[tuple[str, float, int]]:
    """Every parseable number in ``text`` as (token, value, decimals shown)."""
    return [(token, value, decimals) for token, value, decimals, _ in _signed_numbers(text)]


# Key-name hints for the unit of a numeric source value (see module docstring).
_PERCENT_KEY = re.compile(r"(_percent|_pct)$")
_FRACTION_KEY = re.compile(r"(rate|quota|yield|ratio|share|fraction)$")


def _walk(obj: object, key: str = "") -> Iterable[tuple[str, float]]:
    """Yield (nearest dict key, value) for every number inside ``obj``."""
    if isinstance(obj, bool):
        return
    if isinstance(obj, int | float):
        yield key, float(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, str(k))
    elif isinstance(obj, list | tuple):
        for v in obj:
            yield from _walk(v, key)


def _variants(key: str, value: float) -> list[float]:
    """The value plus its percent/fraction twin — only where the key's unit says so."""
    out = [value]
    if _FRACTION_KEY.search(key) and not _PERCENT_KEY.search(key) and abs(value) <= 1:
        out.append(value * 100.0)  # fraction -> percent
    elif _PERCENT_KEY.search(key):
        out.append(value / 100.0)  # percent -> fraction
    return out


def _trivial(token: str, value: float) -> bool:
    """Bare small integers (counts, months, list numbers) and calendar years are not checked."""
    bare = token.isdigit()
    return bare and (value < 10 or 1900 <= value <= 2100)


def _matches(value: float, sign: int, tolerance: float, candidates: list[float]) -> bool:
    """Does a prose number agree with any source value? Sign only counts when it was written."""
    if sign == 0:
        return any(abs(value - abs(c)) <= tolerance for c in candidates)
    return any(abs(sign * value - c) <= tolerance for c in candidates)


def unverified_numbers(
    answer: str,
    tool_calls: list[dict],
    question: str = "",
    context: Iterable[str] = (),
) -> list[str]:
    """Numbers in ``answer`` that match no tool result, tool argument, question or excerpt.

    A prose number matches a source value when they agree to the precision the prose shows
    (so "181.210" matches 181209.86 but "181.210,86" does not). ``context`` is the text of the
    knowledge excerpts the model was given: a knowledge answer may quote figures from them, and
    nothing else. See the module docstring for the unit and sign rules.
    """
    allowed: list[float] = []
    for call in tool_calls:
        for source in (call.get("result"), call.get("args")):
            for key, v in _walk(source):
                allowed.extend(_variants(key, v))
    # numbers the user or the knowledge base wrote are plain text: any sign, no unit twins
    plain = [value for _, value, _ in numbers_in_text(question)]
    for excerpt in context:
        plain.extend(value for _, value, _ in numbers_in_text(excerpt))

    flagged: list[str] = []
    for token, value, decimals, sign in _signed_numbers(answer):
        if _trivial(token, value):
            continue
        tolerance = 0.5 * 10 ** (-decimals) + 1e-9

        # text sources carry no reliable sign semantics, so they match by magnitude only
        in_text = any(abs(value - abs(c)) <= tolerance for c in plain)
        if not (_matches(value, sign, tolerance, allowed) or in_text) and token not in flagged:
            flagged.append(token)
    return flagged
