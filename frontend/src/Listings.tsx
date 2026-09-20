// Saved property objects: intake form + table over /api/listings.
// Object attributes only — never seller contact data (ADR-0001 / DSGVO).

import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";

import { createListing, deleteListing, type Listing, listListings } from "./api";
import { eur, num } from "./format";

const EMPTY_FORM = { price: "", area: "", bundesland: "", ort: "", rooms: "", year: "" };

export function Listings() {
  const [items, setItems] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setItems(await listListings());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const price = Number(form.price.replace(",", "."));
    const area = Number(form.area.replace(",", "."));
    if (Number.isNaN(price) || price <= 0) {
      setError("Kaufpreis: keine gültige Zahl.");
      return;
    }
    if (Number.isNaN(area) || area <= 0) {
      setError("Wohnfläche: keine gültige Zahl.");
      return;
    }
    if (!form.bundesland.trim()) {
      setError("Bundesland fehlt.");
      return;
    }
    setBusy(true);
    try {
      await createListing({
        price,
        living_area_sqm: area,
        bundesland: form.bundesland.trim(),
        ort: form.ort.trim(),
        rooms: form.rooms ? Number(form.rooms.replace(",", ".")) : undefined,
        year_built: form.year ? Number(form.year) : undefined,
      });
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: number) {
    try {
      await deleteListing(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  // Curried change handler: one factory instead of six inline arrow props.
  const set = (key: keyof typeof EMPTY_FORM) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <div className="pane-scroll">
      <form className="card-form" onSubmit={onSubmit}>
        <h3>Objekt erfassen</h3>
        <label>
          Kaufpreis (€)
          <input
            value={form.price}
            onChange={set("price")}
            inputMode="decimal"
            placeholder="300000"
          />
        </label>
        <label>
          Wohnfläche (m²)
          <input value={form.area} onChange={set("area")} inputMode="decimal" placeholder="100" />
        </label>
        <label>
          Bundesland
          <input value={form.bundesland} onChange={set("bundesland")} placeholder="Niedersachsen" />
        </label>
        <label>
          Ort (optional)
          <input value={form.ort} onChange={set("ort")} placeholder="Lingen" />
        </label>
        <label>
          Zimmer (optional)
          <input value={form.rooms} onChange={set("rooms")} inputMode="decimal" />
        </label>
        <label>
          Baujahr (optional)
          <input value={form.year} onChange={set("year")} inputMode="numeric" />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Speichert …" : "Speichern"}
        </button>
      </form>

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      {items.length === 0 ? (
        <p className="empty">
          Noch keine Objekte gespeichert. Erfasse oben dein erstes Objekt — nur Objektdaten, keine
          Anbieterkontakte.
        </p>
      ) : (
        <table className="listing-table">
          <thead>
            <tr>
              <th>Ort</th>
              <th>BL</th>
              <th>Typ</th>
              <th>Preis</th>
              <th>m²</th>
              <th>€/m²</th>
              <th>Zimmer</th>
              <th>Baujahr</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id}>
                <td>{it.ort || "—"}</td>
                <td>{it.bundesland}</td>
                <td>{it.object_type}</td>
                <td className="num">{eur(it.price)}</td>
                <td className="num">{num(it.living_area_sqm)}</td>
                <td className="num">{eur(it.price_per_sqm)}</td>
                <td className="num">{it.rooms ?? "—"}</td>
                <td className="num">{it.year_built ?? "—"}</td>
                <td>
                  <button
                    type="button"
                    className="del"
                    onClick={() => void onDelete(it.id)}
                    aria-label={`Objekt ${it.id} löschen`}
                  >
                    Löschen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
