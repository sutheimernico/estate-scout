"""The assistant loop: routes a question through RAG context and finance tools.

Flow: retrieve knowledge-base context → send system prompt + context + question to the model
with the finance tool schemas → run any requested tools (numbers from `finance/`) → feed the
results back → return the model's final grounded answer. The model never computes numbers; it
only selects tools and explains their exact results.
"""

import json
from dataclasses import dataclass, field

from estatescout.rag.embedder import Embedder
from estatescout.rag.index import RagIndex

from .chat import ChatModel
from .tools import dispatch, tool_specs

DISCLAIMER = (
    "Hinweis: keine Steuer-, Anlage- oder Finanzierungsberatung. Steuersätze und Zinsen "
    "veralten (Stand der Wissensbasis siehe Quellen)."
)

SYSTEM_PROMPT = (
    "Du bist ein sachlicher Immobilien-Assistent für den deutschen Wohnimmobilienmarkt "
    "(Fokus Niedersachsen und NRW). Regeln, die du strikt befolgst:\n"
    "1. Für JEDE Berechnung (Kreditrate, Kaufnebenkosten, Leistbarkeit, Rendite) rufst du das "
    "passende Tool auf und gibst dessen exakte Zahlen wieder. Du rechnest NIEMALS selbst und "
    "erfindest keine Zahlen.\n"
    "2. Bei Wissensfragen nutzt du die bereitgestellten Auszüge und nennst die Quelle "
    "(Dateiname in Klammern).\n"
    "3. Du gibst keine Steuer-, Anlage- oder Finanzierungsberatung — weise bei solchen Fragen "
    "darauf hin.\n"
    "4. Fehlt eine Angabe, die ein Tool braucht, fragst du nach, statt zu raten.\n"
    "Antworte auf Deutsch, knapp und konkret."
)


@dataclass
class AssistantResponse:
    answer: str
    tool_calls: list[dict] = field(default_factory=list)  # {name, args, result}
    sources: list[str] = field(default_factory=list)  # retrieved corpus doc names
    disclaimer: str = DISCLAIMER  # every response carries the honesty disclaimer


def _parse_tool_call(call: object) -> tuple[str, dict] | None:
    """Extract (name, args) from a model tool call; None if the structure is unusable.

    Ollama's contract is arguments-as-dict, but small local models occasionally emit a JSON
    string or garbage — degrade to empty args (dispatch then reports what is missing) instead
    of crashing the request.
    """
    if not isinstance(call, dict):
        return None
    fn = call.get("function")
    if not isinstance(fn, dict) or not isinstance(fn.get("name"), str):
        return None
    args = fn.get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    if not isinstance(args, dict):
        args = {}
    return fn["name"], args


class Assistant:
    def __init__(
        self,
        model: ChatModel,
        index: RagIndex | None = None,
        embedder: Embedder | None = None,
        *,
        k: int = 4,
        max_tool_rounds: int = 4,
    ):
        self.model = model
        self.index = index
        self.embedder = embedder
        self.k = k
        self.max_tool_rounds = max_tool_rounds

    def _context_message(self, question: str) -> tuple[dict | None, list[str]]:
        if self.index is None or self.embedder is None:
            return None, []
        hits = self.index.retrieve(question, self.embedder, k=self.k)
        if not hits:
            return None, []
        blocks = [f"[{h.source}] {h.heading}\n{h.text}" for h in hits]
        sources: list[str] = []
        for h in hits:
            if h.source not in sources:
                sources.append(h.source)
        content = (
            "Auszüge aus der Wissensbasis (nur für Wissensfragen nutzen, Quelle nennen):\n\n"
            + "\n\n---\n\n".join(blocks)
        )
        return {"role": "system", "content": content}, sources

    def ask(self, question: str) -> AssistantResponse:
        context_msg, sources = self._context_message(question)
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context_msg is not None:
            messages.append(context_msg)
        messages.append({"role": "user", "content": question})

        tool_calls: list[dict] = []
        specs = tool_specs()
        for _ in range(self.max_tool_rounds):
            msg = self.model.chat(messages, tools=specs)
            messages.append(msg)
            requested = msg.get("tool_calls") or []
            if not requested:
                return AssistantResponse(
                    answer=msg.get("content", ""), tool_calls=tool_calls, sources=sources
                )
            for call in requested:
                parsed = _parse_tool_call(call)
                if parsed is None:
                    messages.append(
                        {
                            "role": "tool",
                            "name": "unknown",
                            "content": json.dumps(
                                {"error": "malformed tool call"}, ensure_ascii=False
                            ),
                        }
                    )
                    continue
                name, args = parsed
                try:
                    result = dispatch(name, args)
                except (ValueError, TypeError, KeyError) as e:
                    result = {"error": str(e)}  # feed back so the model can correct itself
                tool_calls.append({"name": name, "args": args, "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "name": name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        # Tool budget exhausted: ask once more for a final answer without tools.
        final = self.model.chat(messages, tools=None)
        return AssistantResponse(
            answer=final.get("content", ""), tool_calls=tool_calls, sources=sources
        )
