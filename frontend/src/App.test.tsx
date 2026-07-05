import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AmortizationTable } from "./AmortizationTable";
import { App } from "./App";

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
