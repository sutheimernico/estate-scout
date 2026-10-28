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
import {
  BUNDESLAENDER,
  bundeslandName,
  DEFAULT_BUNDESLAND,
  EXAMPLE_FEATURE,
  EXAMPLE_RENT,
  objectTypeLabel,
} from "./labels";
import { ScoreDrilldown } from "./ScoreDrilldown";
import { useListings } from "./useListings";

const EMPTY_FORM = {
  price: "",
  area: "",
  bundesland: DEFAULT_BUNDESLAND,
  ort: "",
  rooms: "",
  year: "",
};

// The example object ships with a rent that completes its data coverage; real objects start empty.
const isExample = (l: Listing) => l.features.includes(EXAMPLE_FEATURE);

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
  const rentOf = (l: Listing) => rents[l.id] ?? (isExample(l) ? EXAMPLE_RENT : "");
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

  async function onEvaluate(listing: Listing) {
    const id = listing.id;
    setError(null);
    setPendingId(id);
    try {
      // the example's reference data is fixed; the server refuses to re-enrich it
      if (!isExample(listing)) await enrichListing(id);
      const report = await scoreListing(id, parseRent(rentOf(listing)));
      setReports((r) => ({ ...r, [id]: report }));
      setOpenId(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPendingId(null);
    }
  }

  async function onToggle(listing: Listing) {
    const id = listing.id;
    if (openId === id) {
      setOpenId(null);
      return;
    }
    setOpenId(id);
    if (reports[id]) return;
    try {
      const report = await scoreListing(id, parseRent(rentOf(listing)));
      setReports((r) => ({ ...r, [id]: report }));
    } catch (err) {
      // 409 = never enriched: not an error, the row simply offers the button instead
      if (!(err instanceof Error) || !err.message.includes("enrich")) {
        setError(err instanceof Error ? err.message : String(err));
      }
    }
  }

  // Curried change handler: one factory instead of six inline arrow props.
  const set = (key: keyof typeof EMPTY_FORM) => (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
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
            placeholder="z. B. 300000"
          />
        </label>
        <label>
          Wohnfläche (m²)
          <input
            value={form.area}
            onChange={set("area")}
            inputMode="decimal"
            placeholder="z. B. 100"
          />
        </label>
        <label>
          Bundesland
          <select value={form.bundesland} onChange={set("bundesland")}>
            {BUNDESLAENDER.map((b) => (
              <option key={b.code} value={b.code}>
                {b.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Ort (optional)
          <input value={form.ort} onChange={set("ort")} placeholder="z. B. Lingen" />
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
              <th>Bundesland</th>
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
                rent={rentOf(it)}
                onRentChange={(value) => setRents((r) => ({ ...r, [it.id]: value }))}
                onToggle={() => void onToggle(it)}
                onEvaluate={() => void onEvaluate(it)}
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

// The freshest report wins over the list response: the list is scored without a rent (the
// table convention), the report may include the one the user just typed in. Reading only the
// list left the table at "—" while the drilldown already showed 67/100.
function ScoreBadge({ listing, report }: { listing: Listing; report?: ScoreReport }) {
  const score = report ?? listing.score;
  if (!score || score.total === null) return <span className="badge muted">—</span>;
  const strength = score.confidence >= 0.75 ? "high" : "low";
  return (
    <span
      className={`badge score-${strength}`}
      title={`Datenlage ${num(score.confidence * 100, 0)} %`}
    >
      {score.total}
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
        <td>{bundeslandName(listing.bundesland)}</td>
        <td>{objectTypeLabel(listing.object_type)}</td>
        <td className="num">{eur(listing.price)}</td>
        <td className="num">{num(listing.living_area_sqm)}</td>
        <td className="num">{eur(listing.price_per_sqm)}</td>
        <td className="num">
          <ScoreBadge listing={listing} report={report} />
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
                    placeholder="z. B. 1000"
                  />
                </label>
                <button type="button" onClick={onEvaluate} disabled={pending}>
                  {pending ? "Bewertet …" : "Anreichern + bewerten"}
                </button>
              </div>
              {isExample(listing) && (
                <p className="empty">
                  Beispielobjekt mit fest hinterlegten, erfundenen Referenzdaten — es zeigt den Score
                  bei voller Datenlage (4/4). Mit Kaltmiete ergibt sich der Gesamtscore.
                </p>
              )}
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
