// de-DE number formatting shared by all result cards and tables.

import { parseDecimal } from "./parse";

export const eur = (n: number) =>
  n.toLocaleString("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

export const pct = (n: number) => `${n.toLocaleString("de-DE", { maximumFractionDigits: 2 })} %`;

export const num = (n: number, digits = 1) =>
  n.toLocaleString("de-DE", { maximumFractionDigits: digits });

// Amounts that are computed to the cent (monthly rates) keep their cents.
export const eurCents = (n: number) =>
  n.toLocaleString("de-DE", { style: "currency", currency: "EUR", minimumFractionDigits: 2 });

// Keeps a figure and its unit on one line ("300.000 €" must not break before the €).
export const bindUnits = (text: string) =>
  text.replace(/(\d) (€|%|m²|Jahre|Jahren|Monate|Monaten)/g, "$1 $2");

// Tidies what the user typed once the field loses focus: "300000" becomes "300.000", a typed
// decimal count stays ("2,0" stays "2,0"). Text that is not a number is left for the error line.
export function formatInput(raw: string): string {
  const n = parseDecimal(raw);
  if (n === null) return raw;
  const comma = raw.trim().indexOf(",");
  const typed = comma >= 0 ? raw.trim().replace(/[^\d]+$/, "").length - comma - 1 : 0;
  const digits = Math.min(Math.max(typed, 0), 2);
  return n.toLocaleString("de-DE", { minimumFractionDigits: digits, maximumFractionDigits: Math.max(digits, 2) });
}
