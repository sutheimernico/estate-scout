// Types mirror the FastAPI responses (src/estatescout/api.py) and the finance tool results
// (src/estatescout/assistant/tools.py). Narrowing wire data to typed results happens in
// exactly one place: toKnownCalc().

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
  // Numbers in the answer text that match no tool result; absent on older servers.
  unverified_numbers?: string[];
}

// Result shapes of the six calculators — hand-written to match the Pydantic output models in
// src/estatescout/schemas.py (visible as response schemas in /docs). `type` aliases rather than
// interfaces, so they stay assignable to Record<string, unknown> in the guards below.
export type AnnuityResult = {
  monthly_payment: number;
  total_interest: number;
  total_paid: number;
  months_to_payoff: number;
  years_to_payoff: number;
  remaining_debt_by_year: { year: number; remaining_debt: number }[];
  // only when a Zinsbindung was requested
  zinsbindung_years?: number | null;
  restschuld_after_zinsbindung?: number | null;
  interest_during_zinsbindung?: number | null;
};

export type PurchaseCostsResult = {
  bundesland: string;
  grunderwerbsteuer: number;
  notary: number;
  land_registry: number;
  makler: number;
  total_ancillary: number;
  total_investment: number;
  ancillary_quota_percent: number;
  min_equity: number;
};

export type AffordabilityResult = {
  max_monthly_payment: number;
  max_loan: number;
  max_purchase_price: number;
  ancillary_quota_percent: number;
  equity: number;
};

export type YieldResult = {
  annual_cold_rent: number;
  gross_yield_percent: number;
  net_yield_percent: number;
  kaufpreisfaktor: number;
};

export type OperatingCostsResult = {
  instandhaltung: number;
  verwaltung: number;
  mietausfallwagnis: number;
  total_annual: number;
};

export type EquityReturnResult = {
  loan: number;
  annual_debt_service: number;
  net_operating_income: number;
  cashflow_before_tax: number;
  cash_on_cash_percent: number;
  year1_tilgung: number;
  return_incl_tilgung_percent: number;
};

type Wire = Record<string, unknown>;

// Runtime check instead of a cast: every listed key must be a number. A malformed or partial
// result (older server, failed tool call) then renders no card rather than "NaN €".
const hasNumbers = (r: Wire, keys: readonly string[]) =>
  keys.every((k) => typeof r[k] === "number");

const isAnnuity = (r: Wire): r is AnnuityResult =>
  hasNumbers(r, ["monthly_payment", "total_interest", "total_paid", "years_to_payoff"]) &&
  Array.isArray(r.remaining_debt_by_year);
const isPurchaseCosts = (r: Wire): r is PurchaseCostsResult =>
  typeof r.bundesland === "string" &&
  hasNumbers(r, [
    "grunderwerbsteuer",
    "notary",
    "land_registry",
    "makler",
    "total_ancillary",
    "total_investment",
    "ancillary_quota_percent",
    "min_equity",
  ]);
const isAffordability = (r: Wire): r is AffordabilityResult =>
  hasNumbers(r, [
    "max_monthly_payment",
    "max_loan",
    "max_purchase_price",
    "ancillary_quota_percent",
    "equity",
  ]);
const isYield = (r: Wire): r is YieldResult =>
  hasNumbers(r, ["annual_cold_rent", "gross_yield_percent", "net_yield_percent", "kaufpreisfaktor"]);
const isOperatingCosts = (r: Wire): r is OperatingCostsResult =>
  hasNumbers(r, ["instandhaltung", "verwaltung", "mietausfallwagnis", "total_annual"]);
const isEquityReturn = (r: Wire): r is EquityReturnResult =>
  hasNumbers(r, [
    "loan",
    "annual_debt_service",
    "net_operating_income",
    "cashflow_before_tax",
    "cash_on_cash_percent",
    "year1_tilgung",
    "return_incl_tilgung_percent",
  ]);

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
// ({error: ...}), unknown tools and results of an unexpected shape return null — callers
// simply render no card.
export function toKnownCalc(name: string, result: Wire): KnownCalc | null {
  if ("error" in result) return null;
  switch (name) {
    case "annuity":
      return isAnnuity(result) ? { kind: "annuity", result } : null;
    case "purchase_costs":
      return isPurchaseCosts(result) ? { kind: "purchase_costs", result } : null;
    case "affordability":
      return isAffordability(result) ? { kind: "affordability", result } : null;
    case "yield_metrics":
      return isYield(result) ? { kind: "yield_metrics", result } : null;
    case "operating_costs":
      return isOperatingCosts(result) ? { kind: "operating_costs", result } : null;
    case "equity_return":
      return isEquityReturn(result) ? { kind: "equity_return", result } : null;
    default:
      return null;
  }
}

export interface RegionSignal {
  population_trend_pct: number | null;
  vacancy_rate_pct: number | null;
}

export interface EnrichmentView {
  bodenrichtwert_eur_per_sqm: number | null;
  region: RegionSignal | null;
  // signal -> "provider_missing" | "no_data"; the backend never fabricates a value
  unavailable: Record<string, string>;
  enriched_at: string | null;
}

export interface SubScore {
  name: string;
  value: number | null;
  weight: number;
  detail: Record<string, unknown>;
  reason: string | null;
}

export interface ScoreReport {
  total: number | null;
  subscores: SubScore[];
  weights_used: Record<string, number>;
  confidence: number;
  inputs_available: number;
  inputs_expected: number;
  reasons: Record<string, string>;
  as_of: string;
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
  enrichment: EnrichmentView | null;
  score: { total: number | null; confidence: number } | null;
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

// Carries the HTTP status (0 = server unreachable) so the UI can map it to a helpful state
// instead of parsing message text.
export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function errorMessage(res: Response): Promise<string> {
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
  if (res.status === 503) {
    return "Ollama ist nicht erreichbar. Starte den lokalen Server (ollama serve) und ziehe ein Modell.";
  }
  return `Fehler ${res.status}`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err; // caller cancelled
    throw new ApiError(
      "API nicht erreichbar — läuft der Server (uv run uvicorn estatescout.api:app)?",
      0,
    );
  }
  if (!res.ok) throw new ApiError(await errorMessage(res), res.status);
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
  signal?: AbortSignal,
): Promise<{ result: Record<string, unknown>; disclaimer: string }> {
  return request(`/api/finance/${calc}`, { ...asJson(args), signal });
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

export function enrichListing(id: number): Promise<EnrichmentView> {
  return request(`/api/listings/${id}/enrich`, { method: "POST" });
}

export function scoreListing(id: number, monthlyColdRent?: number): Promise<ScoreReport> {
  const query =
    monthlyColdRent === undefined ? "" : `?monthly_cold_rent=${encodeURIComponent(monthlyColdRent)}`;
  return request(`/api/listings/${id}/score${query}`);
}
