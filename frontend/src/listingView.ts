// Pure logic behind the Objekte tab: form parsing, score presentation. No React in here.

import { type Listing, type NewListing, type ScoreReport } from "./api";
import { parseDecimal } from "./parse";

export interface ListingForm {
  price: string;
  area: string;
  bundesland: string;
  ort: string;
  rooms: string;
  year: string;
  objectType: string;
}

export type FormErrors = Partial<Record<keyof ListingForm, string>>;

export type ParsedForm = { ok: true; listing: NewListing } | { ok: false; errors: FormErrors };

export function parseListingForm(form: ListingForm, thisYear = new Date().getFullYear()): ParsedForm {
  const errors: FormErrors = {};
  const price = parseDecimal(form.price);
  const area = parseDecimal(form.area);
  const rooms = form.rooms.trim() === "" ? undefined : parseDecimal(form.rooms);
  const year = form.year.trim() === "" ? undefined : parseDecimal(form.year);

  if (price === null || price <= 0) errors.price = "Kaufpreis: bitte eine Zahl größer 0 eintragen.";
  if (area === null || area <= 0) errors.area = "Wohnfläche: bitte eine Zahl größer 0 eintragen.";
  if (!form.bundesland.trim()) errors.bundesland = "Bundesland fehlt.";
  if (rooms === null || (rooms !== undefined && rooms <= 0)) errors.rooms = "Zimmer: bitte eine Zahl größer 0 eintragen.";
  if (year === null || (year !== undefined && (!Number.isInteger(year) || year < 1500 || year > thisYear + 5))) {
    errors.year = "Baujahr: bitte ein Jahr eintragen, z. B. 1995.";
  }
  if (Object.keys(errors).length > 0) return { ok: false, errors };

  return {
    ok: true,
    listing: {
      price: price as number,
      living_area_sqm: area as number,
      bundesland: form.bundesland.trim(),
      ort: form.ort.trim(),
      object_type: form.objectType,
      rooms: rooms ?? undefined, // validated above: null is not possible here
      year_built: year ?? undefined,
    },
  };
}

// An empty or invalid rent simply means "score without a rent" — never a guess.
export function parseRent(raw: string): number | undefined {
  const value = parseDecimal(raw);
  return value === null || value <= 0 ? undefined : value;
}

export type ScoreTone = "good" | "mid" | "low" | "none";

export function scoreTone(total: number | null | undefined): ScoreTone {
  if (total === null || total === undefined) return "none";
  if (total >= 70) return "good";
  if (total >= 50) return "mid";
  return "low";
}

// Data coverage as 0..4 filled pips (the score is built from four inputs).
export function coveragePips(confidence: number, expected = 4): number {
  return Math.max(0, Math.min(expected, Math.round(confidence * expected)));
}

// The freshest report wins over the list response: the list is scored without a rent (the
// table convention), the report may include the one the user just typed in.
export function effectiveScore(
  listing: Listing,
  report?: ScoreReport,
): { total: number | null; confidence: number } | null {
  if (report) return { total: report.total, confidence: report.confidence };
  return listing.score;
}

export function roomsAndYear(l: Pick<Listing, "rooms" | "year_built">): string {
  const parts: string[] = [];
  if (l.rooms !== null) parts.push(`${l.rooms.toLocaleString("de-DE")} Zimmer`);
  if (l.year_built !== null) parts.push(`Baujahr ${l.year_built}`);
  return parts.join(" · ");
}

// One honest line under a tile's score: why there is no score, or why it is only provisional.
export function scoreNote(listing: Pick<Listing, "enrichment">, score: { total: number | null; confidence: number } | null): string | null {
  if (score === null || (score.total === null && listing.enrichment === null)) return "Öffnen, um das Objekt zu bewerten.";
  if (score.total === null) return "Für diese Lage liegen keine Referenzdaten vor.";
  const n = coveragePips(score.confidence);
  if (n < 2) return `Vorläufig: erst ${n} von 4 Datenquellen.`;
  return null;
}
