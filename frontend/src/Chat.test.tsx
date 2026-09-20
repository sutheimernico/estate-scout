import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Chat } from "./Chat";

const askResponse = {
  answer: "Deine Monatsrate liegt bei 1.400 €.",
  tool_calls: [
    {
      name: "annuity",
      args: {},
      result: {
        monthly_payment: 1400,
        total_interest: 181209.86,
        total_paid: 481209.86,
        years_to_payoff: 28.7,
        remaining_debt_by_year: [{ year: 1, remaining_debt: 293900 }],
      },
    },
  ],
  sources: [],
  disclaimer: "Hinweis: keine Steuer-, Anlage- oder Finanzierungsberatung.",
};

function stubFetch(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify(body), {
          status,
          headers: { "Content-Type": "application/json" },
        }),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function submitQuestion(text: string) {
  fireEvent.change(screen.getByLabelText("Frage"), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Fragen" }));
}

describe("Chat", () => {
  it("renders the answer and the annuity card after a round-trip", async () => {
    stubFetch(askResponse);
    render(<Chat />);
    submitQuestion("Was zahle ich monatlich?");
    expect(await screen.findByText("Deine Monatsrate liegt bei 1.400 €.")).toBeInTheDocument();
    expect(screen.getByText("Annuitätendarlehen")).toBeInTheDocument();
  });

  it("shows the German Ollama hint on 503", async () => {
    stubFetch({ detail: "down" }, 503);
    render(<Chat />);
    submitQuestion("hallo?");
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/Ollama ist nicht erreichbar/),
    );
  });

  it("shows a thinking indicator while waiting", async () => {
    let resolve!: (r: Response) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>((res) => (resolve = res))),
    );
    render(<Chat />);
    submitQuestion("dauert das?");
    expect(await screen.findByText(/denkt nach/)).toBeInTheDocument();
    resolve(
      new Response(JSON.stringify(askResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() => expect(screen.queryByText(/denkt nach/)).not.toBeInTheDocument());
  });
});
