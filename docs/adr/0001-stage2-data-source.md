# ADR-0001: Stage-2 data source for the scouting funnel

**Date:** 2026-07-06
**Status:** Accepted (autonomous decision recorded per AUTOPILOT; the owner can override the scope of the
auto-scan gap below).

## Context

The vision includes "continuously scan Niedersachsen/NRW for well-priced properties in good areas."
The domain research (`knowledge/06-datenzugriff-listings.md`) establishes that automated scraping of
the listing portals (ImmoScout24, Immowelt, Kleinanzeigen) is **not cleanly legal or feasible** for a
private tool:

- AGB explicitly forbid bots/crawlers/data-mining (civil, not criminal — but enforceable via account
  bans and, for systematic bulk extraction, § 87a UrhG database rights);
- active bot protection (Cloudflare/Akamai) makes it technically hostile and evasion pushes into the
  "clearly risky" zone;
- no free listings API exists for private users (only commercial/broker APIs);
- scraped listings carry seller personal data → DSGVO exposure if stored.

A portfolio piece framed as an "honest harness" must not ship AGB-violating scraping.

## Decision

**Stage 2 does NOT scrape listing portals.** The funnel is built as an *honest scout* over objects
the user brings in, enriched with public/legal data:

1. **Intake is user-initiated / manually assisted** — paste a listing's fields (or a single URL the
   user is viewing), or feed official portal search-agent / email results. No automated crawling.
   Persist only **object attributes** (price, size, rooms, year, location, features, source link) —
   **never seller contact data** (DSGVO).
2. **Enrichment from public/legal sources** behind provider seams (with fakes, faked in tests):
   Bodenrichtwert (BORIS.NI / BORIS.NRW), demographics & vacancy (Zensus / GENESIS REST API), price
   trend (Destatis / vdp). Each degrades honestly to "unavailable" rather than guessing.
3. **Transparent scoring** — price vs. local Bodenrichtwert/€-per-m², Kaufpreisfaktor & yield (reusing
   the Stage-1 `finance/` core), and location signals → a 0–100 score with per-factor contribution
   (the equity-scout transparency pattern). No black box; no fabricated market figures.
4. **zvg-portal.de** (Zwangsversteigerungen) is an *optional, experimental* amtliche source
   (public-law publication duty → legally low-risk), but has no API and complex sessions → flagged
   best-effort, not core.

## Consequences

- What ships: a legal, autonomously-buildable per-object evaluation + enrichment + scoring funnel
  that is genuinely useful for the objects the user is actually considering.
- What does NOT ship as scraping: the "continuously auto-scan every listing in NI/NRW" ambition. That
  gap is a **Needs-Owner** decision — accept manual/RSS/official-search-agent intake (the honest
  default), or pursue a commercial API/partnership (paid, out of scope for a free local tool). The
  loop will not attempt scraping to close this gap.

## Alternatives considered

- **Scrape anyway** — rejected: AGB/§ 87a UrhG/DSGVO risk, active bot protection, dishonest framing.
- **Commercial listings API** — rejected: paid, violates the local-&-free constraint.
- **Rely solely on portal RSS** — rejected as the sole path: historical feeds, current availability
  unverified; kept as an optional intake channel to verify live if it still exists.
