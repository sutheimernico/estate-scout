// Saved property objects: tiles over /api/listings, a capture drawer and a detail drawer with the
// score drilldown. Object attributes only — never seller contact data (ADR-0001 / DSGVO).

import { type FormEvent, useState } from "react";

import {
  createListing,
  deleteListing,
  enrichListing,
  type Listing,
  type ScoreReport,
  scoreListing,
} from "./api";
import { FieldShell } from "./FieldShell";
import { eur, num } from "./format";
import {
  BUNDESLAENDER,
  bundeslandName,
  DEFAULT_BUNDESLAND,
  EXAMPLE_FEATURE,
  EXAMPLE_RENT,
  objectTypeLabel,
} from "./labels";
import { type FormErrors, type ListingForm, effectiveScore, parseListingForm, parseRent, roomsAndYear, scoreNote } from "./listingView";
import { ObjectIcon } from "./ObjectIcon";
import { ScoreDrilldown } from "./ScoreDrilldown";
import { CoveragePips, ScoreScale } from "./ScoreScale";
import { Sheet } from "./Sheet";
import { useListings } from "./useListings";

const EMPTY_FORM: ListingForm = {
  price: "",
  area: "",
  bundesland: DEFAULT_BUNDESLAND,
  ort: "",
  rooms: "",
  year: "",
  objectType: "wohnung",
};

// The example object ships with a rent that completes its data coverage; real objects start empty.
const isExample = (l: Listing) => l.features.includes(EXAMPLE_FEATURE);
const placeOf = (l: Listing) => l.ort.replace(/\s*\(Beispiel\)\s*$/, "") || "Ohne Ortsangabe";

const message = (err: unknown) => (err instanceof Error ? err.message : String(err));

