import { render, screen } from "@testing-library/react";
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
  },
];

describe("Listings", () => {
  it("renders fetched listings in the table", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify(oneListing), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    render(<Listings />);
    expect(await screen.findByText("Lingen")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Objekt 1 löschen" })).toBeInTheDocument();
  });

  it("shows the empty state when there are no listings", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    render(<Listings />);
    expect(await screen.findByText(/Noch keine Objekte gespeichert/)).toBeInTheDocument();
  });
});
