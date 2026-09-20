// One card per calculator result. All numbers come from the backend (finance/);
// this component only formats them.

import { type ReactNode } from "react";

import { AmortizationTable } from "./AmortizationTable";
import { type KnownCalc } from "./api";
import { eur, num, pct } from "./format";

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="calc">
      <h4>{title}</h4>
      <div className="grid">{children}</div>
    </div>
  );
}

// A fragment-returning row: the two spans become direct children of the CSS grid,
// so label and value land in adjacent grid cells instead of a nested wrapper.
function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span>{label}</span>
      <span className="num">{value}</span>
    </>
  );
}

export function CalcResultCard({ calc }: { calc: KnownCalc }) {
  switch (calc.kind) {
    case "annuity":
      return <AmortizationTable result={calc.result} />;
    case "purchase_costs": {
      const r = calc.result;
      return (
        <Card title={`Kaufnebenkosten (${r.bundesland})`}>
          <Row label="Grunderwerbsteuer" value={eur(r.grunderwerbsteuer)} />
          <Row label="Notar" value={eur(r.notary)} />
          <Row label="Grundbuch" value={eur(r.land_registry)} />
          <Row label="Makler" value={eur(r.makler)} />
          <Row label="Nebenkosten gesamt" value={eur(r.total_ancillary)} />
          <Row label="Gesamtinvestition" value={eur(r.total_investment)} />
          <Row label="Nebenkostenquote" value={pct(r.ancillary_quota_percent)} />
          <Row label="Mindest-Eigenkapital" value={eur(r.min_equity)} />
        </Card>
      );
    }
    case "affordability": {
      const r = calc.result;
      return (
        <Card title="Leistbarkeit">
          <Row label="Max. Monatsrate" value={eur(r.max_monthly_payment)} />
          <Row label="Max. Darlehen" value={eur(r.max_loan)} />
          <Row label="Max. Kaufpreis" value={eur(r.max_purchase_price)} />
          <Row label="Nebenkostenquote" value={pct(r.ancillary_quota_percent)} />
          <Row label="Eigenkapital" value={eur(r.equity)} />
        </Card>
      );
    }
    case "yield_metrics": {
      const r = calc.result;
      return (
        <Card title="Mietrendite">
          <Row label="Jahreskaltmiete" value={eur(r.annual_cold_rent)} />
          <Row label="Bruttorendite" value={pct(r.gross_yield_percent)} />
          <Row label="Nettorendite" value={pct(r.net_yield_percent)} />
          <Row label="Kaufpreisfaktor" value={num(r.kaufpreisfaktor)} />
        </Card>
      );
    }
    case "operating_costs": {
      const r = calc.result;
      return (
        <Card title="Bewirtschaftungskosten (p.a.)">
          <Row label="Instandhaltung" value={eur(r.instandhaltung)} />
          <Row label="Verwaltung" value={eur(r.verwaltung)} />
          <Row label="Mietausfallwagnis" value={eur(r.mietausfallwagnis)} />
          <Row label="Gesamt" value={eur(r.total_annual)} />
        </Card>
      );
    }
    case "equity_return": {
      const r = calc.result;
      return (
        <Card title="Eigenkapitalrendite (Jahr 1)">
          <Row label="Darlehen" value={eur(r.loan)} />
          <Row label="Kapitaldienst p.a." value={eur(r.annual_debt_service)} />
          <Row label="Netto-Mietertrag p.a." value={eur(r.net_operating_income)} />
          <Row label="Cashflow vor Steuern" value={eur(r.cashflow_before_tax)} />
          <Row label="EK-Rendite" value={pct(r.cash_on_cash_percent)} />
        </Card>
      );
    }
  }
}
