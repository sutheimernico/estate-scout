import { describe, expect, it } from "vitest";

import { ApiError } from "./api";
import { argSummary, formatElapsed, problemFrom, pullCommand, sourceLabel, toolTitle, traceOf } from "./chatView";

describe("pullCommand", () => {
  it("lifts the copyable command out of the backend's sentence", () => {
    expect(pullCommand("Das Modell „bge-m3“ fehlt. Installiere es mit: ollama pull bge-m3")).toBe(
      "ollama pull bge-m3",
    );
    expect(pullCommand("… ollama pull qwen2.5:7b.")).toBe("ollama pull qwen2.5:7b");
    expect(pullCommand("kein Befehl")).toBeUndefined();
  });
});

describe("problemFrom", () => {
  it("maps 424 to a missing-model state with the pull command", () => {
    const p = problemFrom(new ApiError("Installiere es mit: ollama pull bge-m3", 424));
    expect(p.kind).toBe("model-missing");
    expect(p.command).toBe("ollama pull bge-m3");
  });
  it("maps 503 to Ollama-down with ollama serve", () => {
    const p = problemFrom(new ApiError("Ollama ist nicht erreichbar.", 503));
    expect(p).toMatchObject({ kind: "ollama-down", command: "ollama serve" });
  });
  it("maps 504 to a slow-model state that can be retried", () => {
    const p = problemFrom(new ApiError("Das Modell antwortet zu langsam.", 504));
    expect(p.kind).toBe("slow");
    expect(p.retry).toBe(true);
    expect(p.body).toContain("Das Modell antwortet zu langsam.");
  });
  it("maps an unreachable API (status 0) to the server start command", () => {
    expect(problemFrom(new ApiError("x", 0)).command).toMatch(/uvicorn/);
  });
  it("treats an abort as a cancellation, not a failure", () => {
    expect(problemFrom(new DOMException("a", "AbortError")).kind).toBe("cancelled");
  });
  it("falls back to the plain message for anything else", () => {
    expect(problemFrom(new ApiError("Fehler 500", 500))).toMatchObject({ kind: "other", body: "Fehler 500" });
  });
});

describe("formatElapsed", () => {
  it("writes m:ss", () => {
    expect(formatElapsed(7)).toBe("0:07");
    expect(formatElapsed(65.9)).toBe("1:05");
    expect(formatElapsed(-3)).toBe("0:00");
  });
});

describe("argSummary", () => {
  it("reads like the question: labels, de-DE numbers, units, Bundesland names", () => {
    const text = argSummary("purchase_costs", { purchase_price: 350000, bundesland: "NI" });
    expect(text).toBe("Kaufpreis 350.000 € · Bundesland Niedersachsen");
  });
  it("is empty for an unknown tool", () => {
    expect(argSummary("search_knowledge", { query: "x" })).toBe("");
    expect(toolTitle("search_knowledge")).toBe("search_knowledge");
    expect(toolTitle("annuity")).toBe("Annuitätendarlehen");
  });
});

describe("sourceLabel", () => {
  it("turns corpus file names into note titles", () => {
    expect(sourceLabel("03-finanzierung.md")).toBe("Finanzierung");
    expect(sourceLabel("02-lage-und-datenquellen.md")).toBe("Lage und Datenquellen");
    expect(sourceLabel("00-ueberblick.md")).toBe("Überblick");
    expect(sourceLabel("knowledge/05-risiken-und-recht.md")).toBe("Risiken und Recht");
  });
});

describe("traceOf", () => {
  it("numbers tool calls across messages and skips messages without any", () => {
    const t = traceOf([
      { id: 1 },
      { id: 2, response: { tool_calls: [{ name: "annuity", args: { principal: 300000 } }] } },
      { id: 3, response: { tool_calls: [{ name: "purchase_costs", args: {} }, { name: "unknown_tool", args: {} }] } },
    ]);
    expect(t.map((e) => [e.n, e.messageId, e.title])).toEqual([
      [1, 2, "Annuitätendarlehen"],
      [2, 3, "Kaufnebenkosten"],
      [3, 3, "unknown_tool"],
    ]);
    expect(t[0].summary).toContain("300.000");
  });
});
