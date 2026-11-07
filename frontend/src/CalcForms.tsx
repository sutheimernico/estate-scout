// The Rechner: pick a calculator, change the inputs, watch the result recalculate.
// Direct and deterministic against /api/finance/{calc} — no LLM involved.
// German decimal commas and thousands dots are accepted ("3,6", "300.000").

import { useEffect, useRef, useState } from "react";

import { type KnownCalc } from "./api";
import { buildArgs, type CalcSpec, defaultValues, type Field, SPECS } from "./calcSpecs";
import { heroOf } from "./calcView";
import { CalcResult } from "./CalcResult";
import { CountUp } from "./CountUp";
import { FieldShell } from "./FieldShell";
import { formatInput } from "./format";
import { BUNDESLAENDER } from "./labels";
import { useLiveCalc } from "./useLiveCalc";

function FieldInput({
  field,
  value,
  error,
  onChange,
}: {
  field: Field;
  value: string;
  error?: string;
  onChange: (v: string) => void;
}) {
  return (
    <FieldShell
      label={field.label}
      optional={!field.required}
      unit={field.unit}
      error={error}
    >
      {(id) =>
        field.select === "bundesland" ? (
          <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
            {BUNDESLAENDER.map((b) => (
              <option key={b.code} value={b.code}>
                {b.name}
              </option>
            ))}
          </select>
        ) : (
          <input
            id={id}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onBlur={field.text ? undefined : (e) => onChange(formatInput(e.target.value))}
            placeholder={field.placeholder}
            inputMode={field.text ? undefined : "decimal"}
            aria-invalid={error ? true : undefined}
            autoComplete="off"
          />
        )
      }
    </FieldShell>
  );
}

// Phone layout: the result sits below the whole form, so a figure that follows the thumb keeps
// the effect of every keystroke in sight. Opaque on purpose (never see-through over text), and
// it steps aside while the real result is on screen.
function ResultStrip({ calc, target }: { calc: KnownCalc; target: React.RefObject<HTMLElement> }) {
  const [away, setAway] = useState(false);
  useEffect(() => {
    const el = target.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(([entry]) => setAway(!entry.isIntersecting));
    io.observe(el);
    return () => io.disconnect();
  }, [target]);
  const hero = heroOf(calc);
  return (
    <button
      type="button"
      className={away ? "result-strip on" : "result-strip"}
      tabIndex={away ? 0 : -1}
      aria-hidden={away ? undefined : true}
      onClick={() => target.current?.scrollIntoView?.({ behavior: "smooth", block: "start" })}
    >
      <span className="result-strip-label">{hero.label}</span>
      <span className="result-strip-num num">
        <CountUp value={hero.value} format={hero.format} duration={300} />
      </span>
      <span className="result-strip-go" aria-hidden="true">Ergebnis</span>
    </button>
  );
}

function Workbench({
  spec,
  values,
  onChange,
}: {
  spec: CalcSpec;
  values: Record<string, string>;
  onChange: (key: string, v: string) => void;
}) {
  const built = buildArgs(spec, values);
  const live = useLiveCalc(spec, built);
  const errors = built.ok ? {} : built.errors;
  const incomplete = !built.ok;
  const hasErrors = !built.ok && Object.keys(built.errors).length > 0;
  const outputRef = useRef<HTMLDivElement>(null);

  return (
    <>
      <form className="inputs sheet" onSubmit={(e) => e.preventDefault()} aria-label={spec.title}>
        <h3>{spec.title}</h3>
        <p className="inputs-note">Vorbelegt mit einem Beispielfall, Nebenkosten und Bewirtschaftung wie in den Rechnern gleichen Namens. Das Ergebnis rechnet beim Tippen mit.</p>
        <div className="inputs-grid">
          {spec.fields.map((f) => (
            <FieldInput
              key={f.key}
              field={f}
              value={values[f.key] ?? ""}
              error={errors[f.key]}
              onChange={(v) => onChange(f.key, v)}
            />
          ))}
        </div>
      </form>

      <div ref={outputRef} className={live.loading ? "output loading" : "output"} aria-live="polite">
        {live.error && (
          <div className="notice error" role="alert">
            {live.error}
          </div>
        )}
        {incomplete && !live.calc && (
          <p className="output-empty">
            {hasErrors
              ? "Korrigiere die markierten Felder, dann erscheint das Ergebnis."
              : "Trage die Pflichtfelder ein, dann erscheint das Ergebnis."}
          </p>
        )}
        {live.calc && (
          <div className="sheet result-sheet">
            <CalcResult calc={live.calc} args={live.args ?? undefined} />
          </div>
        )}
        {!live.calc && !incomplete && !live.error && <div className="output-skeleton" aria-hidden="true" />}
      </div>
      {live.calc && <ResultStrip calc={live.calc} target={outputRef} />}
    </>
  );
}

export function CalcForms() {
  const [selected, setSelected] = useState(SPECS[0].calc);
  // Values live here, not in the workbench, so switching calculators keeps what was typed.
  const [values, setValues] = useState<Record<string, Record<string, string>>>(() =>
    Object.fromEntries(SPECS.map((s) => [s.calc, defaultValues(s)])),
  );
  const spec = SPECS.find((s) => s.calc === selected)!;

  return (
    <div className="rechner">
      <nav className="calc-nav" aria-label="Rechner">
        {SPECS.map((s, i) => (
          <button
            key={s.calc}
            type="button"
            className="calc-nav-item reveal"
            style={{ ["--i" as string]: i }}
            aria-current={s.calc === selected ? "true" : undefined}
            onClick={() => setSelected(s.calc)}
          >
            <span className="calc-nav-title">{s.title}</span>
            <span className="calc-nav-blurb">{s.blurb}</span>
          </button>
        ))}
      </nav>
      <Workbench
        key={spec.calc}
        spec={spec}
        values={values[spec.calc]}
        onChange={(k, v) =>
          setValues((all) => ({ ...all, [spec.calc]: { ...all[spec.calc], [k]: v } }))
        }
      />
    </div>
  );
}
