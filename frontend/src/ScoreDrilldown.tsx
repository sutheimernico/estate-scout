// Presentational breakdown of one ScoreReport: a bar per building block, the weight that
// block actually carried, and an honest list of what was missing and why.
// Every number comes from the backend's scoring engine — nothing is computed here.

import { type ScoreReport, type SubScore } from "./api";
import { num, pct } from "./format";

const BLOCK_LABELS: Record<string, string> = {
  yield: "Rendite",
  price: "Preisniveau",
  region: "Lage",
};

const REASON_LABELS: Record<string, string> = {
  provider_missing: "Datenquelle fehlt",
  no_data: "keine Daten für dieses Objekt",
  rent_missing: "keine Kaltmiete angegeben",
};

const BLOCK_HINTS: Record<string, string> = {
  yield: "Bruttomietrendite: 0 % → 0, ab 6 % → 100.",
  price: "€/m² Wohnfläche ÷ Bodenrichtwert (€/m² Boden) — ein Näherungswert, keine Bewertung.",
  region: "Bevölkerungstrend und Leerstandsquote, gemittelt.",
};

export function reasonLabel(reason: string): string {
  return REASON_LABELS[reason] ?? reason;
}

function Bar({ sub, weight }: { sub: SubScore; weight: number | undefined }) {
  const label = BLOCK_LABELS[sub.name] ?? sub.name;
  return (
    <div className="score-row">
      <span className="score-label" title={BLOCK_HINTS[sub.name]}>
        {label}
      </span>
      <span className="score-bar" aria-hidden="true">
        <span className="score-fill" style={{ width: `${sub.value ?? 0}%` }} />
      </span>
      <span className="num score-value">
        {sub.value === null ? "n. v." : `${sub.value}/100`}
      </span>
      <span className="num score-weight">{weight === undefined ? "—" : pct(weight * 100)}</span>
    </div>
  );
}

export function ScoreDrilldown({ report }: { report: ScoreReport }) {
  const missing = report.subscores.filter((s) => s.value === null);
  return (
    <div className="score-panel">
      <div className="score-head">
        <span className="score-total">
          {report.total === null ? "Kein Score" : `${report.total}/100`}
        </span>
        <span className="score-confidence">
          Datenlage {report.inputs_available}/{report.inputs_expected} (
          {num(report.confidence * 100, 0)} %)
        </span>
      </div>

      {report.subscores.map((s) => (
        <Bar key={s.name} sub={s} weight={report.weights_used[s.name]} />
      ))}

      {missing.length > 0 && (
        <div className="score-missing">
          <h5>Nicht verfügbar</h5>
          <ul>
            {missing.map((s) => (
              <li key={s.name}>
                {BLOCK_LABELS[s.name] ?? s.name}: {reasonLabel(s.reason ?? "no_data")}
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="score-foot">
        Gewichte und Schwellen aus <code>config/scoring.yaml</code> (Stand {report.as_of}) — eigene
        Heuristik, keine Bewertung und keine Anlageberatung.
      </p>
    </div>
  );
}
