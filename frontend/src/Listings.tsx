// Saved property objects: intake form + table over /api/listings, with the score drilldown.
// Object attributes only — never seller contact data (ADR-0001 / DSGVO).

import { type ChangeEvent, type FormEvent, useState } from "react";

import {
  createListing,
  deleteListing,
  enrichListing,
  type Listing,
  type ScoreReport,
  scoreListing,
} from "./api";
import { eur, num } from "./format";
import { ScoreDrilldown } from "./ScoreDrilldown";
import { useListings } from "./useListings";

const EMPTY_FORM = { price: "", area: "", bundesland: "", ort: "", rooms: "", year: "" };

function parseRent(raw: string): number | undefined {
  const value = Number(raw.replace(",", "."));
  return raw.trim() === "" || Number.isNaN(value) || value <= 0 ? undefined : value;
}

export function Listings() {
  const { items, error, setError, refresh } = useListings();
  const [form, setForm] = useState(EMPTY_FORM);
  const [busy, setBusy] = useState(false);
  // per-listing UI state, keyed by id — one open row, one report cache, one pending id
  const [openId, setOpenId] = useState<number | null>(null);
  const [reports, setReports] = useState<Record<number, ScoreReport>>({});
  const [rents, setRents] = useState<Record<number, string>>({});
  const [pendingId, setPendingId] = useState<number | null>(null);

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

  async function onEvaluate(id: number) {
    setError(null);
    setPendingId(id);
    try {
      await enrichListing(id);
      const report = await scoreListing(id, parseRent(rents[id] ?? ""));
      setReports((r) => ({ ...r, [id]: report }));
      setOpenId(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPendingId(null);
    }
  }

  async function onToggle(id: number) {
    if (openId === id) {
      setOpenId(null);
      return;
    }
    setOpenId(id);
    if (reports[id]) return;
    try {
      const report = await scoreListing(id, parseRent(rents[id] ?? ""));
      setReports((r) => ({ ...r, [id]: report }));
    } catch (err) {
      // 409 = never enriched: not an error, the row simply offers the button instead
      setReports((r) => ({ ...r }));
      if (!(err instanceof Error) || !err.message.includes("enrich")) {
        setError(err instanceof Error ? err.message : String(err));
      }
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
              <th>Score</th>
              <th></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <ListingRow
                key={it.id}
                listing={it}
                open={openId === it.id}
                pending={pendingId === it.id}
                report={reports[it.id]}
                rent={rents[it.id] ?? ""}
                onRentChange={(value) => setRents((r) => ({ ...r, [it.id]: value }))}
                onToggle={() => void onToggle(it.id)}
                onEvaluate={() => void onEvaluate(it.id)}
                onDelete={() => void onDelete(it.id)}
              />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

interface RowProps {
  listing: Listing;
  open: boolean;
  pending: boolean;
  report?: ScoreReport;
  rent: string;
  onRentChange: (value: string) => void;
  onToggle: () => void;
  onEvaluate: () => void;
  onDelete: () => void;
}

function ScoreBadge({ listing }: { listing: Listing }) {
  if (!listing.score || listing.score.total === null) return <span className="badge muted">—</span>;
  const strength = listing.score.confidence >= 0.75 ? "high" : "low";
  return (
    <span className={`badge score-${strength}`} title={`Datenlage ${num(listing.score.confidence * 100, 0)} %`}>
      {listing.score.total}
    </span>
  );
}

function ListingRow({
  listing,
  open,
  pending,
  report,
  rent,
  onRentChange,
  onToggle,
  onEvaluate,
  onDelete,
}: RowProps) {
  return (
    <>
      <tr>
        <td>{listing.ort || "—"}</td>
        <td>{listing.bundesland}</td>
        <td>{listing.object_type}</td>
        <td className="num">{eur(listing.price)}</td>
        <td className="num">{num(listing.living_area_sqm)}</td>
        <td className="num">{eur(listing.price_per_sqm)}</td>
        <td className="num">
          <ScoreBadge listing={listing} />
        </td>
        <td>
          <button
            type="button"
            className="del"
            onClick={onToggle}
            aria-expanded={open}
            aria-label={`Bewertung von Objekt ${listing.id} ${open ? "schließen" : "anzeigen"}`}
          >
            {open ? "Zuklappen" : "Details"}
          </button>
        </td>
        <td>
          <button
            type="button"
            className="del"
            onClick={onDelete}
            aria-label={`Objekt ${listing.id} löschen`}
          >
            Löschen
          </button>
        </td>
      </tr>
      {open && (
        <tr>
          <td colSpan={9}>
            <div className="drilldown">
              <div className="drilldown-controls">
                <label>
                  Kaltmiete (€/Monat, optional)
                  <input
                    value={rent}
                    onChange={(e) => onRentChange(e.target.value)}
                    inputMode="decimal"
                    placeholder="1000"
                  />
                </label>
                <button type="button" onClick={onEvaluate} disabled={pending}>
                  {pending ? "Bewertet …" : "Anreichern + bewerten"}
                </button>
              </div>
              {report ? (
                <ScoreDrilldown report={report} />
              ) : (
                <p className="empty">
                  Noch keine Bewertung. „Anreichern + bewerten“ holt die öffentlichen Referenzdaten
                  und berechnet den Score.
                </p>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
