import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Chat } from "./Chat";

const askResponse = {
  answer: "Deine Monatsrate liegt bei 1.400 €.",
  tool_calls: [
    {
      name: "annuity",
      args: { principal: 300000, annual_rate_percent: 3.6, initial_repayment_percent: 2.0 },
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
    expect(screen.getByRole("heading", { name: "Annuitätendarlehen" })).toBeInTheDocument();
    expect(screen.getByText(/Zahl aus dem Rechner „Annuitätendarlehen“/)).not.toHaveTextContent("annuity");
  });

  it("warns when the answer quotes a number no tool produced", async () => {
    stubFetch({ ...askResponse, unverified_numbers: ["181.210,86"] });
    render(<Chat />);
    submitQuestion("Was zahle ich monatlich?");
    expect(await screen.findByRole("alert")).toHaveTextContent("181.210,86");
  });

  it("shows no warning when every number is traced", async () => {
    stubFetch({ ...askResponse, unverified_numbers: [] });
    render(<Chat />);
    submitQuestion("Was zahle ich monatlich?");
    await screen.findByText("Deine Monatsrate liegt bei 1.400 €.");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("shows the German Ollama hint on 503", async () => {
    stubFetch({}, 503);
    render(<Chat />);
    submitQuestion("hallo?");
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/Ollama ist nicht erreichbar/),
    );
    expect(screen.getByText("ollama serve")).toBeInTheDocument(); // the fix, copyable
    expect(screen.getByRole("button", { name: "Nochmal fragen" })).toBeInTheDocument();
  });

  it("shows the backend's actionable text for a missing model and a timeout", async () => {
    stubFetch({ detail: "Das Modell „bge-m3“ fehlt in Ollama. Installiere es mit: ollama pull bge-m3" }, 424);
    render(<Chat />);
    submitQuestion("hallo?");
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/ollama pull bge-m3/));
  });

  it("shows the slow-model text on a 504", async () => {
    stubFetch({ detail: "Das Modell „qwen2.5:7b“ antwortet zu langsam" }, 504);
    render(<Chat />);
    submitQuestion("hallo?");
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(/antwortet zu langsam/));
  });

  it("shows a thinking indicator while waiting", async () => {
    let resolve!: (r: Response) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>((res) => (resolve = res))),
    );
    render(<Chat />);
    submitQuestion("dauert das?");
    expect(await screen.findByText(/Das Modell liest die Wissensbasis/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Abbrechen" })).toBeInTheDocument();
    resolve(
      new Response(JSON.stringify(askResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() => expect(screen.queryByText(/Das Modell liest die Wissensbasis/)).not.toBeInTheDocument());
  });
});

describe("Chat extras", () => {
  it("starts a conversation from a starter question", async () => {
    stubFetch(askResponse);
    render(<Chat />);
    fireEvent.click(screen.getByRole("button", { name: /Kaufnebenkosten/ }));
    expect(await screen.findByText("Deine Monatsrate liegt bei 1.400 €.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /Der Assistent erklärt/ })).toBeNull();
  });

  it("lists every tool call in the Rechenspur", async () => {
    stubFetch(askResponse);
    render(<Chat />);
    submitQuestion("Was zahle ich monatlich?");
    const trace = await screen.findByRole("complementary", { name: "Rechenspur" });
    expect(trace).toHaveTextContent("Annuitätendarlehen");
    expect(trace).toHaveTextContent("300.000");
  });

  it("names the note a source came from, not its file path", async () => {
    stubFetch({ ...askResponse, sources: ["03-finanzierung.md"] });
    render(<Chat />);
    submitQuestion("Was zahle ich monatlich?");
    expect(await screen.findByText("Finanzierung")).toBeInTheDocument();
    expect(screen.queryByText(/03-finanzierung/)).toBeNull();
  });
});

describe("ToolTrace in the chat", () => {
  it("shows which tool ran with which inputs, collapsed by default", async () => {
    stubFetch(askResponse);
    render(<Chat />);
    submitQuestion("Was zahle ich monatlich?");
    const summary = await screen.findByText("Werkzeuge (1)");
    // <details> renders its content in the DOM even while closed — assert the closed state
    expect(summary.closest("details")).not.toHaveAttribute("open");
    fireEvent.click(summary);
    expect(summary.closest("details")).toHaveAttribute("open");
    expect(screen.getAllByText("annuity").length).toBeGreaterThan(0);
    expect(screen.getByText(/"monthly_payment":1400/)).toBeInTheDocument();
  });

  it("does not scroll on mount, only once there is a transcript to follow", async () => {
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    stubFetch(askResponse);
    render(<Chat />);
    expect(scrollIntoView).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Frage"), { target: { value: "Rate?" } });
    fireEvent.click(screen.getByRole("button", { name: "Fragen" }));
    await waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
    delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
  });

  it("shows the recorded number-guard catch on the intro, with the garbled figure and the verdict", () => {
    stubFetch(askResponse);
    render(<Chat />);
    expect(screen.getByText("181.209,86 €")).toBeInTheDocument();
    expect(screen.getByText("181.210,86 EUR")).toBeInTheDocument();
    expect(screen.getByText(/Nicht belegt/)).toBeInTheDocument();
    expect(screen.getByText(/Aufgezeichneter Lauf, qwen2.5:7b, lokal, 20.09.2026/)).toBeInTheDocument();
    expect(screen.getByText(/Die Prüfung wurde\s+danach gebaut/)).toBeInTheDocument();
  });
});
