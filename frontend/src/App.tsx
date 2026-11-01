import { type KeyboardEvent, useLayoutEffect, useRef, useState } from "react";

import { CalcForms } from "./CalcForms";
import { Chat } from "./Chat";
import { Listings } from "./Listings";

// `as const` freezes the literals so TabId is the union "chat" | "rechner" | "objekte",
// not the widened `string` — typos in setTab() become compile errors.
const TABS = [
  { id: "chat", label: "Chat" },
  { id: "rechner", label: "Rechner" },
  { id: "objekte", label: "Objekte" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const DISCLAIMER =
  "Hinweis: keine Steuer-, Anlage- oder Finanzierungsberatung. Steuersätze und Zinsen veralten.";

// Vermessungspunkt: the survey mark that anchors every Flurkarte.
function BrandMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 34 34" aria-hidden="true">
      <circle cx="17" cy="17" r="9" fill="none" stroke="#142029" strokeWidth="1.5" />
      <circle cx="17" cy="17" r="3" fill="#c0301c" />
      <path d="M17 1v10M17 23v10M1 17h10M23 17h10" stroke="#142029" strokeWidth="1.5" />
    </svg>
  );
}

export function App() {
  const [tab, setTab] = useState<TabId>("chat");
  const navRef = useRef<HTMLDivElement>(null);
  const [indicator, setIndicator] = useState<{ x: number; w: number } | null>(null);

  // The red tick under the active tab slides between tabs (transform only, so it stays on
  // the compositor). Measured after layout; in jsdom every width is 0, so it simply hides.
  useLayoutEffect(() => {
    const el = navRef.current?.querySelector<HTMLElement>('[aria-selected="true"]');
    if (el && el.offsetWidth > 0) setIndicator({ x: el.offsetLeft, w: el.offsetWidth });
  }, [tab]);

  function onKeyDown(e: KeyboardEvent) {
    const i = TABS.findIndex((t) => t.id === tab);
    let next = i;
    if (e.key === "ArrowRight") next = (i + 1) % TABS.length;
    else if (e.key === "ArrowLeft") next = (i + TABS.length - 1) % TABS.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = TABS.length - 1;
    else return;
    e.preventDefault();
    setTab(TABS[next].id);
    navRef.current?.querySelector<HTMLElement>(`#tab-${TABS[next].id}`)?.focus();
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <BrandMark />
          <div>
            <h1>
              estate<span className="dot">·</span>scout
            </h1>
            <p>Lokaler Immobilien-Assistent für Kauf und Finanzierung</p>
          </div>
        </div>
        <div className="tabs" role="tablist" aria-label="Bereiche" ref={navRef} onKeyDown={onKeyDown}>
          {TABS.map((t) => (
            <button
              key={t.id}
              id={`tab-${t.id}`}
              role="tab"
              type="button"
              aria-selected={tab === t.id}
              aria-controls={`pane-${t.id}`}
              tabIndex={tab === t.id ? 0 : -1}
              className="tab"
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
          {indicator && (
            <span
              className="tab-ind"
              aria-hidden="true"
              style={{ transform: `translateX(${indicator.x}px) scaleX(${indicator.w / 100})` }}
            />
          )}
        </div>
      </header>

      {/* Panes stay mounted (hidden, not unmounted) so each tab keeps its state. */}
      <div className="pane" role="tabpanel" id="pane-chat" aria-labelledby="tab-chat" hidden={tab !== "chat"}>
        <Chat />
      </div>
      <div className="pane" role="tabpanel" id="pane-rechner" aria-labelledby="tab-rechner" hidden={tab !== "rechner"}>
        <CalcForms />
      </div>
      <div className="pane" role="tabpanel" id="pane-objekte" aria-labelledby="tab-objekte" hidden={tab !== "objekte"}>
        <Listings />
      </div>

      <footer className="disclaimer">{DISCLAIMER}</footer>
    </div>
  );
}
