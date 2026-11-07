// One calculator result, drawn as a dimensioned figure: headline number on a dimension line,
// a picture where the result has a shape (curve, split, scale), then the remaining facts.
// Used by the Rechner and by the chat, so a number looks the same wherever it appears.

import { AmortizationTable } from "./AmortizationTable";
import { type KnownCalc } from "./api";
import { BarScale, SplitBar } from "./Bars";
import { factsOf, heroOf, segmentsOf, titleOf, yieldScaleMax } from "./calcView";
import { CountUp } from "./CountUp";
import { DimLine } from "./DimLine";
import { duration, eur, pct } from "./format";
import { RestschuldChart } from "./RestschuldChart";

function Picture({ calc, args, compact }: { calc: KnownCalc; args?: Record<string, unknown>; compact?: boolean }) {
  if (calc.kind === "annuity") {
    const r = calc.result;
    const principal = typeof args?.principal === "number" ? args.principal : undefined;
    return (
      <>
        <RestschuldChart
          series={r.remaining_debt_by_year}
          principal={principal}
          zinsbindungYears={r.zinsbindung_years}
          restschuld={r.restschuld_after_zinsbindung}
          payoffYears={r.years_to_payoff}
          compact={compact}
        />
        <SplitBar segments={segmentsOf(calc)!} cents />
      </>
    );
  }
  if (calc.kind === "yield_metrics") {
    const { gross_yield_percent: gross, net_yield_percent: net } = calc.result;
    const max = yieldScaleMax(gross, net);
    const ticks = Array.from({ length: max + 1 }, (_, i) => i)
      .filter((i) => i % 2 === 0)
      .map((i) => ({ value: i, label: `${i} %` }));
    return (
      <BarScale
        max={max}
        ticks={ticks}
        rows={[
          { label: "Brutto", value: gross, display: pct(gross), tone: "ink" },
          { label: "Netto", value: net, display: pct(net), tone: "green" },
        ]}
      />
    );
  }
  if (calc.kind === "equity_return") {
    const r = calc.result;
    const max = Math.max(r.net_operating_income, r.annual_debt_service, Math.abs(r.cashflow_before_tax));
    return (
      <BarScale
        max={max}
        rows={[
          { label: "Netto-Mietertrag", value: r.net_operating_income, display: eur(r.net_operating_income), tone: "green" },
          { label: "Kapitaldienst", value: r.annual_debt_service, display: eur(r.annual_debt_service), tone: "ink" },
          { label: "Cashflow", value: r.cashflow_before_tax, display: eur(r.cashflow_before_tax), tone: "ochre" },
        ]}
      />
    );
  }
  const segments = segmentsOf(calc);
  return segments ? <SplitBar segments={segments} /> : null;
}

export function CalcResult({
  calc,
  args,
  compact = false,
}: {
  calc: KnownCalc;
  args?: Record<string, unknown>;
  compact?: boolean;
}) {
  const { title, context } = titleOf(calc);
  const hero = heroOf(calc);
  const facts = factsOf(calc);
  return (
    <section className={compact ? "result compact" : "result"} aria-label={title}>
      <header className="result-head">
        {/* the calculator's name already stands in the navigation and above the form */}
        <h4 className={compact ? undefined : "sr-only"}>{title}</h4>
        {context && <span className="tag">{context}</span>}
      </header>
      <div className="hero">
        <span className="hero-label">{hero.label}</span>
        <div className={`hero-num num${hero.value < 0 ? " negative" : ""}`}>
          <CountUp value={hero.value} format={hero.format} />
        </div>
        <DimLine>{hero.unit}</DimLine>
      </div>
      <Picture calc={calc} args={args} compact={compact} />
      <dl className="facts">
        {facts.map((f, i) => (
          <div className="fact reveal" key={f.label} style={{ ["--i" as string]: i }}>
            <dt>{f.label}</dt>
            <dd className="num">{f.value}</dd>
          </div>
        ))}
      </dl>
      {calc.kind === "annuity" && (
        <details className="plan">
          <summary>
            Tilgungsplan nach Jahren <span className="tag">{duration(calc.result.years_to_payoff)}</span>
          </summary>
          <AmortizationTable result={calc.result} />
        </details>
      )}
    </section>
  );
}
