// The six calculators as data: which fields, which defaults, which units. The Rechner renders
// whatever is listed here; the numbers themselves always come from /api/finance/{calc}.

import { parseDecimal } from "./parse";

export interface Field {
  key: string;
  label: string;
  unit?: string; // shown inside the input ("€", "%", "Jahre")
  required?: boolean;
  text?: boolean; // string field (default: number)
  positive?: boolean; // must be greater than 0 (other numbers only have to be >= 0)
  select?: "bundesland"; // rendered as a <select> of the 16 Bundesländer (value = code)
  // Real, visible starting value (not a placeholder): the example scenario of this calculator.
  defaultValue?: string;
  // Words for an empty optional field ("keine"); never something that could pass for a value.
  placeholder?: string;
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
  positive: true,
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
      { key: "principal", positive: true, label: "Darlehensbetrag", unit: "€", required: true, defaultValue: "300.000" },
      SOLLZINS,
      TILGUNG,
      { key: "annual_sondertilgung", label: "Sondertilgung", unit: "€ / Jahr", placeholder: "keine" },
      { key: "zinsbindung_years", positive: true, label: "Zinsbindung", unit: "Jahre", defaultValue: "10" },
    ],
  },
  {
    calc: "purchase_costs",
    title: "Kaufnebenkosten",
    blurb: "Steuer, Notar, Makler",
    fields: [
      { key: "purchase_price", positive: true, label: "Kaufpreis", unit: "€", required: true, defaultValue: "300.000" },
      BUNDESLAND,
      { key: "makler_rate_percent", label: "Maklerprovision Käufer", unit: "%", defaultValue: "3,57" },
    ],
  },
  {
    calc: "affordability",
    title: "Leistbarkeit",
    blurb: "Was liegt im Budget?",
    fields: [
      {
        key: "net_monthly_income", positive: true,
        label: "Haushaltsnetto",
        unit: "€ / Monat",
        required: true,
        defaultValue: "4.000",
      },
      { key: "equity", label: "Eigenkapital", unit: "€", required: true, defaultValue: "60.000" },
      SOLLZINS,
      TILGUNG,
      BUNDESLAND,
      { key: "existing_obligations", label: "Bestehende Raten", unit: "€ / Monat", placeholder: "keine" },
      { key: "running_costs_monthly", label: "Laufende Kosten", unit: "€ / Monat", placeholder: "keine" },
    ],
  },
  {
    calc: "yield_metrics",
    title: "Mietrendite",
    blurb: "Brutto, netto, Faktor",
    fields: [
      { key: "purchase_price", positive: true, label: "Kaufpreis", unit: "€", required: true, defaultValue: "300.000" },
      {
        key: "monthly_cold_rent", positive: true,
        label: "Kaltmiete",
        unit: "€ / Monat",
        required: true,
        defaultValue: "1.200",
      },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten", unit: "€ / Jahr", defaultValue: "1.838" },
      { key: "ancillary_costs", label: "Kaufnebenkosten", unit: "€", defaultValue: "31.710" },
    ],
  },
  {
    calc: "operating_costs",
    title: "Bewirtschaftungskosten",
    blurb: "Was die Miete kostet",
    fields: [
      { key: "living_area_sqm", positive: true, label: "Wohnfläche", unit: "m²", required: true, defaultValue: "100" },
      {
        key: "monthly_cold_rent", positive: true,
        label: "Kaltmiete",
        unit: "€ / Monat",
        required: true,
        defaultValue: "1.200",
      },
      { key: "units", positive: true, label: "Wohneinheiten", defaultValue: "1" },
    ],
  },
  {
    calc: "equity_return",
    title: "Cashflow-Rendite vor Steuern",
    blurb: "Rendite auf das Eigenkapital",
    fields: [
      { key: "purchase_price", positive: true, label: "Kaufpreis", unit: "€", required: true, defaultValue: "300.000" },
      {
        key: "monthly_cold_rent", positive: true,
        label: "Kaltmiete",
        unit: "€ / Monat",
        required: true,
        defaultValue: "1.500",
      },
      { key: "equity", label: "Eigenkapital", unit: "€", required: true, defaultValue: "60.000" },
      SOLLZINS,
      TILGUNG,
      { key: "ancillary_costs", label: "Kaufnebenkosten", unit: "€", defaultValue: "31.710" },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten", unit: "€ / Jahr", defaultValue: "1.910" },
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
    else if (f.positive && n <= 0) errors[f.key] = `${f.label}: bitte eine Zahl größer 0 eintragen.`;
    else if (n < 0) errors[f.key] = `${f.label}: darf nicht negativ sein.`;
    else args[f.key] = n;
  }
  if (missing || Object.keys(errors).length > 0) return { ok: false, missing, errors };
  return { ok: true, args };
}
