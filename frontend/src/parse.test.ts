import { describe, expect, it } from "vitest";

import { parseDecimal } from "./parse";

describe("parseDecimal", () => {
  it.each([
    ["3,6", 3.6],
    ["300000", 300000],
    ["300.000", 300000],
    ["1.234,56", 1234.56],
    ["3.6", 3.6],
    [" 2,0 % ", 2],
    ["1.200.000", 1200000],
    ["3,", 3],
  ])("reads %s as %d", (raw, expected) => {
    expect(parseDecimal(raw)).toBe(expected);
  });

  it.each(["", "   ", "abc", "1,2,3", "3,6x"])("rejects %j", (raw) => {
    expect(parseDecimal(raw)).toBeNull();
  });
});
