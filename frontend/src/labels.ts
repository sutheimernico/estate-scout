// Display labels for values the backend sends as codes — the UI never shows raw keys.

export const BUNDESLAENDER = [
  { code: "BW", name: "Baden-Württemberg" },
  { code: "BY", name: "Bayern" },
  { code: "BE", name: "Berlin" },
  { code: "BB", name: "Brandenburg" },
  { code: "HB", name: "Bremen" },
  { code: "HH", name: "Hamburg" },
  { code: "HE", name: "Hessen" },
  { code: "MV", name: "Mecklenburg-Vorpommern" },
  { code: "NI", name: "Niedersachsen" },
  { code: "NW", name: "Nordrhein-Westfalen" },
  { code: "RP", name: "Rheinland-Pfalz" },
  { code: "SL", name: "Saarland" },
  { code: "SN", name: "Sachsen" },
  { code: "ST", name: "Sachsen-Anhalt" },
  { code: "SH", name: "Schleswig-Holstein" },
  { code: "TH", name: "Thüringen" },
] as const;

export const DEFAULT_BUNDESLAND = "NI";

export function bundeslandName(code: string): string {
  return BUNDESLAENDER.find((b) => b.code === code)?.name ?? code;
}

const OBJECT_TYPES: Record<string, string> = {
  wohnung: "Wohnung",
  haus: "Haus",
  grundstueck: "Grundstück",
};

export function objectTypeLabel(type: string): string {
  return OBJECT_TYPES[type] ?? type;
}

// Marks the bundled example object (see src/estatescout/scout/model.py).
export const EXAMPLE_FEATURE = "beispiel";
export const EXAMPLE_RENT = "1000";
