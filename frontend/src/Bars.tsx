// Proportional bars used under the headline figure. Both draw in with a scaleX animation
// (transform only) and always carry their numbers as text, so colour is never the only signal.

import { type Segment, segmentShares } from "./calcView";
import { eur } from "./format";

export function SplitBar({ segments }: { segments: Segment[] }) {
  const shares = segmentShares(segments);
  return (
    <div className="split">
      <div
        className="split-bar"
        role="img"
        aria-label={segments.map((s) => `${s.label} ${eur(s.value)}`).join(", ")}
        style={{ gridTemplateColumns: shares.map((s) => `${s}fr`).join(" ") }}
      >
        {segments.map((s, i) => (
          <i key={s.label} className={`seg tone-${s.tone}`} style={{ ["--i" as string]: i }} />
        ))}
      </div>
      <ul className="split-legend">
        {segments.map((s) => (
          <li key={s.label}>
            <i className={`swatch tone-${s.tone}`} aria-hidden="true" />
            <span>{s.label}</span>
            <strong className="num">{eur(s.value)}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

export interface BarRow {
  label: string;
  value: number; // signed; the bar shows the magnitude, a negative one turns red
  display: string;
  tone: "ink" | "red" | "green" | "ochre";
}

// Rows on one common scale 0..max, with an optional axis underneath.
export function BarScale({
  rows,
  max,
  ticks,
}: {
  rows: BarRow[];
  max: number;
  ticks?: { value: number; label: string }[];
}) {
  return (
    <div className="scale">
      {rows.map((r, i) => (
        <div className="scale-row" key={r.label}>
          <span className="scale-label">{r.label}</span>
          <span className="scale-track">
            <i
              className={`scale-bar tone-${r.value < 0 ? "red" : r.tone}${r.value < 0 ? " negative" : ""}`}
              style={{ width: `${Math.min(100, (Math.abs(r.value) / max) * 100)}%`, ["--i" as string]: i }}
            />
          </span>
          <strong className="scale-value num">{r.display}</strong>
        </div>
      ))}
      {ticks && (
        <div className="scale-row scale-axis" aria-hidden="true">
          <span />
          <span className="scale-track">
            {ticks.map((t) => (
              <span key={t.value} className="scale-tick" style={{ left: `${(t.value / max) * 100}%` }}>
                {t.label}
              </span>
            ))}
          </span>
          <span />
        </div>
      )}
    </div>
  );
}
