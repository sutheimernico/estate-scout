import { describe, expect, it } from "vitest";

import { germanError, toKnownCalc } from "./api";

describe("toKnownCalc", () => {
  it("narrows a well-formed result without any cast", () => {
    const known = toKnownCalc("yield_metrics", {
      annual_cold_rent: 12000,
      gross_yield_percent: 4,
      net_yield_percent: 3.2,
      kaufpreisfaktor: 25,
    });
    expect(known?.kind).toBe("yield_metrics");
  });

  it("returns null for a partial or malformed result instead of rendering NaN", () => {
    expect(toKnownCalc("yield_metrics", { annual_cold_rent: 12000 })).toBeNull();
    expect(toKnownCalc("purchase_costs", { bundesland: "NI", notary: "viel" })).toBeNull();
    expect(toKnownCalc("annuity", { monthly_payment: 1 })).toBeNull();
  });

  it("returns null for failed tool calls and unknown tools", () => {
    expect(toKnownCalc("annuity", { error: "missing" })).toBeNull();
    expect(toKnownCalc("nope", {})).toBeNull();
  });
});

describe("germanError", () => {
  it("keeps German backend text and never shows English details", () => {
    expect(germanError(409, "Beispielobjekt: die Referenzdaten sind fest.")).toMatch(/^Beispielobjekt/);
    expect(germanError(400, "initial_repayment must be > 0")).toMatch(/Eingabe abgelehnt/);
    expect(germanError(404, "listing 5 not found")).toMatch(/Nicht gefunden/);
    expect(germanError(503, "Ollama not reachable at http://x")).not.toMatch(/reachable/);
    expect(germanError(503, "Ollama ist nicht erreichbar unter x")).toMatch(/nicht erreichbar unter/);
  });
});
