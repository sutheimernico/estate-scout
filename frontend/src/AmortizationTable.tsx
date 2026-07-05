// Renders an annuity tool result: summary figures + the per-year remaining-debt schedule.
// All numbers come from the backend (finance/), so this component only formats them.

interface YearRow {
  year: number;
  remaining_debt: number;
}

export interface AnnuityResult {
  monthly_payment: number;
  total_interest: number;
  total_paid: number;
  years_to_payoff: number;
  remaining_debt_by_year: YearRow[];
}

const eur = (n: number) =>
  n.toLocaleString("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

export function AmortizationTable({ result }: { result: AnnuityResult }) {
  return (
    <div className="calc">
      <h4>Annuitätendarlehen</h4>
      <div className="grid">
        <span>Monatsrate</span>
        <span className="num">{eur(result.monthly_payment)}</span>
        <span>Zinskosten gesamt</span>
        <span className="num">{eur(result.total_interest)}</span>
        <span>Gesamt gezahlt</span>
        <span className="num">{eur(result.total_paid)}</span>
        <span>Volltilgung nach</span>
        <span className="num">{result.years_to_payoff} J.</span>
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
