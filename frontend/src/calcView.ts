// What each calculator result looks like as a headline figure plus a list of facts.
// Pure (no React): the strings and numbers here are tested; the components only lay them out.
// All values come from the backend result; nothing is computed here except choosing which to show.

import { type KnownCalc } from "./api";
import { eur, eurCents, num, pct } from "./format";
import { bundeslandName } from "./labels";

export interface Hero {
  label: string;
  value: number;
  format: (n: number) => string;
  unit: string; // text on the dimension line under the figure
}

export interface Fact {
  label: string;
  value: string;
}

export interface CalcTitle {
  title: string;
  context?: string;
}

export function titleOf(calc: KnownCalc): CalcTitle {
  switch (calc.kind) {
    case "annuity":
      return { title: "Annuitätendarlehen" };
    case "purchase_costs":
      return { title: "Kaufnebenkosten", context: bundeslandName(calc.result.bundesland) };
    case "affordability":
      return { title: "Leistbarkeit" };
    case "yield_metrics":
      return { title: "Mietrendite" };
    case "operating_costs":
      return { title: "Bewirtschaftungskosten" };
    case "equity_return":
      return { title: "Cashflow-Rendite vor Steuern", context: "Jahr 1" };
  }
}

export function heroOf(calc: KnownCalc): Hero {
  switch (calc.kind) {
    case "annuity":
      return { label: "Monatsrate", value: calc.result.monthly_payment, format: eurCents, unit: "pro Monat" };
    case "purchase_costs":
      return {
        label: "Kaufnebenkosten gesamt",
        value: calc.result.total_ancillary,
        format: eur,
        unit: `${pct(calc.result.ancillary_quota_percent)} vom Kaufpreis`,
      };
    case "affordability":
      return { label: "Maximaler Kaufpreis", value: calc.result.max_purchase_price, format: eur, unit: "bei diesem Budget" };
    case "yield_metrics":
      return { label: "Bruttomietrendite", value: calc.result.gross_yield_percent, format: pct, unit: "Jahreskaltmiete ÷ Kaufpreis" };
    case "operating_costs":
      return { label: "Bewirtschaftungskosten", value: calc.result.total_annual, format: eur, unit: "pro Jahr" };
    case "equity_return":
      return {
        label: "Rendite auf das Eigenkapital",
        value: calc.result.cash_on_cash_percent,
        format: pct,
        unit: "Cashflow vor Steuern ÷ Eigenkapital",
      };
  }
}

