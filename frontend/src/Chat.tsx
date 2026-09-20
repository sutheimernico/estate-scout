import { type FormEvent, useEffect, useRef, useState } from "react";

import { ask, type AskResponse, toKnownCalc } from "./api";
import { CalcResultCard } from "./CalcResultCard";

interface Msg {
  id: number;
  role: "user" | "assistant";
  text: string;
  response?: AskResponse;
}

export function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextId = useRef(1); // stable monotonic id; a ref avoids a re-render per message
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // scrollIntoView is not implemented in jsdom — the optional call keeps tests green
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    setError(null);
    setMessages((m) => [...m, { id: nextId.current++, role: "user", text: q }]);
    setInput("");
    setLoading(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      const resp = await ask(q, ctrl.signal);
      setMessages((m) => [
        ...m,
        { id: nextId.current++, role: "assistant", text: resp.answer, response: resp },
      ]);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setError("Anfrage abgebrochen.");
      } else {
        setError(err instanceof Error ? err.message : String(err));
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }

  return (
    <>
      <div className="messages" aria-live="polite">
        {messages.length === 0 && (
          <div className="bubble assistant">
            <div className="answer">
              Frag mich etwas zu Kauf, Finanzierung oder Lage — z.B. „Was zahle ich monatlich für
              300.000 € bei 3,6 % Zins und 2 % Tilgung?“
            </div>
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.role}`}>
            <div className="answer">{m.text}</div>
            {m.response?.tool_calls.map((t, i) => {
              const known = toKnownCalc(t.name, t.result);
              return known ? <CalcResultCard key={`${m.id}-${i}`} calc={known} /> : null;
            })}
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
        ))}
        {loading && (
          <div className="bubble assistant thinking">
            <span className="dots" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            Assistent denkt nach …
          </div>
        )}
        <div ref={endRef} />
      </div>

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      <form className="composer" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Deine Frage…"
          aria-label="Frage"
        />
        {loading ? (
          <button type="button" onClick={() => abortRef.current?.abort()}>
            Abbrechen
          </button>
        ) : (
          <button type="submit" disabled={!input.trim()}>
            Fragen
          </button>
        )}
      </form>
    </>
  );
}
