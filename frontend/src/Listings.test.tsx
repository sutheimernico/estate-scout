import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

describe("Listings", () => {
  it("renders fetched listings in the table", async () => {
    stubRoutes([[/\/api\/listings$/, () => json(oneListing)]]);
    render(<Listings />);
    expect(await screen.findByText("Lingen")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Objekt 1 löschen" })).toBeInTheDocument();
  });

  it("shows the empty state when there are no listings", async () => {
    stubRoutes([[/\/api\/listings$/, () => json([])]]);
    render(<Listings />);
    expect(await screen.findByText(/Noch keine Objekte gespeichert/)).toBeInTheDocument();
  });

  it("shows the score badge once a listing is scored", async () => {
    const scored = [{ ...oneListing[0], score: { total: 59, confidence: 1 } }];
    stubRoutes([[/\/api\/listings$/, () => json(scored)]]);
    render(<Listings />);
    expect(await screen.findByText("59")).toBeInTheDocument();
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
      [/\/enrich$/, () => json({ detail: "down" }, 503)],
      [/\/score/, () => json({ detail: "down" }, 503)],
      [/\/api\/listings$/, () => json(oneListing)],
    ]);
    render(<Listings />);
    fireEvent.click(await screen.findByRole("button", { name: /Bewertung von Objekt 1/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Anreichern + bewerten" }));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/Ollama ist nicht erreichbar/),
    );
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
