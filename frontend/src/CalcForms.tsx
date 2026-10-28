// Direct, deterministic calculator forms against /api/finance/{calc} — no LLM involved.
// German decimal commas are accepted ("3,6" → 3.6).

import { type FormEvent, useState } from "react";

import { finance, toKnownCalc } from "./api";
import { CalcResultCard } from "./CalcResultCard";
import { BUNDESLAENDER } from "./labels";

interface Field {
  key: string;
  label: string;
  required?: boolean;
  text?: boolean; // string field (default: number)
  select?: "bundesland"; // rendered as a <select> of the 16 Bundesländer (value = code)
  // Real, visible starting value (not a placeholder): the example scenario of this calculator.
  defaultValue?: string;
}

interface FormSpec {
  calc: string;
  title: string;
  fields: Field[];
}

const FORMS: FormSpec[] = [
  {
    calc: "annuity",
    title: "Annuitätendarlehen",
    fields: [
      { key: "principal", label: "Darlehensbetrag (€)", required: true, defaultValue: "300000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, defaultValue: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        defaultValue: "2,0",
      },
      { key: "annual_sondertilgung", label: "Sondertilgung (€/Jahr, optional)" },
      { key: "zinsbindung_years", label: "Zinsbindung (Jahre, optional)", defaultValue: "10" },
    ],
  },
  {
    calc: "purchase_costs",
    title: "Kaufnebenkosten",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, defaultValue: "300000" },
      {
        key: "bundesland",
        label: "Bundesland",
        required: true,
        text: true, select: "bundesland", defaultValue: "NI",
      },
      { key: "makler_rate_percent", label: "Maklerprovision Käufer (%, optional)" },
    ],
  },
  {
    calc: "affordability",
    title: "Leistbarkeit",
    fields: [
      {
        key: "net_monthly_income",
        label: "Haushaltsnetto (€/Monat)",
        required: true,
        defaultValue: "4000",
      },
      { key: "equity", label: "Eigenkapital (€)", required: true, defaultValue: "60000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, defaultValue: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        defaultValue: "2,0",
      },
      { key: "bundesland", label: "Bundesland", required: true, text: true, select: "bundesland", defaultValue: "NI", },
      { key: "existing_obligations", label: "Bestehende Raten (€/Monat, optional)" },
      { key: "running_costs_monthly", label: "Laufende Kosten (€/Monat, optional)" },
    ],
  },
  {
    calc: "yield_metrics",
    title: "Mietrendite",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, defaultValue: "300000" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete (€/Monat)",
        required: true,
        defaultValue: "1200",
      },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten (€/Jahr, optional)" },
      { key: "ancillary_costs", label: "Kaufnebenkosten (€, optional)" },
    ],
  },
  {
    calc: "operating_costs",
    title: "Bewirtschaftungskosten",
    fields: [
      { key: "living_area_sqm", label: "Wohnfläche (m²)", required: true, defaultValue: "100" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete (€/Monat)",
        required: true,
        defaultValue: "1200",
      },
      { key: "units", label: "Wohneinheiten (optional)" },
    ],
  },
  {
    calc: "equity_return",
    title: "Cashflow-Rendite vor Steuern",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, defaultValue: "300000" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete (€/Monat)",
        required: true,
        defaultValue: "1500",
      },
      { key: "equity", label: "Eigenkapital (€)", required: true, defaultValue: "60000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, defaultValue: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        defaultValue: "2,0",
      },
      { key: "ancillary_costs", label: "Kaufnebenkosten (€, optional)" },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten (€/Jahr, optional)" },
    ],
  },
];

function CalcForm({ spec }: { spec: FormSpec }) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(spec.fields.map((f) => [f.key, f.defaultValue ?? ""])),
  );
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const args: Record<string, unknown> = {};
    for (const f of spec.fields) {
      const raw = (values[f.key] ?? "").trim();
      if (!raw) {
        if (f.required) {
          setError(`${f.label} fehlt.`);
          return;
        }
        continue;
      }
      if (f.text) {
        args[f.key] = raw;
      } else {
        const n = Number(raw.replace(",", "."));
        if (Number.isNaN(n)) {
          setError(`${f.label}: keine gültige Zahl.`);
          return;
        }
        args[f.key] = n;
      }
    }
    setBusy(true);
    try {
      const resp = await finance(spec.calc, args);
      setResult(resp.result);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const known = result ? toKnownCalc(spec.calc, result) : null;

  return (
    <form className="card-form" onSubmit={onSubmit}>
      <h3>{spec.title}</h3>
      {spec.fields.map((f) => (
        <label key={f.key}>
          {f.label}
          {f.select === "bundesland" ? (
            <select
              value={values[f.key] ?? ""}
              onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
            >
              {BUNDESLAENDER.map((b) => (
                <option key={b.code} value={b.code}>
                  {b.name}
                </option>
              ))}
            </select>
          ) : (
            <input
              value={values[f.key] ?? ""}
              onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
              placeholder={f.required ? undefined : "optional"}
              inputMode={f.text ? undefined : "decimal"}
            />
          )}
        </label>
      ))}
      <button type="submit" disabled={busy}>
        {busy ? "Rechnet …" : "Berechnen"}
      </button>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {known && <CalcResultCard calc={known} />}
    </form>
  );
}

export function CalcForms() {
  return (
    <div className="cards">
      <p className="empty">
        Vorbelegt mit Beispielwerten — ersetze sie durch deine eigenen Zahlen.
      </p>
      {FORMS.map((f) => (
        <CalcForm key={f.calc} spec={f} />
      ))}
    </div>
  );
}