function CaptureForm({ onSaved, onError }: { onSaved: () => Promise<void>; onError: (m: string) => void }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [busy, setBusy] = useState(false);
  const set = (key: keyof ListingForm) => (value: string) => setForm((f) => ({ ...f, [key]: value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    const parsed = parseListingForm(form);
    if (!parsed.ok) {
      setErrors(parsed.errors);
      return;
    }
    setErrors({});
    setBusy(true);
    try {
      await createListing(parsed.listing);
      await onSaved();
    } catch (err) {
      onError(message(err));
      setBusy(false);
    }
  }

  return (
    <form className="capture" onSubmit={(e) => void submit(e)} noValidate>
      <fieldset className="type-pick">
        <legend>Objektart</legend>
        {(["wohnung", "haus", "grundstueck"] as const).map((t) => (
          <label key={t} className={form.objectType === t ? "type-opt on" : "type-opt"}>
            <input
              type="radio"
              name="objectType"
              value={t}
              checked={form.objectType === t}
              onChange={() => set("objectType")(t)}
            />
            <ObjectIcon type={t} size={44} />
            <span>{objectTypeLabel(t)}</span>
          </label>
        ))}
      </fieldset>
      <FieldShell label="Kaufpreis" unit="€" error={errors.price}>
        {(id) => (
          <input id={id} value={form.price} onChange={(e) => set("price")(e.target.value)} inputMode="decimal" placeholder="300.000" autoComplete="off" />
        )}
      </FieldShell>
      <FieldShell label="Wohnfläche" unit="m²" error={errors.area}>
        {(id) => (
          <input id={id} value={form.area} onChange={(e) => set("area")(e.target.value)} inputMode="decimal" placeholder="100" autoComplete="off" />
        )}
      </FieldShell>
      <FieldShell label="Bundesland" error={errors.bundesland}>
        {(id) => (
          <select id={id} value={form.bundesland} onChange={(e) => set("bundesland")(e.target.value)}>
            {BUNDESLAENDER.map((b) => (
              <option key={b.code} value={b.code}>
                {b.name}
              </option>
            ))}
          </select>
        )}
      </FieldShell>
      <FieldShell label="Ort" optional>
        {(id) => <input id={id} value={form.ort} onChange={(e) => set("ort")(e.target.value)} placeholder="Lingen" autoComplete="off" />}
      </FieldShell>
      <div className="capture-pair">
        <FieldShell label="Zimmer" optional error={errors.rooms}>
          {(id) => <input id={id} value={form.rooms} onChange={(e) => set("rooms")(e.target.value)} inputMode="decimal" autoComplete="off" />}
        </FieldShell>
        <FieldShell label="Baujahr" optional error={errors.year}>
          {(id) => <input id={id} value={form.year} onChange={(e) => set("year")(e.target.value)} inputMode="numeric" autoComplete="off" />}
        </FieldShell>
      </div>
      <p className="capture-note">Nur Objektdaten, keine Anbieterkontakte.</p>
      <button type="submit" className="btn" disabled={busy}>
        {busy ? "Speichert …" : "Objekt speichern"}
      </button>
    </form>
  );
}

interface DetailProps {
  listing: Listing;
  report?: ScoreReport;
  rent: string;
  pending: boolean;
  onRentChange: (value: string) => void;
  onEvaluate: () => void;
  onDelete: () => void;
}

function Detail({ listing, report, rent, pending, onRentChange, onEvaluate, onDelete }: DetailProps) {
  const [confirm, setConfirm] = useState(false);
  const extra = roomsAndYear(listing);
  return (
    <div className="detail">
      <div className="detail-id">
        <ObjectIcon type={listing.object_type} size={64} />
        <div>
          <p className="detail-place">
            {placeOf(listing)}
            {isExample(listing) && <span className="tag">Beispiel</span>}
          </p>
          <p className="detail-sub">
            {objectTypeLabel(listing.object_type)} · {bundeslandName(listing.bundesland)}
          </p>
        </div>
      </div>
      <dl className="detail-facts">
        <div>
          <dt>Kaufpreis</dt>
          <dd className="num">{eur(listing.price)}</dd>
        </div>
        <div>
          <dt>Fläche</dt>
          <dd className="num">{num(listing.living_area_sqm)} m²</dd>
        </div>
        <div>
          <dt>Preis je m²</dt>
          <dd className="num">{eur(listing.price_per_sqm)}</dd>
        </div>
      </dl>
      {extra && <p className="detail-extra">{extra}</p>}

      <div className="detail-rent">
        <FieldShell label="Kaltmiete pro Monat" optional unit="€">
          {(id) => (
            <input
              id={id}
              value={rent}
              onChange={(e) => onRentChange(e.target.value)}
              inputMode="decimal"
              placeholder="1.000"
              autoComplete="off"
            />
          )}
        </FieldShell>
        <button type="button" className="btn" onClick={onEvaluate} disabled={pending}>
          {pending ? "Bewertet …" : "Anreichern + bewerten"}
        </button>
      </div>

      {isExample(listing) && (
        <p className="detail-note">
          Beispielobjekt mit fest hinterlegten, erfundenen Referenzdaten. Es zeigt den Score bei voller
          Datenlage (4/4). Mit Kaltmiete ergibt sich der Gesamtscore.
        </p>
      )}
      {report ? (
        <ScoreDrilldown report={report} />
      ) : (
        <p className="detail-note">
          Noch keine Bewertung. „Anreichern + bewerten“ holt die öffentlichen Referenzdaten und berechnet
          den Score.
        </p>
      )}

      <div className="detail-delete">
        {confirm ? (
          <>
            <span>Objekt wirklich löschen?</span>
            <button type="button" className="btn danger sm" onClick={onDelete}>
              Ja, löschen
            </button>
            <button type="button" className="btn ghost sm" onClick={() => setConfirm(false)}>
              Behalten
            </button>
          </>
        ) : (
          <button type="button" className="btn danger sm" onClick={() => setConfirm(true)}>
            Löschen
          </button>
        )}
      </div>
    </div>
  );
}

function Tile({ listing, report, index, onOpen }: { listing: Listing; report?: ScoreReport; index: number; onOpen: () => void }) {
  const score = effectiveScore(listing, report);
  const extra = roomsAndYear(listing);
  const note = scoreNote(listing, score);
  return (
    <li className="tile reveal" style={{ ["--i" as string]: index }}>
      <button
        type="button"
        className="tile-open"
        onClick={onOpen}
        aria-label={`${placeOf(listing)}: Bewertung von Objekt ${listing.id} anzeigen`}
      >
        <span className="tile-top">
          <ObjectIcon type={listing.object_type} />
          <span className="tile-kind">
            <span>{objectTypeLabel(listing.object_type)}</span>
            {isExample(listing) && <span className="tag">Beispiel</span>}
          </span>
        </span>
        <span className="tile-place">{placeOf(listing)}</span>
        <span className="tile-region">{bundeslandName(listing.bundesland)}</span>
        <span className="tile-price num">{eur(listing.price)}</span>
        <span className="tile-meta num">
          {num(listing.living_area_sqm)} m² · {eur(listing.price_per_sqm)}/m²
        </span>
        {extra && <span className="tile-extra">{extra}</span>}
        <span className="tile-score">
          <ScoreScale total={score?.total ?? null} />
          <span className="tile-coverage">
            <CoveragePips confidence={score?.confidence ?? 0} />
            <span>Datenlage</span>
          </span>
          {note && <span className="tile-note">{note}</span>}
        </span>
      </button>
    </li>
  );
}

function EmptyState({ onCapture }: { onCapture: () => void }) {
  return (
    <section className="objects-empty">
      <div className="empty-drawings" aria-hidden="true">
        <ObjectIcon type="wohnung" size={96} />
        <ObjectIcon type="haus" size={96} />
        <ObjectIcon type="grundstueck" size={96} />
      </div>
      <h3>Noch keine Objekte gespeichert</h3>
      <p>
        Erfasse ein Objekt mit Preis, Fläche und Bundesland. estate-scout holt öffentliche Referenzdaten
        und bewertet es mit Rendite, Preisniveau und Lage, ohne Werte zu erfinden. Nur Objektdaten,
        keine Anbieterkontakte.
      </p>
      <button type="button" className="btn" onClick={onCapture}>
        Erstes Objekt erfassen
      </button>
    </section>
  );
}

export function Listings() {
  const { items, error, setError, refresh } = useListings();
  const [capturing, setCapturing] = useState(false);
  // per-listing UI state, keyed by id — one open drawer, one report cache, one pending id
  const [openId, setOpenId] = useState<number | null>(null);
  const [reports, setReports] = useState<Record<number, ScoreReport>>({});
  const [rents, setRents] = useState<Record<number, string>>({});
  const rentOf = (l: Listing) => rents[l.id] ?? (isExample(l) ? EXAMPLE_RENT : "");
  const [pendingId, setPendingId] = useState<number | null>(null);
  const open = items.find((l) => l.id === openId);

  async function onDelete(id: number) {
    try {
      await deleteListing(id);
      setOpenId(null);
      await refresh();
    } catch (err) {
      setError(message(err));
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
      await refresh();
    } catch (err) {
      setError(message(err));
    } finally {
      setPendingId(null);
    }
  }

  async function onOpen(listing: Listing) {
    const id = listing.id;
    setOpenId(id);
    if (reports[id]) return;
    try {
      const report = await scoreListing(id, parseRent(rentOf(listing)));
      setReports((r) => ({ ...r, [id]: report }));
    } catch (err) {
      // 409 = never enriched: not an error, the drawer simply offers the button instead
      if (!(err instanceof Error) || !err.message.includes("enrich")) setError(message(err));
    }
  }

  const errorNode = error && (
    <div className="notice error" role="alert">
      {error}
    </div>
  );

  return (
    <div className="objects">
      <header className="objects-head">
        <div>
          <h2>Objekte</h2>
          <p>
            {items.length === 0
              ? "Deine Objektliste ist leer."
              : `${items.length} ${items.length === 1 ? "Objekt" : "Objekte"}, bewertet nach Rendite, Preisniveau und Lage.`}
          </p>
        </div>
      </header>

      {!capturing && !open && errorNode}

      {items.length === 0 ? (
        <EmptyState onCapture={() => setCapturing(true)} />
      ) : (
        <ul className="tiles">
          {items.map((it, i) => (
            <Tile key={it.id} listing={it} report={reports[it.id]} index={i} onOpen={() => void onOpen(it)} />
          ))}
          <li className="reveal" style={{ ["--i" as string]: items.length }}>
            <button type="button" className="tile-add" onClick={() => setCapturing(true)}>
              <span className="tile-add-plus" aria-hidden="true">+</span>
              Weiteres Objekt
            </button>
          </li>
        </ul>
      )}

      {capturing && (
        <Sheet title="Objekt erfassen" onClose={() => setCapturing(false)}>
          {errorNode}
          <CaptureForm
            onSaved={async () => {
              setCapturing(false);
              await refresh();
            }}
            onError={setError}
          />
        </Sheet>
      )}
      {open && (
        <Sheet title={`${placeOf(open)}, ${objectTypeLabel(open.object_type)}`} onClose={() => setOpenId(null)}>
          {errorNode}
          <Detail
            listing={open}
            report={reports[open.id]}
            rent={rentOf(open)}
            pending={pendingId === open.id}
            onRentChange={(value) => setRents((r) => ({ ...r, [open.id]: value }))}
            onEvaluate={() => void onEvaluate(open)}
            onDelete={() => void onDelete(open.id)}
          />
        </Sheet>
      )}
    </div>
  );
}
