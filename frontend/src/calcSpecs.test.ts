import { describe, expect, it } from "vitest";

import { buildArgs, defaultValues, SPECS } from "./calcSpecs";

const annuity = SPECS.find((s) => s.calc === "annuity")!;

describe("buildArgs", () => {
  it("turns the visible defaults into typed arguments", () => {
    const built = buildArgs(annuity, defaultValues(annuity));
    expect(built).toEqual({
      ok: true,
      args: {
        principal: 300000,
        annual_rate_percent: 3.6,
        initial_repayment_percent: 2,
        zinsbindung_years: 10,
      },
    });
  });

  it("reads German thousands separators instead of silently shrinking the amount", () => {
    const built = buildArgs(annuity, { ...defaultValues(annuity), principal: "300.000" });
    expect(built.ok && built.args.principal).toBe(300000);
  });

  it("reports a missing required field as 'missing', not as an error", () => {
    const built = buildArgs(annuity, { ...defaultValues(annuity), principal: "" });
    expect(built).toEqual({ ok: false, missing: true, errors: {} });
  });

  it("reports non-numeric text on the field that holds it", () => {
    const built = buildArgs(annuity, { ...defaultValues(annuity), annual_rate_percent: "abc" });
    expect(built.ok).toBe(false);
    if (!built.ok) expect(built.errors.annual_rate_percent).toMatch(/keine gültige Zahl/);
  });

  it("keeps the Bundesland as a code string", () => {
    const spec = SPECS.find((s) => s.calc === "purchase_costs")!;
    const built = buildArgs(spec, defaultValues(spec));
    expect(built.ok && built.args.bundesland).toBe("NI");
  });
});
