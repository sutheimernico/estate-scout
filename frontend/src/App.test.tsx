import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AmortizationTable } from "./AmortizationTable";
import { App } from "./App";
import { CalcResultCard } from "./CalcResultCard";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } }),
    ),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// The Listings pane mounts with the App and fetches immediately; awaiting its settled
// empty state keeps that async update inside act() instead of leaking after the test.
async function renderApp() {
  render(<App />);
  await screen.findByText(/Noch keine Objekte gespeichert/);
}

describe("App", () => {
  it("renders the header subtitle and the disclaimer", async () => {
    await renderApp();
    expect(screen.getByText(/Lokaler Immobilien-Assistent/)).toBeInTheDocument();
    expect(screen.getByText(/keine Steuer/i)).toBeInTheDocument();
  });

  it("shows an empty-state prompt before any message", async () => {
    await renderApp();
    expect(screen.getByText(/Frag mich etwas zu Kauf/)).toBeInTheDocument();
  });
});

describe("AmortizationTable", () => {
  it("formats the summary and schedule numbers", () => {
    render(
      <AmortizationTable
        result={{
          monthly_payment: 1400,
          total_interest: 181209.86,
          total_paid: 481209.86,
          months_to_payoff: 344,
          years_to_payoff: 28.7,
          remaining_debt_by_year: [{ year: 1, remaining_debt: 293900 }],
          zinsbindung_years: 10,
          restschuld_after_zinsbindung: 215432.1,
          interest_during_zinsbindung: 98765.4,
        }}
      />,
    );
    expect(screen.getByText("Annuitätendarlehen")).toBeInTheDocument();
    expect(screen.getByText("1.400,00 €")).toBeInTheDocument(); // computed rate keeps its cents
    expect(screen.getByText("28,7 Jahre")).toBeInTheDocument(); // de-DE decimal comma
    expect(screen.getByText("Restschuld nach 10 Jahren Zinsbindung")).toBeInTheDocument();
    expect(screen.getByText("215.432 €")).toBeInTheDocument();
  });

  it("omits the Zinsbindung rows when none was requested", () => {
    render(
      <AmortizationTable
        result={{
          monthly_payment: 1400,
          total_interest: 1,
          total_paid: 2,
          months_to_payoff: 12,
          years_to_payoff: 1,
          remaining_debt_by_year: [{ year: 1, remaining_debt: 0 }],
        }}
      />,
    );
    expect(screen.queryByText(/Zinsbindung/)).toBeNull();
  });
});

describe("CalcResultCard", () => {
  it("renders a purchase-costs breakdown", () => {
    render(
      <CalcResultCard
        calc={{
          kind: "purchase_costs",
          result: {
            bundesland: "NW",
            grunderwerbsteuer: 19500,
            notary: 4500,
            land_registry: 1500,
            makler: 10710,
            total_ancillary: 36210,
            total_investment: 336210,
            ancillary_quota_percent: 12.07,
            min_equity: 36210,
          },
        }}
      />,
    );
    expect(screen.getByText("Kaufnebenkosten (Nordrhein-Westfalen)")).toBeInTheDocument();
    expect(screen.getByText(/19\.500/)).toBeInTheDocument();
  });

  it("renders an equity-return card", () => {
    render(
      <CalcResultCard
        calc={{
          kind: "equity_return",
          result: {
            loan: 270000,
            annual_debt_service: 15120,
            net_operating_income: 15600,
            cashflow_before_tax: 480,
            cash_on_cash_percent: 0.8,
            year1_tilgung: 5460,
            return_incl_tilgung_percent: 9.9,
          },
        }}
      />,
    );
    expect(screen.getByText("Cashflow-Rendite vor Steuern (Jahr 1)")).toBeInTheDocument();
    expect(screen.getByText("0,8 %")).toBeInTheDocument();
    expect(screen.getByText("Rendite inkl. Tilgung")).toBeInTheDocument();
  });
});

describe("Tabs", () => {
  it("switches to the Rechner tab", async () => {
    await renderApp();
    fireEvent.click(screen.getByRole("tab", { name: "Rechner" }));
    expect(screen.getByRole("heading", { name: "Annuitätendarlehen" })).toBeInTheDocument();
  });
});
