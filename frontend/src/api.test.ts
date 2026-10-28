import { describe, expect, it } from "vitest";

import { toKnownCalc } from "./api";

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
