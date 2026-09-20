// Types mirror the FastAPI responses (src/estatescout/api.py) and the finance tool results
// (src/estatescout/assistant/tools.py). Narrowing wire data to typed results happens in
// exactly one place: toKnownCalc().

import { type AnnuityResult } from "./AmortizationTable";

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface AskResponse {
  answer: string;
  tool_calls: ToolCall[];
  sources: string[];
  disclaimer: string;
}

export interface PurchaseCostsResult {
  bundesland: string;
  grunderwerbsteuer: number;
  notary: number;
  land_registry: number;
  makler: number;
  total_ancillary: number;
  total_investment: number;
  ancillary_quota_percent: number;
  min_equity: number;
}

export interface AffordabilityResult {
  max_monthly_payment: number;
  max_loan: number;
  max_purchase_price: number;
  ancillary_quota_percent: number;
  equity: number;
}

export interface YieldResult {
  annual_cold_rent: number;
  gross_yield_percent: number;
  net_yield_percent: number;
  kaufpreisfaktor: number;
}

export interface OperatingCostsResult {
  instandhaltung: number;
  verwaltung: number;
  mietausfallwagnis: number;
  total_annual: number;
}

export interface EquityReturnResult {
  loan: number;
  annual_debt_service: number;
  net_operating_income: number;
  cashflow_before_tax: number;
  cash_on_cash_percent: number;
}

// Discriminated union: the `kind` tag lets TypeScript narrow `result` to one exact shape
// inside a switch, so every card renders with full type safety and no casts at use site.
export type KnownCalc =
  | { kind: "annuity"; result: AnnuityResult }
  | { kind: "purchase_costs"; result: PurchaseCostsResult }
  | { kind: "affordability"; result: AffordabilityResult }
  | { kind: "yield_metrics"; result: YieldResult }
  | { kind: "operating_costs"; result: OperatingCostsResult }
  | { kind: "equity_return"; result: EquityReturnResult };

// The single narrowing boundary between wire data and typed results. Failed tool calls
// ({error: ...}) and unknown tools return null — callers simply render no card.
export function toKnownCalc(name: string, result: Record<string, unknown>): KnownCalc | null {
  if ("error" in result) return null;
  switch (name) {
    case "annuity":
      return "remaining_debt_by_year" in result
        ? { kind: "annuity", result: result as unknown as AnnuityResult }
        : null;
    case "purchase_costs":
      return { kind: "purchase_costs", result: result as unknown as PurchaseCostsResult };
    case "affordability":
      return { kind: "affordability", result: result as unknown as AffordabilityResult };
    case "yield_metrics":
      return { kind: "yield_metrics", result: result as unknown as YieldResult };
    case "operating_costs":
      return { kind: "operating_costs", result: result as unknown as OperatingCostsResult };
    case "equity_return":
      return { kind: "equity_return", result: result as unknown as EquityReturnResult };
    default:
      return null;
  }
}

export interface Listing {
  id: number;
  price: number;
  living_area_sqm: number;
  bundesland: string;
  plz: string;
  ort: string;
  rooms: number | null;
  year_built: number | null;
  object_type: string;
  features: string[];
  source_url: string;
  price_per_sqm: number;
}

export interface NewListing {
  price: number;
  living_area_sqm: number;
  bundesland: string;
  ort?: string;
  rooms?: number;
  year_built?: number;
  object_type?: string;
  source_url?: string;
}

async function errorMessage(res: Response): Promise<string> {
  if (res.status === 503) {
    return "Ollama ist nicht erreichbar. Starte den lokalen Server (ollama serve) und ziehe ein Modell.";
  }
  try {
    const body: unknown = await res.json();
    if (
      body !== null &&
      typeof body === "object" &&
      typeof (body as { detail?: unknown }).detail === "string"
    ) {
      return (body as { detail: string }).detail;
    }
  } catch {
    // non-JSON error body — fall through to the generic message
  }
  return `Fehler ${res.status}`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err; // caller cancelled
    throw new Error("API nicht erreichbar — läuft der Server (uv run uvicorn estatescout.api:app)?");
  }
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const asJson = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export function ask(question: string, signal?: AbortSignal): Promise<AskResponse> {
  return request<AskResponse>("/api/ask", { ...asJson({ question }), signal });
}

export function finance(
  calc: string,
  args: Record<string, unknown>,
): Promise<{ result: Record<string, unknown>; disclaimer: string }> {
  return request(`/api/finance/${calc}`, asJson(args));
}

export function listListings(): Promise<Listing[]> {
  return request("/api/listings");
}

export function createListing(data: NewListing): Promise<Listing> {
  return request("/api/listings", asJson(data));
}

export function deleteListing(id: number): Promise<void> {
  return request(`/api/listings/${id}`, { method: "DELETE" });
}
