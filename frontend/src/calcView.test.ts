import { describe, expect, it } from "vitest";

import { type KnownCalc } from "./api";
import { factsOf, heroOf, segmentShares, segmentsOf, titleOf, yieldScaleMax } from "./calcView";

const annuity: KnownCalc = {
  kind: "annuity",
  result: {
    monthly_payment: 1400,
    total_interest: 181209.86,
    total_paid: 481209.86,
    months_to_payoff: 344,
    years_to_payoff: 28.7,
    remaining_debt_by_year: [{ year: 1, remaining_debt: 293900 }],
    zinsbindung_years: 10,
    restschuld_after_zinsbindung: 227907.14,
    interest_during_zinsbindung: 95907.14,
  },
};

describe("heroOf / factsOf", () => {
  it("leads the annuity with the Monatsrate in cents, de-DE", () => {
    const hero = heroOf(annuity);
    expect(hero.label).toBe("Monatsrate");
    expect(hero.format(hero.value).replace(/\u00a0/g, " ")).toBe("1.400,00 €");
  });

  it("names the Zinsbindung in the Restschuld fact and omits it when none was asked for", () => {
    expect(factsOf(annuity).map((f) => f.label)).toContain("Restschuld nach 10 Jahren Zinsbindung");
    const without: KnownCalc = {
      kind: "annuity",
      result: { ...annuity.result, zinsbindung_years: null, restschuld_after_zinsbindung: null, interest_during_zinsbindung: null },
    } as KnownCalc;
    expect(factsOf(without).some((f) => /Zinsbindung/.test(f.label))).toBe(false);
  });

  it("puts the Bundesland name, not its code, into the title context", () => {
    const calc: KnownCalc = {
      kind: "purchase_costs",
      result: {
        bundesland: "NW",
        grunderwerbsteuer: 19500,
        notary: 4500,
        land_registry: 1500,
        makler: 10710,
        total_ancillary: 36210,
        total_investment: 336210,
        ancillary_quota_percent: 12.07,
        min_equity: 36210,
      },
    };
    expect(titleOf(calc)).toEqual({ title: "Kaufnebenkosten", context: "Nordrhein-Westfalen" });
    expect(segmentsOf(calc)?.map((s) => s.label)).toEqual(["Grunderwerbsteuer", "Notar", "Grundbuch", "Makler"]);
  });
});

describe("segments", () => {
  it("splits the annuity into loan and interest that add up to the total paid", () => {
    const segs = segmentsOf(annuity)!;
    expect(segs[0].value + segs[1].value).toBeCloseTo(481209.86, 2);
  });
  it("splits the Leistbarkeit budget into loan, equity and ancillary costs that sum to loan + equity", () => {
    const calc: KnownCalc = {
      kind: "affordability",
      result: {
        max_monthly_payment: 1400,
        max_loan: 300000,
        max_purchase_price: 325585.6,
        ancillary_quota_percent: 10.57,
        equity: 60000,
      },
    };
    const segs = segmentsOf(calc)!;
    expect(segs.map((s) => s.label)).toEqual(["Darlehen", "Eigenkapital im Kaufpreis", "Kaufnebenkosten"]);
    expect(segs.reduce((a, s) => a + s.value, 0)).toBeCloseTo(360000, 2);
    expect(segs[2].value).toBeCloseTo(34414.4, 1);
  });
  it("shares add up to 100 and ignore negative parts", () => {
    const shares = segmentShares([
      { label: "a", value: 30, tone: "ink" },
      { label: "b", value: 70, tone: "red" },
      { label: "c", value: -5, tone: "green" },
    ]);
    expect(shares.reduce((a, b) => a + b, 0)).toBeCloseTo(100);
    expect(shares[2]).toBe(0);
    expect(segmentShares([{ label: "a", value: 0, tone: "ink" }])).toEqual([0]);
  });
  it("gives the yield ruler room above both markers", () => {
    expect(yieldScaleMax(4, 3.2)).toBe(8);
    expect(yieldScaleMax(9.4, 7)).toBe(11);
  });
});
