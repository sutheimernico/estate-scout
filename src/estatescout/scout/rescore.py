"""Re-enrich and re-score every saved object, then write a digest of what changed.

The previous run's snapshots live in a small JSON state file next to the database, so no schema
change is needed. Scoring here has no rent (the table-view convention), so yield never enters.
"""

import json
from pathlib import Path

from .digest import diff_snapshots, render_digest, snapshot
from .enrich import BodenrichtwertProvider, RegionSignalProvider, enrich
from .scoring import score_listing
from .store import ListingStore


def rescore(
    store: ListingStore,
    *,
    bodenrichtwert: BodenrichtwertProvider | None,
    region: RegionSignalProvider | None,
    state_path: Path,
    digest_dir: Path,
    today: str,
) -> Path:
    """Update stored enrichments, write ``digest_dir/<today>.md`` and refresh the state file."""
    previous: dict[str, dict] = {}
    if state_path.exists():
        previous = json.loads(state_path.read_text(encoding="utf-8"))

    current: dict[str, dict] = {}
    for listing in store.list():
        result = enrich(listing, bodenrichtwert=bodenrichtwert, region=region)
        store.set_enrichment(listing.id, result)
        current[str(listing.id)] = snapshot(listing, result, score_listing(listing, result))

    digest_dir.mkdir(parents=True, exist_ok=True)
    out = digest_dir / f"{today}.md"
    out.write_text(render_digest(today, diff_snapshots(previous, current)), encoding="utf-8")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
