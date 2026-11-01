// The six calculators as data: which fields, which defaults, which units. The Rechner renders
// whatever is listed here; the numbers themselves always come from /api/finance/{calc}.

import { parseDecimal } from "./parse";

export interface Field {
  key: string;
  label: string;
  unit?: string; // shown inside the input ("€", "%", "Jahre")
  required?: boolean;
  text?: boolean; // string field (default: number)
  select?: "bundesland"; // rendered as a <select> of the 16 Bundesländer (value = code)
  // Real, visible starting value (not a placeholder): the example scenario of this calculator.
  defaultValue?: string;
}

export interface CalcSpec {
  calc: string;
  title: string;
  blurb: string; // one line under the title in the navigation
  fields: Field[];
}

const SOLLZINS: Field = {
  key: "annual_rate_percent",
  label: "Sollzins",
  unit: "% p. a.",
  required: true,
  defaultValue: "3,6",
};
const TILGUNG: Field = {
  key: "initial_repayment_percent",
  label: "Anfängliche Tilgung",
  unit: "%",
  required: true,
  defaultValue: "2,0",
};
const BUNDESLAND: Field = {
  key: "bundesland",
  label: "Bundesland",
  required: true,
  text: true,
  select: "bundesland",
  defaultValue: "NI",
};

export const SPECS: CalcSpec[] = [
  {
    calc: "annuity",
    title: "Annuitätendarlehen",
    blurb: "Rate, Zinsen, Restschuld",
    fields: [
      { key: "principal", label: "Darlehensbetrag", unit: "€", required: true, defaultValue: "300000" },
      SOLLZINS,
      TILGUNG,
      { key: "annual_sondertilgung", label: "Sondertilgung", unit: "€ / Jahr" },
      { key: "zinsbindung_years", label: "Zinsbindung", unit: "Jahre", defaultValue: "10" },
    ],
  },
  {
    calc: "purchase_costs",
    title: "Kaufnebenkosten",
    blurb: "Steuer, Notar, Makler",
    fields: [
      { key: "purchase_price", label: "Kaufpreis", unit: "€", required: true, defaultValue: "300000" },
      BUNDESLAND,
      { key: "makler_rate_percent", label: "Maklerprovision Käufer", unit: "%" },
    ],
  },
  {
    calc: "affordability",
    title: "Leistbarkeit",
    blurb: "Was liegt im Budget?",
    fields: [
      {
        key: "net_monthly_income",
        label: "Haushaltsnetto",
        unit: "€ / Monat",
        required: true,
        defaultValue: "4000",
      },
      { key: "equity", label: "Eigenkapital", unit: "€", required: true, defaultValue: "60000" },
      SOLLZINS,
      TILGUNG,
      BUNDESLAND,
      { key: "existing_obligations", label: "Bestehende Raten", unit: "€ / Monat" },
      { key: "running_costs_monthly", label: "Laufende Kosten", unit: "€ / Monat" },
    ],
  },
  {
    calc: "yield_metrics",
    title: "Mietrendite",
    blurb: "Brutto, netto, Faktor",
    fields: [
      { key: "purchase_price", label: "Kaufpreis", unit: "€", required: true, defaultValue: "300000" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete",
        unit: "€ / Monat",
        required: true,
        defaultValue: "1200",
      },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten", unit: "€ / Jahr" },
      { key: "ancillary_costs", label: "Kaufnebenkosten", unit: "€" },
    ],
  },
  {
    calc: "operating_costs",
    title: "Bewirtschaftungskosten",
    blurb: "Was die Miete kostet",
    fields: [
      { key: "living_area_sqm", label: "Wohnfläche", unit: "m²", required: true, defaultValue: "100" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete",
        unit: "€ / Monat",
        required: true,
        defaultValue: "1200",
      },
      { key: "units", label: "Wohneinheiten" },
    ],
  },
  {
    calc: "equity_return",
    title: "Cashflow-Rendite vor Steuern",
    blurb: "Rendite auf das Eigenkapital",
    fields: [
      { key: "purchase_price", label: "Kaufpreis", unit: "€", required: true, defaultValue: "300000" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete",
        unit: "€ / Monat",
        required: true,
        defaultValue: "1500",
      },
      { key: "equity", label: "Eigenkapital", unit: "€", required: true, defaultValue: "60000" },
      SOLLZINS,
      TILGUNG,
      { key: "ancillary_costs", label: "Kaufnebenkosten", unit: "€" },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten", unit: "€ / Jahr" },
    ],
  },
];

export function defaultValues(spec: CalcSpec): Record<string, string> {
  return Object.fromEntries(spec.fields.map((f) => [f.key, f.defaultValue ?? ""]));
}

export type BuiltArgs =
  | { ok: true; args: Record<string, unknown> }
  // `missing`: a required field is empty (not an error, the user is still typing);
  // `errors`: fields whose text is not a number (shown on the field).
  | { ok: false; missing: boolean; errors: Record<string, string> };

export function buildArgs(spec: CalcSpec, values: Record<string, string>): BuiltArgs {
  const args: Record<string, unknown> = {};
  const errors: Record<string, string> = {};
  let missing = false;
  for (const f of spec.fields) {
    const raw = (values[f.key] ?? "").trim();
    if (!raw) {
      if (f.required) missing = true;
      continue;
    }
    if (f.text) {
      args[f.key] = raw;
      continue;
    }
    const n = parseDecimal(raw);
    if (n === null) errors[f.key] = `${f.label}: keine gültige Zahl.`;
    else args[f.key] = n;
  }
  if (missing || Object.keys(errors).length > 0) return { ok: false, missing, errors };
  return { ok: true, args };
}
