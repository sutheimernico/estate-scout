import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Listings } from "./Listings";

afterEach(() => {
  vi.unstubAllGlobals();
});

const oneListing = [
  {
    id: 1,
    price: 300000,
    living_area_sqm: 100,
    bundesland: "NI",
    plz: "",
    ort: "Lingen",
    rooms: 3,
    year_built: 1995,
    object_type: "wohnung",
    features: [],
    source_url: "",
    price_per_sqm: 3000,
    enrichment: null,
    score: null,
  },
];

const scoreReport = {
  total: 59,
  subscores: [
    { name: "yield", value: 67, weight: 0.4, detail: {}, reason: null },
    { name: "price", value: 43, weight: 0.4, detail: {}, reason: null },
    { name: "region", value: 73, weight: 0.2, detail: {}, reason: null },
  ],
  weights_used: { yield: 0.4, price: 0.4, region: 0.2 },
  confidence: 1,
  inputs_available: 4,
  inputs_expected: 4,
  reasons: {},
  as_of: "2026-09-20",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Route fetch by URL so one stub can serve list, enrich and score. */
function stubRoutes(routes: Array<[RegExp, () => Response]>) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      for (const [pattern, respond] of routes) {
        if (pattern.test(url)) return respond();
      }
      return json({ detail: `unrouted ${url}` }, 500);
    }),
  );
}

describe("Listings capture and delete", () => {
  it("validates the capture form with German messages and saves German number input", async () => {
    const bodies: unknown[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, init?: RequestInit) => {
        if (init?.method === "POST") {
          bodies.push(JSON.parse(String(init.body)));
          return json({ ...oneListing[0] }, 201);
        }
        return json([]);
      }),
    );
    render(<Listings />);
    await screen.findByText("Noch keine Objekte gespeichert");
    fireEvent.click(screen.getByRole("button", { name: /erfassen/ }));
    fireEvent.click(screen.getByRole("button", { name: "Objekt speichern" }));
    expect(await screen.findByText(/Kaufpreis: bitte eine Zahl/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Kaufpreis/), { target: { value: "300.000" } });
    fireEvent.change(screen.getByLabelText(/Wohnfläche/), { target: { value: "100,5" } });
    fireEvent.click(screen.getByRole("button", { name: "Objekt speichern" }));
    await waitFor(() => expect(bodies).toHaveLength(1));
    expect(bodies[0]).toMatchObject({ price: 300000, living_area_sqm: 100.5, object_type: "wohnung" });
  });

  it("asks before deleting and deletes only after confirmation", async () => {
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push(`${init?.method ?? "GET"} ${url}`);
        if (/\/score/.test(url)) return json({ detail: "enrich first" }, 409);
        if (init?.method === "DELETE") return new Response(null, { status: 204 });
        return json(oneListing);
      }),
    );
    render(<Listings />);
    fireEvent.click(await screen.findByRole("button", { name: /Bewertung von Objekt 1/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Löschen" }));
    expect(calls.some((c) => c.startsWith("DELETE"))).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Ja, löschen" }));
    await waitFor(() => expect(calls.some((c) => c.startsWith("DELETE"))).toBe(true));
  });
});

