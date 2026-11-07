// de-DE number formatting shared by all result cards and tables.

import { parseDecimal } from "./parse";

export const eur = (n: number) =>
  n.toLocaleString("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

// Percentages always carry two decimals, so "3,60 %" and "10,57 %" line up in one column.
export const pct = (n: number) =>
  `${n.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} %`;

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

// 28.7 years as words a person says: "28 Jahre, 8 Monate" (dative for "nach …": "28 Jahren, 8 Monaten").
export function duration(years: number, dative = false): string {
  const total = Math.round(years * 12);
  const y = Math.floor(total / 12);
  const m = total % 12;
  const yUnit = dative ? (y === 1 ? "Jahr" : "Jahren") : y === 1 ? "Jahr" : "Jahre";
  const mUnit = dative ? (m === 1 ? "Monat" : "Monaten") : m === 1 ? "Monat" : "Monate";
  if (y === 0) return `${m} ${mUnit}`;
  return m === 0 ? `${y} ${yUnit}` : `${y} ${yUnit}, ${m} ${mUnit}`;
}

// "2026-09-20" -> "20.09.2026"; anything else is returned as it came.
export function germanDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}.${m[2]}.${m[1]}` : iso;
}
