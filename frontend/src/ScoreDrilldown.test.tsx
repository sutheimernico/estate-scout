import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { type ScoreReport } from "./api";
import { ScoreDrilldown } from "./ScoreDrilldown";

const partialReport: ScoreReport = {
  total: 73,
  subscores: [
    {
      name: "yield",
      value: null,
      weight: 0.4,
      detail: {},
      reason: "rent_missing",
    },
    {
      name: "price",
      value: null,
      weight: 0.4,
      detail: {},
      reason: "provider_missing",
    },
    {
      name: "region",
      value: 73,
      weight: 0.2,
      detail: { population_trend_pct: 0.5, vacancy_rate_pct: 3.0 },
      reason: null,
    },
  ],
  weights_used: { region: 1 },
  confidence: 0.5,
  inputs_available: 2,
  inputs_expected: 4,
  reasons: { yield: "rent_missing", price: "provider_missing" },
  as_of: "2026-09-20",
};

describe("ScoreDrilldown", () => {
  it("renders the total, the available block and its renormalized weight", () => {
    render(<ScoreDrilldown report={partialReport} />);
    // the region block also reads 73/100 (it carries the whole weight) — pin the headline
    expect(screen.getByText("73/100", { selector: ".score-total" })).toBeInTheDocument();
    expect(screen.getByText("Lage")).toBeInTheDocument();
    expect(screen.getByText("100 %")).toBeInTheDocument(); // region carries the full weight
    expect(screen.getByText(/Datenlage 2\/4/)).toBeInTheDocument();
  });

  it("lists every missing block with its honest reason", () => {
    render(<ScoreDrilldown report={partialReport} />);
    expect(screen.getByText("Nicht verfügbar")).toBeInTheDocument();
    expect(screen.getByText("Rendite: keine Kaltmiete angegeben")).toBeInTheDocument();
    expect(screen.getByText("Preisniveau: Datenquelle fehlt")).toBeInTheDocument();
  });

  it("shows 'kein Score' instead of a fabricated zero when nothing is computable", () => {
    render(
      <ScoreDrilldown
        report={{
          ...partialReport,
          total: null,
          subscores: partialReport.subscores.map((s) => ({
            ...s,
            value: null,
            reason: s.reason ?? "no_data",
          })),
          weights_used: {},
          confidence: 0,
          inputs_available: 0,
        }}
      />,
    );
    expect(screen.getByText("Kein Score")).toBeInTheDocument();
    expect(screen.getByText("Lage: keine Daten für dieses Objekt")).toBeInTheDocument();
  });
});
