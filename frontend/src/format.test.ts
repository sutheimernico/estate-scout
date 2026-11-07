import { describe, expect, it } from "vitest";

import { bindUnits, duration, eur, germanDate, eurCents, formatInput, num, pct } from "./format";

const nbsp = (s: string) => s.replace(/\s/g, " "); // Intl uses (narrow) no-break spaces

describe("de-DE formatting", () => {
  it("uses dots for thousands and commas for decimals", () => {
    expect(nbsp(eur(300000))).toBe("300.000 €");
    expect(nbsp(eurCents(1399.94))).toBe("1.399,94 €");
    expect(num(28.7)).toBe("28,7");
    expect(pct(3.6)).toBe("3,60 %");
    expect(pct(10.57)).toBe("10,57 %");
  });
});

describe("bindUnits", () => {
  it("glues numbers to their unit with a no-break space", () => {
    expect(bindUnits("bei 300.000 € und 3,6 % für 10 Jahre")).toBe("bei 300.000 € und 3,6 % für 10 Jahre");
  });
  it("leaves other text alone", () => {
    expect(bindUnits("Zinsbindung in Euro")).toBe("Zinsbindung in Euro");
  });
});

describe("formatInput", () => {
  it.each([
    ["300000", "300.000"],
    ["300.000", "300.000"],
    ["1234,5", "1.234,5"],
    ["2,0", "2,0"],
    ["3,60", "3,60"],
    ["3,6 %", "3,6"],
    ["0", "0"],
  ])("tidies %s to %s", (raw, expected) => {
    expect(formatInput(raw)).toBe(expected);
  });
  it.each(["", "abc", "1,2,3"])("leaves %j untouched", (raw) => {
    expect(formatInput(raw)).toBe(raw);
  });
});

describe("duration", () => {
  it("speaks years and months", () => {
    expect(duration(28.7)).toBe("28 Jahre, 8 Monate");
    expect(duration(28.7, true)).toBe("28 Jahren, 8 Monaten");
    expect(duration(10)).toBe("10 Jahre");
    expect(duration(1.09, true)).toBe("1 Jahr, 1 Monat");
    expect(duration(0.5)).toBe("6 Monate");
  });
});

describe("germanDate", () => {
  it("writes ISO dates the German way", () => {
    expect(germanDate("2026-09-20")).toBe("20.09.2026");
    expect(germanDate("unbekannt")).toBe("unbekannt");
  });
});
