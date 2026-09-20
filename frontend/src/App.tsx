import { Chat } from "./Chat";

const DISCLAIMER =
  "Hinweis: keine Steuer-, Anlage- oder Finanzierungsberatung. Steuersätze und Zinsen veralten.";

export function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>
          estate<span className="dot">·</span>scout
        </h1>
        <p>Lokaler Immobilien-Assistent — Wissen aus der Wissensbasis, Zahlen aus geprüftem Code.</p>
      </header>

      <Chat />

      <footer className="disclaimer">{DISCLAIMER}</footer>
    </div>
  );
}
