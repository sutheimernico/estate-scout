// de-DE number formatting shared by all result cards and tables.

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
