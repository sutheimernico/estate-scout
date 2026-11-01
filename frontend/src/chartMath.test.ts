import { describe, expect, it } from "vitest";

import { areaPath, linearScale, linePath, nearestIndex, niceTicks, yearTicks } from "./chartMath";

describe("niceTicks", () => {
  it("covers the maximum with round steps starting at zero", () => {
    expect(niceTicks(300000)).toEqual([0, 100000, 200000, 300000]);
    expect(niceTicks(293900)).toEqual([0, 100000, 200000, 300000]);
    expect(niceTicks(7)).toEqual([0, 2, 4, 6, 8]);
  });
  it("does not break on a zero maximum", () => {
    expect(niceTicks(0)).toEqual([0, 1]);
  });
});

describe("paths", () => {
  it("builds a polyline and a closed area", () => {
    const pts = [
      { x: 0, y: 10 },
      { x: 10, y: 20 },
    ];
    expect(linePath(pts)).toBe("M0.0 10.0 L10.0 20.0");
    expect(areaPath(pts, 30)).toBe("M0.0 10.0 L10.0 20.0 L10.0 30 L0.0 30 Z");
    expect(areaPath([], 30)).toBe("");
  });
  it("maps a domain onto a range, also inverted (SVG y)", () => {
    const y = linearScale(0, 100, 200, 0);
    expect(y(0)).toBe(200);
    expect(y(100)).toBe(0);
    expect(y(50)).toBe(100);
  });
});

describe("hover and axis helpers", () => {
  it("finds the nearest year", () => {
    expect(nearestIndex([0, 1, 2, 3], 2.4)).toBe(2);
    expect(nearestIndex([0, 1, 2, 3], -5)).toBe(0);
  });
  it("labels whole years only", () => {
    for (const max of [5, 12, 29, 40]) {
      const t = yearTicks(max);
      expect(t.every(Number.isInteger)).toBe(true);
      expect(t[0]).toBe(0);
      expect(t.length).toBeLessThanOrEqual(9);
    }
  });
});
