import { coveragePips, scoreTone } from "./listingView";

// The score read from a 0..100 ruler: filled bar, red marker, three ticks. The number is
// always printed, so the bar is never the only carrier of the value.
export function ScoreScale({ total }: { total: number | null }) {
  const tone = scoreTone(total);
  return (
    <div className={`score-scale tone-${tone}`}>
      <div className="score-scale-head">
        <strong className="score-scale-num num">{total === null ? "—" : total}</strong>
        <span className="score-scale-of">{total === null ? "nicht bewertet" : "von 100"}</span>
      </div>
      <div className="score-scale-track" aria-hidden="true">
        {total !== null && (
          <>
            <i className="score-scale-fill" style={{ width: `${total}%` }} />
            <i className="score-scale-mark" style={{ left: `${total}%` }} />
          </>
        )}
        <span className="score-scale-tick" style={{ left: "0%" }} />
        <span className="score-scale-tick" style={{ left: "50%" }} />
        <span className="score-scale-tick" style={{ left: "100%" }} />
      </div>
    </div>
  );
}

// Four pips: how many of the four score inputs actually had data.
export function CoveragePips({ confidence }: { confidence: number }) {
  const n = coveragePips(confidence);
  return (
    <span className="pips" role="img" aria-label={`Datenlage ${n} von 4`}>
      {[0, 1, 2, 3].map((i) => (
        <i key={i} className={i < n ? "pip on" : "pip"} />
      ))}
    </span>
  );
}
