import { useState } from "react";

// A shell command with a copy button; falls back to showing the command only when the
// clipboard API is unavailable (insecure origin, tests).
export function CopyCommand({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* the command stays visible and selectable */
    }
  }
  return (
    <div className="cmd">
      <code>{command}</code>
      <button type="button" className="btn ghost sm" onClick={() => void copy()}>
        {copied ? "Kopiert" : "Kopieren"}
      </button>
    </div>
  );
}
