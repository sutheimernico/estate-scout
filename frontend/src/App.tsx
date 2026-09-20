import { useState } from "react";

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

export function App() {
  const [tab, setTab] = useState<TabId>("chat");

  return (
    <div className="app">
      <header className="header">
        <h1>
          estate<span className="dot">·</span>scout
        </h1>
        <p>Lokaler Immobilien-Assistent — Wissen aus der Wissensbasis, Zahlen aus geprüftem Code.</p>
        <nav className="tabs" role="tablist" aria-label="Bereiche">
          {TABS.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              className={tab === t.id ? "tab active" : "tab"}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      {/* Panes stay mounted (hidden, not unmounted) so each tab keeps its state. */}
      <div className="pane" hidden={tab !== "chat"}>
        <Chat />
      </div>
      <div className="pane" hidden={tab !== "rechner"}>
        <CalcForms />
      </div>
      <div className="pane" hidden={tab !== "objekte"}>
        <Listings />
      </div>

      <footer className="disclaimer">{DISCLAIMER}</footer>
    </div>
  );
}
