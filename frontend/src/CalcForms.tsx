// Direct, deterministic calculator forms against /api/finance/{calc} — no LLM involved.
// German decimal commas are accepted ("3,6" → 3.6).

import { type FormEvent, useState } from "react";

import { finance, toKnownCalc } from "./api";
import { CalcResultCard } from "./CalcResultCard";

interface Field {
  key: string;
  label: string;
  required?: boolean;
  text?: boolean; // string field (default: number)
  placeholder?: string;
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
      { key: "principal", label: "Darlehensbetrag (€)", required: true, placeholder: "300000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, placeholder: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        placeholder: "2,0",
      },
      { key: "annual_sondertilgung", label: "Sondertilgung (€/Jahr, optional)" },
    ],
  },
  {
    calc: "purchase_costs",
    title: "Kaufnebenkosten",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, placeholder: "300000" },
      {
        key: "bundesland",
        label: "Bundesland",
        required: true,
        text: true,
        placeholder: "Niedersachsen",
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
        placeholder: "4000",
      },
      { key: "equity", label: "Eigenkapital (€)", required: true, placeholder: "60000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, placeholder: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        placeholder: "2,0",
      },
      { key: "bundesland", label: "Bundesland", required: true, text: true, placeholder: "NRW" },
      { key: "existing_obligations", label: "Bestehende Raten (€/Monat, optional)" },
      { key: "running_costs_monthly", label: "Laufende Kosten (€/Monat, optional)" },
    ],
  },
  {
    calc: "yield_metrics",
    title: "Mietrendite",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, placeholder: "300000" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete (€/Monat)",
        required: true,
        placeholder: "1200",
      },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten (€/Jahr, optional)" },
      { key: "ancillary_costs", label: "Kaufnebenkosten (€, optional)" },
    ],
  },
  {
    calc: "operating_costs",
    title: "Bewirtschaftungskosten",
    fields: [
      { key: "living_area_sqm", label: "Wohnfläche (m²)", required: true, placeholder: "100" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete (€/Monat)",
        required: true,
        placeholder: "1200",
      },
      { key: "units", label: "Wohneinheiten (optional)" },
    ],
  },
  {
    calc: "equity_return",
    title: "Eigenkapitalrendite",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, placeholder: "300000" },
      {
        key: "monthly_cold_rent",
        label: "Kaltmiete (€/Monat)",
        required: true,
        placeholder: "1500",
      },
      { key: "equity", label: "Eigenkapital (€)", required: true, placeholder: "60000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, placeholder: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        placeholder: "2,0",
      },
      { key: "ancillary_costs", label: "Kaufnebenkosten (€, optional)" },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten (€/Jahr, optional)" },
    ],
  },
];

function CalcForm({ spec }: { spec: FormSpec }) {
  const [values, setValues] = useState<Record<string, string>>({});
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
          <input
            value={values[f.key] ?? ""}
            onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
            placeholder={f.placeholder}
            inputMode={f.text ? undefined : "decimal"}
          />
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
      {FORMS.map((f) => (
        <CalcForm key={f.calc} spec={f} />
      ))}
    </div>
  );
}
