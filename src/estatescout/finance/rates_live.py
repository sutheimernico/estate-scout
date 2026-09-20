"""Current German mortgage rate from the Bundesbank — live, keyless, with an honest fallback.

Source: Bundesbank SDMX REST API (``api.statistiken.bundesbank.de``), no authentication and no
registration. Dataflow ``BBIM1`` (MFI-Zinsstatistik), series key
``M.DE.B.A2C.A.R.A.2250.EUR.N`` — "Effektivzinssätze Banken DE / Neugeschäft / Wohnungsbaukredite
an private Haushalte insgesamt" (the old time-series id is SUD131Z). Verified 2026-09-20: the
narrow query answers in well under a second and returns ``% p.a.``.

Why this is *not* wired into the calculators as a silent default: ``finance/`` is the trust
anchor and must stay pure, deterministic and offline — a calculator whose result depends on a
network call cannot be hand-verified in a test. The live rate is offered as a *suggestion*
(API endpoint, assistant tool, UI prefill); the caller always passes the rate it actually wants.

On any failure the static value from ``config/rates.yaml`` is returned instead, and ``origin``
plus ``source`` say so plainly — a stale number is never passed off as today's.
"""

import csv
import io
import json
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from .config import load_config

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE = _REPO_ROOT / "data" / "market_rate_cache.json"

BUNDESBANK_BASE = "https://api.statistiken.bundesbank.de/rest/data"
BUNDESBANK_FLOW = "BBIM1"  # MFI-Zinsstatistik
BUNDESBANK_SERIES = "M.DE.B.A2C.A.R.A.2250.EUR.N"  # housing loans to households, new business
BUNDESBANK_URL = f"{BUNDESBANK_BASE}/{BUNDESBANK_FLOW}/{BUNDESBANK_SERIES}?lastNObservations=1"

CACHE_TTL_SECONDS = 24 * 60 * 60

ORIGIN_LIVE = "bundesbank_live"
ORIGIN_CACHE = "bundesbank_cache"
ORIGIN_FALLBACK = "static_fallback"


@dataclass(frozen=True)
class MarketRate:
    annual_rate_percent: float
    source: str  # human-readable provenance, always present
    as_of: str  # the observation period (live) or the config date (fallback)
    origin: str  # ORIGIN_LIVE | ORIGIN_CACHE | ORIGIN_FALLBACK


def _parse_sdmx_csv(text: str) -> tuple[float, str, str]:
    """Return (rate percent, period, series title) from the Bundesbank CSV response."""
    rows = list(csv.DictReader(io.StringIO(text), delimiter=";"))
    if not rows:
        raise ValueError("Bundesbank response contained no observations")
    row = rows[-1]  # lastNObservations=1, but take the newest defensively
    return float(row["OBS_VALUE"]), row["TIME_PERIOD"], (row.get("BBK_TITLE") or "").strip()


def _static_fallback(config: dict | None = None) -> MarketRate:
    block = (config or load_config())["market_rate"]
    return MarketRate(
        annual_rate_percent=float(block["fallback_annual_rate_percent"]),
        source=f"static fallback — config/rates.yaml ({block['source']})",
        as_of=str(block["as_of"]),
        origin=ORIGIN_FALLBACK,
    )


def _read_cache(path: Path, ttl: float) -> MarketRate | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(payload["fetched_at"]) > ttl:
            return None
        return MarketRate(
            annual_rate_percent=float(payload["annual_rate_percent"]),
            source=str(payload["source"]),
            as_of=str(payload["as_of"]),
            origin=ORIGIN_CACHE,
        )
    except (OSError, KeyError, ValueError, TypeError):
        return None  # missing or corrupt cache → refetch


def _write_cache(path: Path, rate: MarketRate) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "annual_rate_percent": rate.annual_rate_percent,
                    "source": rate.source,
                    "as_of": rate.as_of,
                    "fetched_at": time.time(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass  # an unwritable cache must never break a request


def market_rate(
    *,
    client: httpx.Client | None = None,
    cache_path: Path | str = DEFAULT_CACHE,
    ttl_seconds: float = CACHE_TTL_SECONDS,
    timeout: float = 15.0,
    config: dict | None = None,
) -> MarketRate:
    """Current effective mortgage rate for new business, live or honestly labelled as not."""
    path = Path(cache_path)
    cached = _read_cache(path, ttl_seconds)
    if cached is not None:
        return cached

    http = client or httpx.Client(timeout=timeout)
    try:
        response = http.get(BUNDESBANK_URL, headers={"Accept": "text/csv"})
        response.raise_for_status()
        value, period, title = _parse_sdmx_csv(response.text)
    except (httpx.HTTPError, ValueError, KeyError):
        return _static_fallback(config)
    finally:
        if client is None:
            http.close()

    rate = MarketRate(
        annual_rate_percent=value,
        source=(
            f"Deutsche Bundesbank, {BUNDESBANK_FLOW}/{BUNDESBANK_SERIES}"
            + (f" — {title}" if title else "")
        ),
        as_of=period,
        origin=ORIGIN_LIVE,
    )
    _write_cache(path, rate)
    return rate
