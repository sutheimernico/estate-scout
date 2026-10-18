#!/usr/bin/env python
"""Re-enrich and re-score all saved objects and write data/digests/<date>.md.

Run: uv run python scripts/nightly_rescore.py
Scheduling is the owner's call - see deploy/ for ready-made systemd user units (not installed).
"""

from datetime import date

from estatescout.scout.enrich import configured_providers
from estatescout.scout.rescore import rescore
from estatescout.scout.store import DEFAULT_DB, ListingStore

if __name__ == "__main__":
    data_dir = DEFAULT_DB.parent
    store = ListingStore(DEFAULT_DB)
    try:
        bodenrichtwert, region = configured_providers()
        out = rescore(
            store,
            bodenrichtwert=bodenrichtwert,
            region=region,
            state_path=data_dir / "score_state.json",
            digest_dir=data_dir / "digests",
            today=date.today().isoformat(),
        )
    finally:
        store.close()
    print(f"Digest geschrieben: {out}")
