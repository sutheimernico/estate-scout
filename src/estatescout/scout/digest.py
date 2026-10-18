"""Re-score digest: what changed in the saved objects' scores since the last run.

Pure logic only (snapshot, diff, render) so it is testable without network or clock; the
runner in ``scripts/nightly_rescore.py`` does the I/O. A snapshot records the score *and* the
raw inputs behind it, so a delta can name the input that moved ("Bodenrichtwert 190 -> 210").
"""

from dataclasses import dataclass

from .enrich import Enrichment
from .model import Listing
from .scoring import ScoreReport

_INPUT_LABELS = {
    "bodenrichtwert": "Bodenrichtwert (€/m²)",
    "population_trend_pct": "Bevölkerungstrend (%)",
    "vacancy_rate_pct": "Leerstand (%)",
}


def snapshot(listing: Listing, enrichment: Enrichment, report: ScoreReport) -> dict:
    """JSON-ready record of one listing's score and the inputs it came from."""
    region = enrichment.region
    return {
        "label": ", ".join(p for p in (listing.ort, listing.plz) if p) or f"Objekt {listing.id}",
        "total": report.total,
        "inputs": {
            "bodenrichtwert": enrichment.bodenrichtwert_eur_per_sqm,
            "population_trend_pct": region.population_trend_pct if region else None,
            "vacancy_rate_pct": region.vacancy_rate_pct if region else None,
        },
    }


@dataclass(frozen=True)
class Delta:
    listing_id: str
    label: str
    old_total: int | None
    new_total: int | None
    changed_inputs: tuple[tuple[str, float | None, float | None], ...]  # (name, old, new)


def diff_snapshots(previous: dict[str, dict], current: dict[str, dict]) -> list[Delta]:
    """Deltas for every object whose score or inputs changed.

    Objects missing from ``previous`` are new (no old score); objects only in ``previous`` were
    deleted and are not reported.
    """
    deltas = []
    for listing_id, cur in current.items():
        prev = previous.get(listing_id)
        old_inputs = prev["inputs"] if prev else {}
        changed = tuple(
            (name, old_inputs.get(name), new)
            for name, new in cur["inputs"].items()
            if prev is not None and old_inputs.get(name) != new
        )
        old_total = prev["total"] if prev else None
        if prev is None or old_total != cur["total"] or changed:
            deltas.append(
                Delta(listing_id, cur["label"], old_total, cur["total"], changed)
            )
    return deltas


def _num(value: float | None) -> str:
    return "–" if value is None else f"{value:g}".replace(".", ",")


def _score(value: int | None) -> str:
    return "–" if value is None else str(value)


def render_digest(date: str, deltas: list[Delta]) -> str:
    """German Markdown digest for one run."""
    lines = [f"# Score-Digest {date}", ""]
    if not deltas:
        lines.append("Keine Änderungen seit dem letzten Lauf.")
        return "\n".join(lines) + "\n"
    for d in deltas:
        head = f"- **{d.label}** (Objekt {d.listing_id}): "
        if d.old_total is None:
            head += f"neu, Score {_score(d.new_total)}"
        else:
            head += f"Score {_score(d.old_total)} → {_score(d.new_total)}"
        if d.changed_inputs:
            parts = [
                f"{_INPUT_LABELS.get(n, n)} {_num(old)} → {_num(new)}"
                for n, old, new in d.changed_inputs
            ]
            head += " (" + "; ".join(parts) + ")"
        lines.append(head)
    return "\n".join(lines) + "\n"
