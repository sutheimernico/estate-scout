import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CalcForms } from "./CalcForms";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CalcForms", () => {
  it("renders one form per calculator", () => {
    render(<CalcForms />);
    for (const title of [
      "Annuitätendarlehen",
      "Kaufnebenkosten",
      "Leistbarkeit",
      "Mietrendite",
      "Bewirtschaftungskosten",
      "Eigenkapitalrendite",
    ]) {
      expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    }
  });

  it("submits the Kaufnebenkosten form and renders the result card", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
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
              disclaimer: "x",
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
      ),
    );
    render(<CalcForms />);
    const form = screen.getByRole("heading", { name: "Kaufnebenkosten" }).closest("form")!;
    fireEvent.change(within(form).getByLabelText(/Kaufpreis/), { target: { value: "300000" } });
    fireEvent.change(within(form).getByLabelText(/Bundesland/), { target: { value: "NRW" } });
    fireEvent.submit(form);
    await waitFor(() => expect(within(form).getByText("Grunderwerbsteuer")).toBeInTheDocument());
  });

  it("rejects a non-numeric value with a German error", async () => {
    render(<CalcForms />);
    const form = screen.getByRole("heading", { name: "Mietrendite" }).closest("form")!;
    fireEvent.change(within(form).getByLabelText(/Kaufpreis/), { target: { value: "abc" } });
    fireEvent.change(within(form).getByLabelText(/Kaltmiete/), { target: { value: "1200" } });
    fireEvent.submit(form);
    await waitFor(() =>
      expect(within(form).getByRole("alert")).toHaveTextContent(/keine gültige Zahl/),
    );
  });
});
