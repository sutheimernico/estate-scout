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
      "Cashflow-Rendite vor Steuern",
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
    fireEvent.change(within(form).getByLabelText(/Bundesland/), { target: { value: "NW" } });
    fireEvent.submit(form);
    await waitFor(() => expect(within(form).getByText("Grunderwerbsteuer")).toBeInTheDocument());
  });

  it("offers the 16 Bundesländer as a select, not free text", () => {
    render(<CalcForms />);
    const form = screen.getByRole("heading", { name: "Kaufnebenkosten" }).closest("form")!;
    const select = within(form).getByLabelText(/Bundesland/) as HTMLSelectElement;
    expect(select.tagName).toBe("SELECT");
    expect(select.options).toHaveLength(16);
    expect(select.value).toBe("NI");
  });

  it("starts with visible example values, not placeholders", () => {
    render(<CalcForms />);
    const form = screen.getByRole("heading", { name: "Annuitätendarlehen" }).closest("form")!;
    expect(within(form).getByLabelText(/Darlehensbetrag/)).toHaveValue("300000");
    expect(within(form).getByLabelText(/Sollzins/)).toHaveValue("3,6");
    // optional empty fields carry a hint, not something that looks like a value
    expect(within(form).getByLabelText(/Sondertilgung/)).toHaveAttribute("placeholder", "optional");
  });

  it("sends the Zinsbindung to the API", async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ result: {}, disclaimer: "x" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<CalcForms />);
    const form = screen.getByRole("heading", { name: "Annuitätendarlehen" }).closest("form")!;
    fireEvent.submit(form);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/finance/annuity");
    expect(JSON.parse(init.body as string)).toMatchObject({
      principal: 300000,
      annual_rate_percent: 3.6,
      zinsbindung_years: 10,
    });
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