describe("Listings", () => {
  it("renders fetched listings as tiles", async () => {
    stubRoutes([[/\/api\/listings$/, () => json(oneListing)]]);
    render(<Listings />);
    expect(await screen.findByText("Lingen")).toBeInTheDocument();
    expect(screen.getByText("300.000 €")).toBeInTheDocument();
  });

  it("shows the empty state when there are no listings", async () => {
    stubRoutes([[/\/api\/listings$/, () => json([])]]);
    render(<Listings />);
    expect(await screen.findByText("Noch keine Objekte gespeichert")).toBeInTheDocument();
  });

  it("shows the score badge once a listing is scored", async () => {
    const scored = [{ ...oneListing[0], score: { total: 59, confidence: 1 } }];
    stubRoutes([[/\/api\/listings$/, () => json(scored)]]);
    render(<Listings />);
    expect(await screen.findByText("59")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Datenlage 4 von 4" })).toBeInTheDocument();
  });

  it("shows Bundesland and object type as labels, never as raw codes", async () => {
    stubRoutes([[/\/api\/listings$/, () => json(oneListing)]]);
    render(<Listings />);
    expect(await screen.findByText("Niedersachsen")).toBeInTheDocument();
    expect(screen.getByText("Wohnung")).toBeInTheDocument();
    expect(screen.queryByText("wohnung")).toBeNull();
    expect(screen.queryByText("NI")).toBeNull();
    expect(screen.queryByText("grundstueck")).toBeNull();
  });

  it("offers the Bundesland as a select with all 16 states", async () => {
    stubRoutes([[/\/api\/listings$/, () => json([])]]);
    render(<Listings />);
    await screen.findByText("Noch keine Objekte gespeichert");
    fireEvent.click(screen.getByRole("button", { name: /erfassen/ }));
    const select = screen.getByLabelText("Bundesland") as HTMLSelectElement;
    expect(select.options).toHaveLength(16);
  });

  it("updates the table score after 'Anreichern + bewerten' (no stale dash)", async () => {
    // the list response stays unscored (no rent) — only the report carries the 59
    stubRoutes([
      [/\/enrich$/, () => json({ bodenrichtwert_eur_per_sqm: 2500, region: null, unavailable: {}, enriched_at: "x" })],
      [/\/score/, () => json(scoreReport)],
      [/\/api\/listings$/, () => json(oneListing)],
    ]);
    render(<Listings />);
    const tile = (await screen.findByText("Lingen")).closest("li")!;
    expect(within(tile).getByText("—")).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: /Bewertung von Objekt 1/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Anreichern + bewerten" }));
    await screen.findByText("59/100");
    expect(within(tile).getByText("59")).toBeInTheDocument();
    expect(within(tile).queryByText("—")).toBeNull();
  });

  it("scores the example object with its rent and never calls enrich", async () => {
    const example = [{ ...oneListing[0], ort: "Lingen (Beispiel)", features: ["beispiel"] }];
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        calls.push(url);
        if (/\/score/.test(url)) return json(scoreReport);
        return json(example);
      }),
    );
    render(<Listings />);
    fireEvent.click(await screen.findByRole("button", { name: /Bewertung von Objekt 1/ }));
    expect(await screen.findByText("59/100")).toBeInTheDocument();
    expect(calls.some((u) => u.includes("monthly_cold_rent=1000"))).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Anreichern + bewerten" }));
    await waitFor(() => expect(calls.filter((u) => /score/.test(u)).length).toBeGreaterThan(1));
    expect(calls.some((u) => /enrich/.test(u))).toBe(false);
    expect(screen.getByText(/Beispielobjekt mit fest hinterlegten/)).toBeInTheDocument();
  });

  it("enriches, scores and renders the drilldown", async () => {
    stubRoutes([
      [/\/enrich$/, () => json({ bodenrichtwert_eur_per_sqm: 2500, region: null, unavailable: {}, enriched_at: "x" })],
      [/\/score/, () => json(scoreReport)],
      [/\/api\/listings$/, () => json(oneListing)],
    ]);
    render(<Listings />);
    fireEvent.click(await screen.findByRole("button", { name: /Bewertung von Objekt 1/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Anreichern + bewerten" }));
    expect(await screen.findByText("59/100")).toBeInTheDocument();
    expect(screen.getByText("Rendite")).toBeInTheDocument();
  });

  it("surfaces the German Ollama hint when the backend answers 503", async () => {
    stubRoutes([
      [/\/enrich$/, () => json({}, 503)],
      [/\/score/, () => json({}, 503)],
      [/\/api\/listings$/, () => json(oneListing)],
    ]);
    render(<Listings />);
    fireEvent.click(await screen.findByRole("button", { name: /Bewertung von Objekt 1/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Anreichern + bewerten" }));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/Ollama ist nicht erreichbar/),
    );
    // the error shows inside the open drawer, not behind its scrim
    expect(screen.getByRole("dialog").contains(screen.getByRole("alert"))).toBe(true);
  });

  it("treats a 409 (never enriched) as an offer to enrich, not an error", async () => {
    stubRoutes([
      [/\/score/, () => json({ detail: "listing 1 has no enrichment yet — enrich first" }, 409)],
      [/\/api\/listings$/, () => json(oneListing)],
    ]);
    render(<Listings />);
    fireEvent.click(await screen.findByRole("button", { name: /Bewertung von Objekt 1/ }));
    expect(await screen.findByText(/Noch keine Bewertung/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
