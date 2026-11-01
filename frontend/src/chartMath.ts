// Pure geometry for the SVG charts, kept apart from React so it can be tested.

// Round tick values from 0 up to at least `max`: [0, 100000, 200000, 300000].
export function niceTicks(max: number, target = 4): number[] {
  if (!(max > 0)) return [0, 1];
  const rough = max / target;
  const magnitude = Math.pow(10, Math.floor(Math.log10(rough)));
  const step = ([1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= rough) ??
    10 * magnitude) as number;
  const ticks: number[] = [];
  for (let v = 0; v < max + step; v += step) {
    ticks.push(Math.round(v * 1e6) / 1e6);
    if (v >= max) break;
  }
  return ticks;
}

export interface Pt {
  x: number;
  y: number;
}

export function linePath(points: Pt[]): string {
  return points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
}

export function areaPath(points: Pt[], baseY: number): string {
  if (points.length === 0) return "";
  const first = points[0];
  const last = points[points.length - 1];
  return `${linePath(points)} L${last.x.toFixed(1)} ${baseY} L${first.x.toFixed(1)} ${baseY} Z`;
}

export const linearScale =
  (d0: number, d1: number, r0: number, r1: number) =>
  (v: number): number =>
    d1 === d0 ? r0 : r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

// Index of the point whose x is closest to `x` (the hovered year).
export function nearestIndex(xs: number[], x: number): number {
  let best = 0;
  for (let i = 1; i < xs.length; i++) {
    if (Math.abs(xs[i] - x) < Math.abs(xs[best] - x)) best = i;
  }
  return best;
}

// Year labels on the x axis: about `target` of them, always whole years, starting at 0.
export function yearTicks(maxYear: number, target = 6): number[] {
  const raw = Math.max(1, Math.ceil(maxYear / target));
  const step = maxYear <= 12 ? raw : Math.ceil(raw / 5) * 5;
  const ticks: number[] = [];
  for (let y = 0; y <= maxYear; y += step) ticks.push(y);
  return ticks;
}
