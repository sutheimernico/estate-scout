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

  it("rejects zero where the calculator needs a positive number, and any negative amount", () => {
    const zero = buildArgs(annuity, { ...defaultValues(annuity), initial_repayment_percent: "0" });
    expect(!zero.ok && zero.errors.initial_repayment_percent).toMatch(/größer 0/);
    const negative = buildArgs(annuity, { ...defaultValues(annuity), principal: "-5000" });
    expect(!negative.ok && negative.errors.principal).toMatch(/größer 0/);
    const sonder = buildArgs(annuity, { ...defaultValues(annuity), annual_sondertilgung: "-1" });
    expect(!sonder.ok && sonder.errors.annual_sondertilgung).toMatch(/nicht negativ/);
    expect(buildArgs(annuity, { ...defaultValues(annuity), annual_rate_percent: "0" }).ok).toBe(true);
  });

  it("works the Leistbarkeit assumption out from the current income", () => {
    const spec = SPECS.find((s) => s.calc === "affordability")!;
    const text = (income: string) => spec.assumption!({ net_monthly_income: income }).replace(/\s/g, " ");
    expect(text("4.000")).toContain("bei 4.000 € netto also 1.400 € im Monat");
    expect(text("5.200")).toContain("1.820 € im Monat");
    expect(text("abc")).not.toMatch(/netto also/);
  });
});
