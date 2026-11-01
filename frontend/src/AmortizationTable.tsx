// The per-year remaining-debt schedule: the plain-text counterpart of the Restschuld curve.

import { type AnnuityResult } from "./api";
import { eur } from "./format";

export function AmortizationTable({ result }: { result: AnnuityResult }) {
  return (
    <table className="plan-table">
      <caption className="sr-only">Restschuld zum Jahresende</caption>
      <thead>
        <tr>
          <th scope="col">Jahr</th>
          <th scope="col">Restschuld</th>
        </tr>
      </thead>
      <tbody>
        {result.remaining_debt_by_year.map((r) => (
          <tr key={r.year} className={r.year === result.zinsbindung_years ? "mark" : undefined}>
            <td>{r.year}</td>
            <td className="num">{eur(r.remaining_debt)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
