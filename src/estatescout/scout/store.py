"""SQLite persistence for listings — object attributes only (no seller contact data).

The store keeps a single connection (so ``:memory:`` works for tests) and is the seam the CLI/API
depend on; pass a file path for real use or ``:memory:`` / a temp path in tests.
"""

import json
import sqlite3
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from .enrich import Enrichment, from_dict, to_dict
from .model import Listing

# Default local DB (gitignored via *.db). CLI/API use this; tests pass :memory: or a temp path.
DEFAULT_DB = Path(__file__).resolve().parents[3] / "data" / "listings.db"

_COLUMNS = (
    "price",
    "living_area_sqm",
    "bundesland",
    "plz",
    "ort",
    "rooms",
    "year_built",
    "object_type",
    "features",
    "source_url",
)

# Bumped whenever the table shape changes; `_migrate` upgrades older files in place.
SCHEMA_VERSION = 1

_CREATE = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    price REAL NOT NULL,
    living_area_sqm REAL NOT NULL,
    bundesland TEXT NOT NULL,
    plz TEXT,
    ort TEXT,
    rooms REAL,
    year_built INTEGER,
    object_type TEXT,
    features TEXT,
    source_url TEXT,
    enrichment TEXT,
    enriched_at TEXT
)
"""


@dataclass(frozen=True)
class StoredEnrichment:
    enrichment: Enrichment
    enriched_at: str  # ISO-8601 UTC


def _migrate(conn: sqlite3.Connection) -> None:
    """Bring an existing file up to SCHEMA_VERSION. No-op for a freshly created table."""
    if conn.execute("PRAGMA user_version").fetchone()[0] >= SCHEMA_VERSION:
        return
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(listings)")}
    for column in ("enrichment", "enriched_at"):
        if column not in existing:
            conn.execute(f"ALTER TABLE listings ADD COLUMN {column} TEXT")
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _row_to_listing(row: sqlite3.Row) -> Listing:
    return Listing(
        price=row["price"],
        living_area_sqm=row["living_area_sqm"],
        bundesland=row["bundesland"],
        plz=row["plz"] or "",
        ort=row["ort"] or "",
        rooms=row["rooms"],
        year_built=row["year_built"],
        object_type=row["object_type"] or "wohnung",
        features=tuple(json.loads(row["features"] or "[]")),
        source_url=row["source_url"] or "",
        id=row["id"],
    )


class ListingStore:
    def __init__(self, path: str | Path = ":memory:"):
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_CREATE)
        _migrate(self._conn)
        self._conn.commit()

    def add(self, listing: Listing) -> Listing:
        placeholders = ", ".join("?" for _ in _COLUMNS)
        values = (
            listing.price,
            listing.living_area_sqm,
            listing.bundesland,
            listing.plz,
            listing.ort,
            listing.rooms,
            listing.year_built,
            listing.object_type,
            json.dumps(list(listing.features)),
            listing.source_url,
        )
        cur = self._conn.execute(
            f"INSERT INTO listings ({', '.join(_COLUMNS)}) VALUES ({placeholders})", values
        )
        self._conn.commit()
        return replace(listing, id=cur.lastrowid)

    def get(self, listing_id: int) -> Listing | None:
        row = self._conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
        return _row_to_listing(row) if row else None

    def list(self) -> list[Listing]:
        rows = self._conn.execute("SELECT * FROM listings ORDER BY id").fetchall()
        return [_row_to_listing(r) for r in rows]

    def delete(self, listing_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def schema_version(self) -> int:
        return int(self._conn.execute("PRAGMA user_version").fetchone()[0])

    def set_enrichment(self, listing_id: int, enrichment: Enrichment) -> bool:
        """Store (or replace) the enrichment of a listing. False if the id is unknown."""
        cur = self._conn.execute(
            "UPDATE listings SET enrichment = ?, enriched_at = ? WHERE id = ?",
            (
                json.dumps(to_dict(enrichment), ensure_ascii=False),
                datetime.now(UTC).isoformat(timespec="seconds"),
                listing_id,
            ),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def get_enrichment(self, listing_id: int) -> StoredEnrichment | None:
        row = self._conn.execute(
            "SELECT enrichment, enriched_at FROM listings WHERE id = ?", (listing_id,)
        ).fetchone()
        if row is None or not row["enrichment"]:
            return None
        return StoredEnrichment(
            enrichment=from_dict(json.loads(row["enrichment"])),
            enriched_at=row["enriched_at"] or "",
        )

    def enrichment_map(self) -> dict[int, StoredEnrichment]:
        """Every stored enrichment in one query (the listings view needs all of them)."""
        rows = self._conn.execute(
            "SELECT id, enrichment, enriched_at FROM listings WHERE enrichment IS NOT NULL"
        ).fetchall()
        return {
            row["id"]: StoredEnrichment(
                enrichment=from_dict(json.loads(row["enrichment"])),
                enriched_at=row["enriched_at"] or "",
            )
            for row in rows
        }

    def close(self) -> None:
        self._conn.close()
