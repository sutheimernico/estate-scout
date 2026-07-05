import { type FormEvent, useRef, useState } from "react";

import { AmortizationTable, type AnnuityResult } from "./AmortizationTable";
import { type AskResponse, ask, type ToolCall } from "./api";

interface Msg {
  id: number;
  role: "user" | "assistant";
  text: string;
  response?: AskResponse;
}

// Pull the annuity tool call (with a schedule) out of a response, if the assistant made one.
function annuityCall(r?: AskResponse): ToolCall | undefined {
  return r?.tool_calls.find(
    (t) => t.name === "annuity" && "remaining_debt_by_year" in t.result,
  );
}

const FALLBACK_DISCLAIMER =
  "Hinweis: keine Steuer-, Anlage- oder Finanzierungsberatung.";

export function App() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(1); // stable monotonic id; a ref avoids a re-render per message

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    setError(null);
    setMessages((m) => [...m, { id: nextId.current++, role: "user", text: q }]);
    setInput("");
    setLoading(true);
    try {
      const resp = await ask(q);
      setMessages((m) => [
        ...m,
        { id: nextId.current++, role: "assistant", text: resp.answer, response: resp },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  const lastDisclaimer = [...messages].reverse().find((m) => m.response)?.response?.disclaimer;

  return (
    <div className="app">
      <header className="header">
        <h1>
          estate<span className="dot">·</span>scout
        </h1>
        <p>Lokaler Immobilien-Assistent — Wissen aus der Wissensbasis, Zahlen aus geprüftem Code.</p>
      </header>

      <div className="messages">
        {messages.length === 0 && (
          <div className="bubble assistant">
            <div className="answer">
              Frag mich etwas zu Kauf, Finanzierung oder Lage — z.B. „Was zahle ich monatlich für
              300.000 € bei 3,6 % Zins und 2 % Tilgung?“
            </div>
          </div>
        )}
        {messages.map((m) => {
          const ann = annuityCall(m.response);
          return (
            <div key={m.id} className={`bubble ${m.role}`}>
              <div className="answer">{m.text}</div>
              {ann && <AmortizationTable result={ann.result as unknown as AnnuityResult} />}
              {m.response && m.response.sources.length > 0 && (
                <div className="sources">
                  {m.response.sources.map((s) => (
                    <span key={s} className="chip">
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {error && <div className="error">{error}</div>}

      <form className="composer" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Deine Frage…"
          aria-label="Frage"
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? "…" : "Fragen"}
        </button>
      </form>

      <footer className="disclaimer">{lastDisclaimer ?? FALLBACK_DISCLAIMER}</footer>
    </div>
  );
}
