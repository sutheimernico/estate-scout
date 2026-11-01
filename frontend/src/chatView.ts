// Pure helpers behind the chat: which problem an API failure is, what to show for it, how to
// write the elapsed time and how a tool call reads in plain German. No React in here.

import { ApiError } from "./api";
import { type CalcSpec, SPECS } from "./calcSpecs";
import { num } from "./format";
import { bundeslandName } from "./labels";

export type ProblemKind = "model-missing" | "ollama-down" | "slow" | "offline" | "cancelled" | "other";

export interface Problem {
  kind: ProblemKind;
  title: string;
  body: string;
  command?: string; // shown copyable
  retry: boolean; // offer "Nochmal fragen"
}

// "…Installiere es mit: ollama pull bge-m3." → "ollama pull bge-m3"
export function pullCommand(text: string): string | undefined {
  const match = /ollama pull [\w.:/-]+/.exec(text);
  return match ? match[0].replace(/[.:]+$/, "") : undefined;
}

export const SERVER_COMMAND = "uv run uvicorn estatescout.api:app --port 8000";

export function problemFrom(err: unknown): Problem {
  if (err instanceof DOMException && err.name === "AbortError") {
    return { kind: "cancelled", title: "Abgebrochen", body: "Die Anfrage wurde abgebrochen.", retry: true };
  }
  const message = err instanceof Error ? err.message : String(err);
  const status = err instanceof ApiError ? err.status : -1;
  switch (status) {
    case 424:
      return {
        kind: "model-missing",
        title: "Das Modell fehlt in Ollama",
        body: message,
        command: pullCommand(message),
        retry: true,
      };
    case 503:
      return {
        kind: "ollama-down",
        title: "Ollama läuft nicht",
        body: message,
        command: "ollama serve",
        retry: true,
      };
    case 504:
      return {
        kind: "slow",
        title: "Das Modell antwortet zu langsam",
        body: `${message} Auf der CPU braucht ein lokales Modell beim ersten Aufruf oft über eine Minute. Der zweite Versuch ist meist schneller.`,
        retry: true,
      };
    case 0:
      return {
        kind: "offline",
        title: "Der Server antwortet nicht",
        body: "Die API von estate-scout ist nicht erreichbar. Starte sie im Projektordner:",
        command: SERVER_COMMAND,
        retry: true,
      };
    default:
      return { kind: "other", title: "Das hat nicht geklappt", body: message, retry: true };
  }
}

export function formatElapsed(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export interface Starter {
  label: string;
  question: string;
}

export const STARTERS: Starter[] = [
  {
    label: "Monatsrate berechnen",
    question: "Was zahle ich monatlich bei 300.000 € Darlehen, 3,6 % Zins und 2 % Tilgung, 10 Jahre Zinsbindung?",
  },
  {
    label: "Kaufnebenkosten",
    question: "Wie hoch sind die Kaufnebenkosten bei 350.000 € in Niedersachsen?",
  },
  {
    label: "Lohnt sich die Vermietung?",
    question: "Wie hoch ist die Mietrendite bei 250.000 € Kaufpreis und 1.000 € Kaltmiete im Monat?",
  },
  {
    label: "Zinsbindung verstehen",
    question: "Was bedeutet Zinsbindung, und welche Laufzeit ist sinnvoll?",
  },
];

// One tool call as the user would say it: "Darlehensbetrag 300.000 € · Sollzins 3,6 % p. a."
export function argSummary(name: string, args: Record<string, unknown>): string {
  const spec: CalcSpec | undefined = SPECS.find((s) => s.calc === name);
  if (!spec) return "";
  const parts: string[] = [];
  for (const f of spec.fields) {
    const v = args[f.key];
    if (v === undefined || v === null) continue;
    const shown = f.select === "bundesland" ? bundeslandName(String(v)) : typeof v === "number" ? num(v, 2) : String(v);
    parts.push(`${f.label} ${shown}${f.unit && !f.select ? ` ${f.unit}` : ""}`);
  }
  return parts.join(" · ");
}

export function toolTitle(name: string): string {
  return SPECS.find((s) => s.calc === name)?.title ?? name;
}

// "02-lage-und-datenquellen.md" → "Lage und Datenquellen": corpus file names are shown as the
// titles of the notes they are, never as paths.
export function sourceLabel(file: string): string {
  const base = file.replace(/^.*\//, "").replace(/\.md$/, "").replace(/^\d+-/, "");
  const words = base.split("-").map((w) => (w.startsWith("ueber") ? `ü${w.slice(2)}` : w));
  // German nouns are capitalised; the file names only contain nouns and "und"
  return words.map((w) => (w === "und" ? w : w.charAt(0).toUpperCase() + w.slice(1))).join(" ");
}

// Every tool call of the conversation in order, flattened for the "Rechenspur" column.
export interface TraceEntry {
  n: number;
  messageId: number;
  name: string;
  title: string;
  summary: string;
}

export function traceOf(
  messages: { id: number; response?: { tool_calls: { name: string; args: Record<string, unknown> }[] } }[],
): TraceEntry[] {
  const out: TraceEntry[] = [];
  for (const m of messages) {
    for (const c of m.response?.tool_calls ?? []) {
      out.push({
        n: out.length + 1,
        messageId: m.id,
        name: c.name,
        title: toolTitle(c.name),
        summary: argSummary(c.name, c.args),
      });
    }
  }
  return out;
}
