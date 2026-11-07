import { type FormEvent, useEffect, useRef, useState } from "react";

import { ask, type AskResponse, toKnownCalc } from "./api";
import { CalcResult } from "./CalcResult";
import { CopyCommand } from "./CopyCommand";
import { formatElapsed, type Problem, problemFrom, RECORDED_CATCH, sourceLabel, STARTERS, toolTitle, type TraceEntry, traceOf } from "./chatView";
import { bindUnits } from "./format";
import { HouseDrawing } from "./HouseDrawing";
import { ToolTrace } from "./ToolTrace";

interface Msg {
  id: number;
  question: string;
  answer: string;
  response: AskResponse;
}

function useElapsed(active: boolean): number {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!active) return;
    setSeconds(0);
    const started = Date.now();
    const timer = setInterval(() => setSeconds((Date.now() - started) / 1000), 1000);
    return () => clearInterval(timer);
  }, [active]);
  return seconds;
}

// Proof instead of a promise: one recorded case where the model garbled a figure and the code caught it.
function RecordedCatch() {
  const c = RECORDED_CATCH;
  const ref = useRef<HTMLElement>(null);
  // The strike-through and the verdict are timed animations: they start when the card is
  // actually on screen, not while it still sits under the composer on a short viewport.
  const [seen, setSeen] = useState(() => typeof IntersectionObserver === "undefined");
  useEffect(() => {
    const el = ref.current;
    if (seen || !el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setSeen(true);
          io.disconnect();
        }
      },
      { threshold: 0.6 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [seen]);
  return (
    <figure className={seen ? "catch seen" : "catch"} ref={ref}>
      <figcaption>
        <h3>Das Modell hat sich verschrieben. Die Prüfung hat es gemerkt.</h3>
      </figcaption>
      <dl className="catch-ledger">
        <div>
          <dt>Python rechnete ({c.toolLabel})</dt>
          <dd className="num">{c.toolValue}</dd>
        </div>
        <div className="catch-wrong">
          <dt>Das Modell schrieb</dt>
          <dd className="num">
            <span>{c.modelValue}</span>
          </dd>
        </div>
        <div className="catch-verdict">
          <dt>Zahlen-Prüfung</dt>
          <dd>
            Nicht belegt: <span className="num">181.210,86</span> stammt aus keinem Rechenergebnis.
          </dd>
        </div>
      </dl>
      <p className="catch-src">
        Aufgezeichneter Lauf, {c.model}, {c.recorded}. Frage: {bindUnits(c.question)} Die Prüfung wurde
        danach gebaut; ein Testfall fängt genau diese Zahl. Sie markiert, ohne die Antwort umzuschreiben.
      </p>
    </figure>
  );
}

function Intro({ onPick }: { onPick: (q: string) => void }) {
  return (
    <section className="intro">
      <div className="intro-text">
        <h2>
          <span>Der Assistent erklärt.</span> <span>Der Code rechnet.</span>
        </h2>
        <p>
          Fragen zu Kauf, Finanzierung und Lage beantwortet ein lokales Modell aus der Wissensbasis.
          Jede Zahl kommt aus geprüftem Python und steht in der Rechenspur, mit Eingaben und Ergebnis.
        </p>
        <ul className="starters" aria-label="Beispielfragen">
          {STARTERS.map((s, i) => (
            <li key={s.label} className="reveal" style={{ ["--i" as string]: i + 2 }}>
              <button type="button" onClick={() => onPick(s.question)}>
                <span className="starter-title">{s.label}</span>
                <span className="starter-q">{bindUnits(s.question)}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="intro-figure">
        <HouseDrawing />
        <RecordedCatch />
      </div>
    </section>
  );
}

function TraceList({ entries }: { entries: TraceEntry[] }) {
  return (
    <ol>
      {entries.map((t) => (
        <li key={t.n}>
          <span className="trace-n num">{t.n}</span>
          <div>
            <strong>{t.title}</strong>
            <p>{t.summary || "ohne Eingaben"}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

function Waiting({ question, seconds, onCancel }: { question: string; seconds: number; onCancel: () => void }) {
  return (
    <article className="turn waiting" aria-live="polite">
      <p className="turn-q">{bindUnits(question)}</p>
      <div className="wait">
        <span className="wait-rule" aria-hidden="true" />
        <p>
          Das Modell liest die Wissensbasis und ruft die Rechner auf. Laufzeit{" "}
          <span className="num">{formatElapsed(seconds)}</span>
          {seconds > 20 && <span className="wait-hint"> Auf der CPU dauert die erste Antwort oft über eine Minute.</span>}
        </p>
        <button type="button" className="btn ghost sm" onClick={onCancel}>
          Abbrechen
        </button>
      </div>
    </article>
  );
}

function ProblemNotice({ problem, onRetry }: { problem: Problem; onRetry: () => void }) {
  return (
    <div className="problem" role="alert">
      <h3>{problem.title}</h3>
      <p>{problem.body}</p>
      {problem.command && <CopyCommand command={problem.command} />}
      {problem.retry && (
        <button type="button" className="btn sm" onClick={onRetry}>
          Nochmal fragen
        </button>
      )}
    </div>
  );
}

export function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [problem, setProblem] = useState<Problem | null>(null);
  const lastQuestion = useRef("");
  const nextId = useRef(1); // stable monotonic id; a ref avoids a re-render per message
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const seconds = useElapsed(pending !== null);
  const trace = traceOf(messages.map((m) => ({ id: m.id, response: m.response })));

  useEffect(() => {
    // Nothing to follow on the empty intro: scrolling there would open the page half-way down.
    if (messages.length === 0 && pending === null && problem === null) return;
    // scrollIntoView is not implemented in jsdom — the optional call keeps tests green
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, pending, problem]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || pending !== null) return;
    lastQuestion.current = q;
    setProblem(null);
    setInput("");
    setPending(q);
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      const resp = await ask(q, ctrl.signal);
      setMessages((m) => [...m, { id: nextId.current++, question: q, answer: resp.answer, response: resp }]);
    } catch (err) {
      setProblem(problemFrom(err));
    } finally {
      setPending(null);
      abortRef.current = null;
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void send(input);
  }

  const empty = messages.length === 0 && pending === null && problem === null;

  return (
    <div className={trace.length > 0 ? "chat has-trace" : "chat"}>
      <div className="chat-main">
        {empty && <Intro onPick={(q) => void send(q)} />}

        <div className="turns">
          {messages.map((m) => (
            <article key={m.id} className="turn">
              <p className="turn-q">{bindUnits(m.question)}</p>
              <div className="turn-a">
                <p className="answer">{bindUnits(m.answer)}</p>
                {m.response.unverified_numbers && m.response.unverified_numbers.length > 0 && (
                  <div className="number-warning" role="alert">
                    <strong>Nicht belegt:</strong> {m.response.unverified_numbers.join(", ")} stammt aus
                    keinem Rechenergebnis. Bitte gegen die Zahlen unten prüfen.
                  </div>
                )}
                {m.response.tool_calls.map((t, i) => {
                  const known = toKnownCalc(t.name, t.result);
                  return known ? (
                    <div className="stamped sheet" key={`${m.id}-${i}`}>
                      <CalcResult calc={known} args={t.args} compact />
                      <p className="stamp">
                        Zahl aus dem Rechner „{toolTitle(t.name)}“, gerechnet von Python
                      </p>
                    </div>
                  ) : null;
                })}
                {trace.some((t) => t.messageId === m.id) && (
                  <section className="trace-inline" aria-label="Rechenspur">
                    <h4>Rechenspur</h4>
                    <TraceList entries={trace.filter((t) => t.messageId === m.id)} />
                  </section>
                )}
                <ToolTrace calls={m.response.tool_calls} />
                {m.response.sources.length > 0 && (
                  <p className="sources">
                    <span>Gelesen in</span>
                    {m.response.sources.map((s) => (
                      <span key={s} className="tag">
                        {sourceLabel(s)}
                      </span>
                    ))}
                  </p>
                )}
              </div>
            </article>
          ))}
          {pending !== null && (
            <Waiting question={pending} seconds={seconds} onCancel={() => abortRef.current?.abort()} />
          )}
          {problem && <ProblemNotice problem={problem} onRetry={() => void send(lastQuestion.current)} />}
          <div ref={endRef} />
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Frage stellen"
            aria-label="Frage"
            autoComplete="off"
          />
          <button type="submit" className="btn" disabled={!input.trim() || pending !== null}>
            Fragen
          </button>
        </form>
      </div>

      {trace.length > 0 && (
        <aside className="rechenspur" aria-label="Rechenspur">
          <h3>Rechenspur</h3>
          <TraceList entries={trace} />
          <p className="trace-note">Jeder Schritt wurde von Python gerechnet, nicht vom Modell.</p>
        </aside>
      )}
    </div>
  );
}