export function factsOf(calc: KnownCalc): Fact[] {
  switch (calc.kind) {
    case "annuity": {
      const r = calc.result;
      const facts: Fact[] = [
        { label: "Zinskosten gesamt", value: eur(r.total_interest) },
        { label: "Gesamt gezahlt", value: eur(r.total_paid) },
        { label: "Volltilgung nach", value: `${num(r.years_to_payoff)} Jahre` },
      ];
      if (r.zinsbindung_years != null && r.restschuld_after_zinsbindung != null) {
        facts.push({
          label: `Restschuld nach ${r.zinsbindung_years} Jahren Zinsbindung`,
          value: eur(r.restschuld_after_zinsbindung),
        });
      }
      if (r.zinsbindung_years != null && r.interest_during_zinsbindung != null) {
        facts.push({ label: "Zinsen in der Zinsbindung", value: eur(r.interest_during_zinsbindung) });
      }
      return facts;
    }
    case "purchase_costs": {
      const r = calc.result;
      return [
        { label: "Grunderwerbsteuer", value: eur(r.grunderwerbsteuer) },
        { label: "Notar", value: eur(r.notary) },
        { label: "Grundbuch", value: eur(r.land_registry) },
        { label: "Makler", value: eur(r.makler) },
        { label: "Gesamtinvestition", value: eur(r.total_investment) },
        { label: "Nebenkostenquote", value: pct(r.ancillary_quota_percent) },
        { label: "Mindest-Eigenkapital", value: eur(r.min_equity) },
      ];
    }
    case "affordability": {
      const r = calc.result;
      return [
        { label: "Max. Monatsrate", value: eurCents(r.max_monthly_payment) },
        { label: "Max. Darlehen", value: eur(r.max_loan) },
        { label: "Eigenkapital", value: eur(r.equity) },
        { label: "Nebenkostenquote", value: pct(r.ancillary_quota_percent) },
      ];
    }
    case "yield_metrics": {
      const r = calc.result;
      return [
        { label: "Jahreskaltmiete", value: eur(r.annual_cold_rent) },
        { label: "Nettorendite", value: pct(r.net_yield_percent) },
        { label: "Kaufpreisfaktor", value: num(r.kaufpreisfaktor) },
      ];
    }
    case "operating_costs": {
      const r = calc.result;
      return [
        { label: "Instandhaltung", value: eur(r.instandhaltung) },
        { label: "Verwaltung", value: eur(r.verwaltung) },
        { label: "Mietausfallwagnis", value: eur(r.mietausfallwagnis) },
      ];
    }
    case "equity_return": {
      const r = calc.result;
      return [
        { label: "Darlehen", value: eur(r.loan) },
        { label: "Kapitaldienst p. a. (Zins + Tilgung)", value: eur(r.annual_debt_service) },
        { label: "Netto-Mietertrag p. a.", value: eur(r.net_operating_income) },
        { label: "Cashflow vor Steuern", value: eur(r.cashflow_before_tax) },
        { label: "Tilgung im 1. Jahr (Vermögensaufbau)", value: eur(r.year1_tilgung) },
        { label: "Rendite inkl. Tilgung", value: pct(r.return_incl_tilgung_percent) },
      ];
    }
  }
}

export interface Segment {
  label: string;
  value: number;
  tone: "ink" | "red" | "green" | "ochre" | "mute";
}

// The proportional bar under the headline figure, for the calculators that split a total.
export function segmentsOf(calc: KnownCalc): Segment[] | null {
  switch (calc.kind) {
    case "annuity": {
      const r = calc.result;
      // identity: total paid = loan repaid + interest, so the loan is what is left after interest
      return [
        { label: "Darlehen (Tilgung)", value: r.total_paid - r.total_interest, tone: "green" },
        { label: "Zinsen", value: r.total_interest, tone: "red" },
      ];
    }
    case "purchase_costs": {
      const r = calc.result;
      return [
        { label: "Grunderwerbsteuer", value: r.grunderwerbsteuer, tone: "ink" },
        { label: "Notar", value: r.notary, tone: "green" },
        { label: "Grundbuch", value: r.land_registry, tone: "ochre" },
        { label: "Makler", value: r.makler, tone: "red" },
      ];
    }
    case "affordability":
      return [
        { label: "Darlehen", value: calc.result.max_loan, tone: "ink" },
        { label: "Eigenkapital", value: calc.result.equity, tone: "green" },
      ];
    case "operating_costs": {
      const r = calc.result;
      return [
        { label: "Instandhaltung", value: r.instandhaltung, tone: "ink" },
        { label: "Verwaltung", value: r.verwaltung, tone: "green" },
        { label: "Mietausfallwagnis", value: r.mietausfallwagnis, tone: "red" },
      ];
    }
    default:
      return null;
  }
}

// Widths in percent that always add up to 100 (zero and negative parts get no width).
export function segmentShares(segments: Segment[]): number[] {
  const positive = segments.map((s) => Math.max(0, s.value));
  const total = positive.reduce((a, b) => a + b, 0);
  return total === 0 ? positive.map(() => 0) : positive.map((v) => (v / total) * 100);
}

// Scale for the yield ruler: whole percent up to at least 8 and above both markers.
export function yieldScaleMax(gross: number, net: number): number {
  return Math.max(8, Math.ceil(Math.max(gross, net) + 1));
}
