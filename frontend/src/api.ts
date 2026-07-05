// Types mirror the FastAPI AskResponse (src/estatescout/api.py).

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface AskResponse {
  answer: string;
  tool_calls: ToolCall[];
  sources: string[];
  disclaimer: string;
}

export async function ask(question: string): Promise<AskResponse> {
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    if (res.status === 503) {
      throw new Error(
        "Ollama ist nicht erreichbar. Starte den lokalen Server (ollama serve) und ziehe ein Modell.",
      );
    }
    throw new Error(`Fehler ${res.status}`);
  }
  return res.json();
}
