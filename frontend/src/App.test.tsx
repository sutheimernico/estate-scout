import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AmortizationTable } from "./AmortizationTable";
import { App } from "./App";
import { CalcResultCard } from "./CalcResultCard";

describe("App", () => {
  it("renders the header subtitle and the disclaimer", () => {
    render(<App />);
    expect(screen.getByText(/Lokaler Immobilien-Assistent/)).toBeInTheDocument();
    expect(screen.getByText(/keine Steuer/i)).toBeInTheDocument();
  });

  it("shows an empty-state prompt before any message", () => {
    render(<App />);
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
          years_to_payoff: 28.7,
          remaining_debt_by_year: [{ year: 1, remaining_debt: 293900 }],
        }}
      />,
    );
    expect(screen.getByText("Annuitätendarlehen")).toBeInTheDocument();
    expect(screen.getByText(/1\.400/)).toBeInTheDocument(); // de-DE currency formatting
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
    expect(screen.getByText(/Kaufnebenkosten/)).toBeInTheDocument();
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
          },
        }}
      />,
    );
    expect(screen.getByText("Eigenkapitalrendite (Jahr 1)")).toBeInTheDocument();
    expect(screen.getByText("0,8 %")).toBeInTheDocument();
  });
});
