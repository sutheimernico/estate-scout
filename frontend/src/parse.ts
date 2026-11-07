// German number input: "3,6", "300.000", "1.234,56" and "300000" all have one unambiguous meaning.
// Number("300.000") would silently read 300, which for a loan amount is a wrong-by-1000 answer.

export function parseDecimal(raw: string): number | null {
  // a trailing comma ("3,") is a decimal being typed, not an error
  const s = raw.trim().replace(/[\s €%]/g, "").replace(/,$/, "");
  if (s === "") return null;
  let normalized: string;
  if (s.includes(",")) {
    normalized = s.replace(/\./g, "").replace(",", ".");
  } else if (/^\d{1,3}(\.\d{3})+$/.test(s)) {
    normalized = s.replace(/\./g, ""); // dots as thousands separators
  } else {
    normalized = s;
  }
  if (!/^-?\d+(\.\d+)?$/.test(normalized)) return null;
  return Number(normalized);
}
