import { describe, expect, it } from "vitest";

import { coveragePips, effectiveScore, type ListingForm, parseListingForm, parseRent, roomsAndYear, scoreTone } from "./listingView";

const form: ListingForm = {
  price: "300.000",
  area: "100,5",
  bundesland: "NI",
  ort: " Lingen ",
  rooms: "",
  year: "",
  objectType: "wohnung",
};

describe("parseListingForm", () => {
  it("reads German number input without the wrong-by-1000 trap", () => {
    const r = parseListingForm(form);
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.listing).toMatchObject({ price: 300000, living_area_sqm: 100.5, ort: "Lingen", object_type: "wohnung" });
      expect(r.listing.rooms).toBeUndefined();
    }
  });

  it("reports each invalid field in German", () => {
    const r = parseListingForm({ ...form, price: "abc", area: "0", rooms: "x", year: "19" });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(Object.keys(r.errors).sort()).toEqual(["area", "price", "rooms", "year"]);
  });

  it("accepts optional rooms and a plausible year", () => {
    const r = parseListingForm({ ...form, rooms: "3,5", year: "1995" });
    expect(r.ok && r.listing.rooms).toBe(3.5);
    expect(r.ok && r.listing.year_built).toBe(1995);
  });

  it("rejects a year far in the future", () => {
    expect(parseListingForm({ ...form, year: "2100" }, 2026).ok).toBe(false);
  });
});

describe("parseRent", () => {
  it("treats empty and non-positive input as no rent", () => {
    expect(parseRent("")).toBeUndefined();
    expect(parseRent("0")).toBeUndefined();
    expect(parseRent("abc")).toBeUndefined();
    expect(parseRent("1.050,50")).toBe(1050.5);
  });
});

describe("score presentation", () => {
  it("maps totals to tones and null to none", () => {
    expect(scoreTone(80)).toBe("good");
    expect(scoreTone(59)).toBe("mid");
    expect(scoreTone(12)).toBe("low");
    expect(scoreTone(null)).toBe("none");
  });

  it("converts confidence to filled pips within 0..4", () => {
    expect(coveragePips(0.5)).toBe(2);
    expect(coveragePips(1)).toBe(4);
    expect(coveragePips(0)).toBe(0);
    expect(coveragePips(7)).toBe(4);
  });

  it("prefers a fresh report over the list score", () => {
    const listing = { score: { total: null, confidence: 0.25 } } as Parameters<typeof effectiveScore>[0];
    expect(effectiveScore(listing)?.total).toBeNull();
    const report = { total: 59, confidence: 1 } as Parameters<typeof effectiveScore>[1];
    expect(effectiveScore(listing, report)).toEqual({ total: 59, confidence: 1 });
  });
});

describe("roomsAndYear", () => {
  it("joins what is known and drops what is not", () => {
    expect(roomsAndYear({ rooms: 3, year_built: 1995 })).toBe("3 Zimmer · Baujahr 1995");
    expect(roomsAndYear({ rooms: null, year_built: 1995 })).toBe("Baujahr 1995");
    expect(roomsAndYear({ rooms: null, year_built: null })).toBe("");
  });
});
