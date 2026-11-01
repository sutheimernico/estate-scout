import { describe, expect, it } from "vitest";

import { countUpValue, easeOutCubic, motionAllowed } from "./motion";

describe("count-up maths", () => {
  it("starts at from, ends at to and never overshoots", () => {
    expect(countUpValue(0, 100, 0, 700)).toBe(0);
    expect(countUpValue(0, 100, 700, 700)).toBe(100);
    expect(countUpValue(0, 100, 5000, 700)).toBe(100);
    for (let t = 0; t <= 700; t += 50) {
      const v = countUpValue(0, 100, t, 700);
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(100);
    }
  });

  it("eases out: more than half the distance in the first half of the time", () => {
    expect(easeOutCubic(0.5)).toBeGreaterThan(0.5);
  });

  it("counts down as well as up", () => {
    expect(countUpValue(100, 0, 350, 700)).toBeLessThan(50);
  });

  it("does not animate where matchMedia is missing (jsdom) so tests see final values", () => {
    expect(motionAllowed()).toBe(false);
  });
});
