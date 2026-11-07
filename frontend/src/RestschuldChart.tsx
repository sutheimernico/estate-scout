// The Restschuld curve: remaining debt at the end of every year, drawn like a section with the
// Zinsbindung as a dimension. All values come from the annuity result; this only draws them.

import { useRef, useState } from "react";

import { areaPath, clearOfGrid, linearScale, linePath, nearestIndex, niceTicks, withPayoff, yearTicks } from "./chartMath";
import { eurCents, eur, num } from "./format";
import { useWidth } from "./useWidth";

interface Props {
  series: { year: number; remaining_debt: number }[];
  principal?: number; // the loan amount: the curve starts there at year 0
  zinsbindungYears?: number | null;
  restschuld?: number | null;
  payoffYears?: number; // exact repayment time; the curve ends there
  compact?: boolean;
}

export function RestschuldChart({ series, principal, zinsbindungYears, restschuld, payoffYears, compact }: Props) {
  const wrap = useRef<HTMLDivElement>(null);
  const width = useWidth(wrap);
  const [hover, setHover] = useState<number | null>(null);

  const narrow = width < 520;
  const height = compact || narrow ? 220 : 300;
  const m = { l: narrow ? 56 : 68, r: 16, t: zinsbindungYears ? 40 : 16, b: 30 };

  const points = withPayoff(principal != null ? [{ year: 0, remaining_debt: principal }, ...series] : series, payoffYears);
  if (points.length < 2) return null;
  const maxYear = points[points.length - 1].year;
  const minYear = points[0].year;
  const yTicks = niceTicks(Math.max(...points.map((p) => p.remaining_debt)), 4);
  const yMax = yTicks[yTicks.length - 1];

  const x = linearScale(minYear, maxYear, m.l, width - m.r);
  const y = linearScale(0, yMax, height - m.b, m.t);
  const coords = points.map((p) => ({ x: x(p.year), y: y(p.remaining_debt) }));
  const baseY = height - m.b;

  const zb = zinsbindungYears != null && zinsbindungYears <= maxYear ? zinsbindungYears : null;
  const zbPoint = zb != null ? points.find((p) => p.year === zb) : undefined;
  const zbDebt = restschuld ?? zbPoint?.remaining_debt;
  const showZb = zb != null && zbDebt != null;

  function onMove(e: React.PointerEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const year = minYear + ((e.clientX - rect.left - m.l) / (width - m.l - m.r)) * (maxYear - minYear);
    setHover(nearestIndex(points.map((p) => p.year), year));
  }

  const hovered = hover != null ? points[hover] : null;
  const calloutRight = showZb && x(zb!) + (narrow ? 170 : 190) < width - m.r;
  // keep the callout text off the gridlines: they would run through its letters
  const calloutY = showZb
    ? clearOfGrid(y(zbDebt!) + (calloutRight ? -38 : 26), yTicks.map(y), 16, 28)
    : 0;

  return (
    <div className="chart" ref={wrap}>
      <div className="chart-readout" aria-live="off">
        {hovered ? (
          <>
            <span>Jahr {num(hovered.year)}</span>
            <strong className="num">Restschuld {eurCents(hovered.remaining_debt)}</strong>
          </>
        ) : (
          <>
            <span className="legend-line">Restschuld zum Jahresende</span>
            {showZb && <span className="legend-band">Zinsbindung</span>}
          </>
        )}
      </div>
      <svg
        width={width}
        height={height}
        role="img"
        aria-label={`Restschuld über ${maxYear} Jahre, von ${eur(points[0].remaining_debt)} auf ${eur(points[points.length - 1].remaining_debt)}${
          showZb ? `; nach ${zb} Jahren Zinsbindung ${eurCents(zbDebt!)}` : ""
        }. Werte stehen im Tilgungsplan darunter.`}
        onPointerMove={onMove}
        onPointerLeave={() => setHover(null)}
      >
        {yTicks.map((t) => (
          <g key={t}>
            <line className="grid" x1={m.l} x2={width - m.r} y1={y(t)} y2={y(t)} />
            <text className="tick" x={m.l - 8} y={y(t) + 4} textAnchor="end">
              {eur(t)}
            </text>
          </g>
        ))}
        {yearTicks(maxYear, narrow ? 4 : 7).map((t) => (
          <text key={t} className="tick" x={x(t)} y={height - 8} textAnchor="middle">
            {t === 0 ? "Jahr 0" : t}
          </text>
        ))}

        {showZb && (
          <g className="zb-band">
            <rect x={x(minYear)} y={m.t} width={x(zb!) - x(minYear)} height={baseY - m.t} />
            {/* the Zinsbindung as a dimension line above the plot */}
            <g className="zb-dim">
              <line x1={x(minYear)} x2={x(zb!)} y1={m.t - 14} y2={m.t - 14} />
              <line x1={x(minYear)} x2={x(minYear)} y1={m.t - 20} y2={m.t - 8} />
              <line x1={x(zb!)} x2={x(zb!)} y1={m.t - 20} y2={m.t - 8} />
              <text x={(x(minYear) + x(zb!)) / 2} y={m.t - 20} textAnchor="middle">
                {x(zb!) - x(minYear) > 120 ? `Zinsbindung ${zb} Jahre` : `${zb} J.`}
              </text>
            </g>
          </g>
        )}

        <path className="area" d={areaPath(coords, baseY)} />
        <path className="curve" d={linePath(coords)} pathLength={1} />

        {showZb && (
          <g className="zb-mark">
            <line x1={x(zb!)} x2={x(zb!)} y1={m.t} y2={baseY} />
            <circle cx={x(zb!)} cy={y(zbDebt!)} r={5.5} />
            <g transform={`translate(${calloutRight ? x(zb!) + 12 : x(zb!) - 12} ${calloutY})`}>
              <text textAnchor={calloutRight ? "start" : "end"} className="callout-label">
                {narrow ? `Restschuld nach ${zb} J.` : `Restschuld nach ${zb} Jahren`}
              </text>
              <text textAnchor={calloutRight ? "start" : "end"} y={20} className="callout-value">
                {eurCents(zbDebt!)}
              </text>
            </g>
          </g>
        )}

        {hovered && (
          <g className="hover">
            <line x1={x(hovered.year)} x2={x(hovered.year)} y1={m.t} y2={baseY} />
            <circle cx={x(hovered.year)} cy={y(hovered.remaining_debt)} r={4.5} />
          </g>
        )}
      </svg>
    </div>
  );
}
