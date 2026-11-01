import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CalcForms } from "./CalcForms";

afterEach(() => {
  vi.unstubAllGlobals();
});

const purchaseCosts = {
  bundesland: "NI",
  grunderwerbsteuer: 19500,
  notary: 4500,
  land_registry: 1500,
  makler: 10710,
  total_ancillary: 36210,
  total_investment: 336210,
  ancillary_quota_percent: 12.07,
  min_equity: 36210,
};

function stubFetch(result: unknown = purchaseCosts) {
  const mock = vi.fn(
    async () =>
      new Response(JSON.stringify({ result, disclaimer: "x" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
  );
  vi.stubGlobal("fetch", mock);
  return mock;
}

const pick = (name: RegExp) => fireEvent.click(screen.getByRole("button", { name }));

describe("CalcForms", () => {
  it("offers all six calculators in a list", () => {
    stubFetch();
    render(<CalcForms />);
    const nav = screen.getByRole("navigation", { name: "Rechner" });
    for (const title of [
      "Annuitätendarlehen",
      "Kaufnebenkosten",
      "Leistbarkeit",
      "Mietrendite",
      "Bewirtschaftungskosten",
      "Cashflow-Rendite vor Steuern",
    ]) {
      expect(within(nav).getByRole("button", { name: new RegExp(title) })).toBeInTheDocument();
    }
  });

  it("calculates on its own when a calculator opens and shows the result", async () => {
    stubFetch();
    render(<CalcForms />);
    pick(/Kaufnebenkosten/);
    expect((await screen.findAllByText("Grunderwerbsteuer")).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: "Kaufnebenkosten", level: 4 })).toBeInTheDocument();
    expect(screen.getByText("Niedersachsen", { selector: ".tag" })).toBeInTheDocument(); // never the code NI
  });

  it("offers the 16 Bundesländer as a select, not free text", () => {
    stubFetch();
    render(<CalcForms />);
    pick(/Kaufnebenkosten/);
    const select = screen.getByLabelText(/Bundesland/) as HTMLSelectElement;
    expect(select.tagName).toBe("SELECT");
    expect(select.options).toHaveLength(16);
    expect(select.value).toBe("NI");
  });

  it("starts with visible example values, not placeholders", () => {
    stubFetch();
    render(<CalcForms />);
    expect(screen.getByLabelText(/Darlehensbetrag/)).toHaveValue("300000");
    expect(screen.getByLabelText(/Sollzins/)).toHaveValue("3,6");
    // optional empty fields carry a hint, not something that looks like a value
    expect(screen.getByLabelText(/Sondertilgung/)).toHaveAttribute("placeholder", "optional");
  });

  it("sends the Zinsbindung to the API without any submit click", async () => {
    const fetchMock = stubFetch({});
    render(<CalcForms />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/finance/annuity");
    expect(JSON.parse(init.body as string)).toMatchObject({
      principal: 300000,
      annual_rate_percent: 3.6,
      zinsbindung_years: 10,
    });
  });

  it("keeps what was typed when switching calculators and back", () => {
    stubFetch();
    render(<CalcForms />);
    fireEvent.change(screen.getByLabelText(/Darlehensbetrag/), { target: { value: "250000" } });
    pick(/Mietrendite/);
    pick(/Annuitätendarlehen/);
    expect(screen.getByLabelText(/Darlehensbetrag/)).toHaveValue("250000");
  });

  it("rejects a non-numeric value with a German error and does not call the API for it", async () => {
    const fetchMock = stubFetch({});
    render(<CalcForms />);
    pick(/Mietrendite/);
    fireEvent.change(screen.getByLabelText(/Kaufpreis/), { target: { value: "abc" } });
    expect(await screen.findByRole("alert")).toHaveTextContent(/keine gültige Zahl/);
    const callsAfterInvalid = fetchMock.mock.calls.length;
    await new Promise((r) => setTimeout(r, 450)); // past the debounce
    expect(fetchMock.mock.calls.length).toBe(callsAfterInvalid);
  });
});
