"""Load and query the versioned financial reference config (``config/rates.yaml``).

Values age, so each block carries ``source`` + ``as_of``. Lookups error loudly on unknown
keys rather than assuming a default — a missing fact must never be silently invented.
"""

from functools import lru_cache
from pathlib import Path

import yaml

_DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "rates.yaml"


@lru_cache(maxsize=8)
def load_config(path: str | None = None) -> dict:
    """Parse ``config/rates.yaml`` (or an explicit path). Cached per path."""
    p = Path(path) if path else _DEFAULT_CONFIG
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"config at {p} is not a mapping")
    return data


def normalize_bundesland(bundesland: str, *, config: dict | None = None) -> str:
    """Resolve a Bundesland code or common name to its canonical two-letter code.

    Accepts codes (``NI``, ``NW``) and names (``Niedersachsen``, ``NRW``), case-insensitively.
    Raises ``ValueError`` for an unknown Bundesland.
    """
    cfg = config or load_config()
    block = cfg["grunderwerbsteuer"]
    rates: dict = block["rates"]
    aliases: dict = block.get("aliases", {})

    key = bundesland.strip().upper()
    key = aliases.get(key, key)
    if key not in rates:
        known = ", ".join(sorted(rates))
        raise ValueError(f"unknown Bundesland '{bundesland}' (known codes: {known})")
    return key


def grunderwerbsteuer_rate(bundesland: str, *, config: dict | None = None) -> float:
    """Grunderwerbsteuer rate (fraction) for a Bundesland by code or full name."""
    cfg = config or load_config()
    code = normalize_bundesland(bundesland, config=cfg)
    return float(cfg["grunderwerbsteuer"]["rates"][code])
