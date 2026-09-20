// The honest-harness claim, made inspectable: every tool the assistant called, with the exact
// arguments it passed and the exact result it got back. Collapsed by default.

import { type ToolCall } from "./api";

export function ToolTrace({ calls }: { calls: ToolCall[] }) {
  if (calls.length === 0) return null;
  return (
    // <details> gives the disclosure behaviour (and its a11y semantics) without any state.
    <details className="tool-trace">
      <summary>Werkzeuge ({calls.length})</summary>
      {calls.map((call, i) => (
        <div className="tool-call" key={`${call.name}-${i}`}>
          <code className="tool-name">{call.name}</code>
          <div className="tool-io">
            <span>Eingaben</span>
            <code>{JSON.stringify(call.args)}</code>
          </div>
          <div className="tool-io">
            <span>Ergebnis</span>
            <code>{JSON.stringify(call.result)}</code>
          </div>
        </div>
      ))}
      <p className="tool-note">
        Alle Zahlen stammen aus geprüftem Python (<code>finance/</code>), nicht aus dem Modell.
      </p>
    </details>
  );
}
