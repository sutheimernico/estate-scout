// Renders an annuity tool result: summary figures + the per-year remaining-debt schedule.
// All numbers come from the backend (finance/), so this component only formats them.

import { type AnnuityResult } from "./api";
import { eur, eurCents, num } from "./format";

export function AmortizationTable({ result }: { result: AnnuityResult }) {
  return (
    <div className="calc">
      <h4>Annuitätendarlehen</h4>
      <div className="grid">
        <span>Monatsrate</span>
        <span className="num">{eurCents(result.monthly_payment)}</span>
        <span>Zinskosten gesamt</span>
        <span className="num">{eur(result.total_interest)}</span>
        <span>Gesamt gezahlt</span>
        <span className="num">{eur(result.total_paid)}</span>
        <span>Volltilgung nach</span>
        <span className="num">{num(result.years_to_payoff)} Jahre</span>
        {result.zinsbindung_years != null && result.restschuld_after_zinsbindung != null && (
          <>
            <span>Restschuld nach {result.zinsbindung_years} Jahren Zinsbindung</span>
            <span className="num">{eur(result.restschuld_after_zinsbindung)}</span>
          </>
        )}
        {result.zinsbindung_years != null && result.interest_during_zinsbindung != null && (
          <>
            <span>Zinsen in der Zinsbindung</span>
            <span className="num">{eur(result.interest_during_zinsbindung)}</span>
          </>
        )}
      </div>
      <table>
        <thead>
          <tr>
            <th>Jahr</th>
            <th>Restschuld</th>
          </tr>
        </thead>
        <tbody>
          {result.remaining_debt_by_year.map((r) => (
            <tr key={r.year}>
              <td>{r.year}</td>
              <td className="num">{eur(r.remaining_debt)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
