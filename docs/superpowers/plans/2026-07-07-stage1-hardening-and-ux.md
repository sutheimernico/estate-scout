# Stage-1 Hardening & UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the robustness bugs found in the 2026-07-07 critical review and close the biggest UX gaps: typed tool dispatch, per-process RAG cache, retrieval threshold, two new investor calculators (operating costs, cash-on-cash equity return), assistant access to saved listings, and a three-tab frontend (Chat / Rechner / Objekte) with direct calculator forms and a listings view.

**Architecture:** Backend stays the honest-harness layering: `finance/` computes, `assistant/tools.py` adapts, `assistant/assistant.py` orchestrates, `api.py`/`cli.py` expose. All argument validation moves into `dispatch()` so the API and the LLM path share one guard. The frontend becomes a tabbed single-page app; all three panes stay mounted (hidden via the `hidden` attribute) so switching tabs never loses state; wire-data narrowing is confined to one function in `api.ts`.

**Tech Stack:** Python 3.11, FastAPI, httpx, NumPy, typer, pytest, ruff (line-length 100) · React 18 + TypeScript + Vite, vitest + @testing-library/react (use `fireEvent`, NOT `user-event` — it is not installed and must not be added).

**Context:** Repo `~/private/estate-scout`, branch `autopilot/work` (`main` is unborn — never switch). Gate: `uv run pytest -q` green AND `uv run ruff check .` clean; frontend gate: `cd frontend && npm test && npm run build`. 97 pytest tests + 3 vitest tests are green at plan time. One commit per task, Conventional Commits, English, imperative.

**Iron rules from PROJECT.md that this plan must respect:**
- Numbers only from `finance/` — the LLM never computes.
- No fabricated facts: config values carry `source` + `as_of`.
- No live Ollama/network in tests — use `FakeChat` / `FakeEmbedder` / `httpx.MockTransport`.
- Never commit red. German UI texts, English code/comments/commits.

**Review findings covered (file:line at plan time):**
1. `assistant/tools.py:199-208` — `dispatch()` checks only key presence; typed-wrong args (string principal, explicit `null`) crash as `TypeError` → API 500. (Tasks 1, 2)
2. `api.py:91` — `/api/finance/{calc}` takes an untyped `dict` body; `{"principal": "abc"}` → 500 instead of 400. (Task 1 fixes via dispatch; regression test added)
3. `assistant/assistant.py:96-98` — malformed `tool_calls` from the 7B model (missing keys, string `arguments`) raise uncaught `KeyError`/`TypeError`. (Task 2)
4. `rag/embedder.py:83-97` — `OllamaEmbedder` raises raw `httpx` errors, so `/api/ask` 500s (not 503) when Ollama is down during index build. (Task 3)
5. `rag/index.py:66-81` — retrieval has no similarity threshold; off-topic questions still get "Auszüge" context, inviting forced citations/hallucination. (Task 4)
6. `api.py:78-82` + `cli.py:126-129` — `RagIndex.build()` re-embeds the whole corpus on EVERY request/CLI call; `save()`/`load()` exist but are never used. (Task 5)
7. `finance/annuity.py:75-82`, `finance/affordability.py:53-60` — no upper bound on rates; `annual_rate=3.6` (percent-instead-of-fraction) silently accepted. (Task 6)
8. `config/rates.yaml:75,77-87` — `management_cost_eur_per_sqm` and `reference_interest` are declared but consumed by nothing (stale-risk dead config). (Task 7)
9. Missing investor math: operating-cost anchor and levered equity return. (Tasks 7, 8, 9)
10. Assistant and scout module are silos — the assistant cannot see saved listings. (Task 10)
11. No DELETE for listings in API/CLI. (Task 11)
12. `frontend/src/App.tsx:76` — `as unknown as AnnuityResult` double-cast; only the `annuity` tool result is ever rendered. (Tasks 12, 13, 14)
13. No calculator forms, no listings view, no waiting feedback, no abort, no aria-live, generic error texts. (Tasks 14–17)

**Explicitly OUT of scope (do not build):**
- Streaming responses (SSE) — deferred; the thinking indicator covers feedback for now.
- Code-level verification that free-text numbers match tool results (prompt-only honesty stays).
- SQLite schema migrations; scoring engine (PLAN.md Phase 8) and scout scoring tab (Phase 9).
- New knowledge-corpus documents.
- Verified fact for context: Bremen GrESt 5.5 % since 2025-07-01 is CORRECT in `config/rates.yaml` (checked 2026-07-07 against haufe.de + service.bremen.de) — do not "fix" it.

---

## File structure

**Create:**
- `src/estatescout/errors.py` — shared `OllamaUnavailable` (breaks the would-be rag→assistant import)
- `src/estatescout/finance/operating_costs.py` — Bewirtschaftungskosten estimator (config-anchored)
- `src/estatescout/finance/equity_return.py` — first-year cash-on-cash return
- `tests/test_finance_operating_costs.py`, `tests/test_finance_equity_return.py`
- `frontend/src/format.ts` — shared de-DE formatters (`eur`, `pct`, `num`)
- `frontend/src/CalcResultCard.tsx` — renders every calculator result type
- `frontend/src/Chat.tsx` — chat pane extracted from App (with polish)
- `frontend/src/CalcForms.tsx` — direct calculator forms (no LLM)
- `frontend/src/Listings.tsx` — listings table + intake form
- `frontend/src/Chat.test.tsx`, `frontend/src/CalcForms.test.tsx`, `frontend/src/Listings.test.tsx`

**Modify:**
- `src/estatescout/assistant/tools.py` — arg cleaning/coercion, injectable tools map, `listing_tools()`, 2 new tools
- `src/estatescout/assistant/assistant.py` — loop hardening, `min_score`, `extra_tools`, prompt rules
- `src/estatescout/assistant/chat.py` — import `OllamaUnavailable` from `errors`
- `src/estatescout/rag/embedder.py` — map httpx errors to `OllamaUnavailable`
- `src/estatescout/rag/index.py` — `min_score` filter, `_fingerprint`, `load_or_build()`
- `src/estatescout/finance/annuity.py`, `affordability.py` — fraction sanity bounds
- `src/estatescout/api.py` — index cache, listing tools wiring, DELETE endpoint
- `src/estatescout/cli.py` — `load_or_build`, listing tools, `opcosts`/`equity`/`scout delete` commands
- `config/rates.yaml` — add `bewirtschaftung`, remove two dead blocks
- `frontend/src/api.ts` (rewrite), `frontend/src/App.tsx` (tabs), `frontend/src/AmortizationTable.tsx` (use format.ts), `frontend/src/index.css` (tabs/forms/table styles), `frontend/src/App.test.tsx`

---

## Part A — Backend robustness

### Task 1: Type-validate and coerce tool arguments in `dispatch()`

The single guard for BOTH the API (`/api/finance/{calc}`) and the LLM tool path. Rules: explicit `null` counts as absent; numeric strings (`"300000"`) are coerced to float (7B models do this constantly); bools and non-coercible values are a loud `ValueError` (which both callers already translate: API → 400, loop → error fed back to the model).

**Files:**
- Modify: `src/estatescout/assistant/tools.py`
- Test: `tests/test_assistant_tools.py`, `tests/test_api.py`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_assistant_tools.py`:

```python
def test_dispatch_coerces_numeric_strings():
    out = dispatch(
        "annuity",
        {"principal": "300000", "annual_rate_percent": "3.6", "initial_repayment_percent": 2.0},
    )
    assert out["monthly_payment"] == pytest.approx(1_400.0)


def test_dispatch_rejects_non_numeric_string():
    with pytest.raises(ValueError, match="must be a number"):
        dispatch(
            "annuity",
            {"principal": "dreihundert", "annual_rate_percent": 3.6,
             "initial_repayment_percent": 2.0},
        )


def test_dispatch_rejects_bool_for_number():
    with pytest.raises(ValueError, match="must be a number"):
        dispatch(
            "annuity",
            {"principal": True, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0},
        )


def test_dispatch_rejects_number_for_string():
    with pytest.raises(ValueError, match="must be a string"):
        dispatch("purchase_costs", {"purchase_price": 300_000, "bundesland": 42})


def test_dispatch_treats_explicit_null_as_absent():
    out = dispatch(
        "annuity",
        {"principal": 300_000, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0,
         "annual_sondertilgung": None},
    )
    assert out["monthly_payment"] == pytest.approx(1_400.0)


def test_dispatch_null_required_arg_counts_as_missing():
    with pytest.raises(ValueError, match="missing required"):
        dispatch(
            "annuity",
            {"principal": None, "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0},
        )
```

And append to `tests/test_api.py` (regression for the reproduced 500):

```python
def test_finance_wrong_type_is_400():
    body = {"principal": "abc", "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0}
    assert client.post("/api/finance/annuity", json=body).status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_assistant_tools.py tests/test_api.py -q`
Expected: the 6 new tool tests FAIL (`TypeError` / `DID NOT RAISE`), `test_finance_wrong_type_is_400` FAILS with 500.

- [ ] **Step 3: Implement** — in `src/estatescout/assistant/tools.py`, insert directly above `def dispatch(...)`:

```python
def _clean_args(name: str, tool: Tool, args: dict) -> dict:
    """Drop explicit nulls, coerce numeric strings, and type-check against the tool spec.

    Local 7B models routinely send numbers as strings or explicit nulls — coerce what is
    safe, reject the rest loudly so the caller (API 400 / loop error-feedback) can react.
    """
    props = tool.spec["function"]["parameters"]["properties"]
    cleaned: dict = {}
    for key, value in args.items():
        if value is None:
            continue  # explicit null == absent; required-check below reports it
        expected = props.get(key, {}).get("type")
        if expected == "number":
            if isinstance(value, bool):
                raise ValueError(f"tool '{name}' argument '{key}' must be a number, got {value!r}")
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    raise ValueError(
                        f"tool '{name}' argument '{key}' must be a number, got {value!r}"
                    ) from None
        elif expected == "string" and not isinstance(value, str):
            raise ValueError(f"tool '{name}' argument '{key}' must be a string, got {value!r}")
        cleaned[key] = value
    return cleaned
```

Then replace the body of `dispatch()` with:

```python
def dispatch(name: str, args: dict) -> dict:
    """Validate, type-coerce and run the named finance tool. Numbers come from finance/."""
    if name not in TOOLS:
        raise ValueError(f"unknown tool '{name}' (known: {', '.join(sorted(TOOLS))})")
    tool = TOOLS[name]
    cleaned = _clean_args(name, tool, args)
    required = tool.spec["function"]["parameters"]["required"]
    missing = [r for r in required if r not in cleaned]
    if missing:
        raise ValueError(f"tool '{name}' missing required args: {', '.join(missing)}")
    return tool.run(cleaned)
```

- [ ] **Step 4: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all tests pass, ruff clean.

- [ ] **Step 5: Commit**

```bash
git add src/estatescout/assistant/tools.py tests/test_assistant_tools.py tests/test_api.py
git commit -m "fix(tools): validate and coerce tool argument types in dispatch"
```

### Task 2: Harden the assistant loop against malformed tool calls

**Files:**
- Modify: `src/estatescout/assistant/assistant.py`
- Test: `tests/test_assistant_loop.py`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_assistant_loop.py`:

```python
def test_malformed_tool_call_is_skipped_and_answer_still_returned():
    model = FakeChat(
        [
            {"role": "assistant", "content": "", "tool_calls": [{"function": {"nope": True}}]},
            _final("Das hat nicht geklappt — magst du die Frage umformulieren?"),
        ]
    )
    resp = Assistant(model).ask("kaputt?")
    assert resp.answer.startswith("Das hat nicht geklappt")
    assert resp.tool_calls == []


def test_string_tool_arguments_are_parsed_as_json():
    call = {
        "function": {
            "name": "annuity",
            "arguments": '{"principal": 300000, "annual_rate_percent": 3.6,'
            ' "initial_repayment_percent": 2.0}',
        }
    }
    model = FakeChat(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            _final("Die Rate beträgt 1.400 €."),
        ]
    )
    resp = Assistant(model).ask("Rate?")
    assert resp.tool_calls[0]["result"]["monthly_payment"] == pytest.approx(1_400.0)


def test_type_error_inside_tool_is_fed_back_not_raised():
    # bypasses dispatch coercion paths: unknown-string arg for a number that float() accepts
    # is coerced, so force a KeyError-ish structure instead: arguments as a list
    call = {"function": {"name": "annuity", "arguments": [1, 2, 3]}}
    model = FakeChat(
        [
            {"role": "assistant", "content": "", "tool_calls": [call]},
            _final("Mir fehlen die Angaben."),
        ]
    )
    resp = Assistant(model).ask("Rechne.")
    assert "error" in resp.tool_calls[0]["result"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_assistant_loop.py -q`
Expected: new tests FAIL (KeyError / TypeError / json decode issues).

- [ ] **Step 3: Implement** — in `src/estatescout/assistant/assistant.py`, insert above `class Assistant:`:

```python
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
```

Then replace the `for call in requested:` block inside `ask()` with:

```python
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
```

- [ ] **Step 4: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/estatescout/assistant/assistant.py tests/test_assistant_loop.py
git commit -m "fix(assistant): survive malformed tool calls from the model"
```

### Task 3: `OllamaUnavailable` shared; embedder degrades honestly

Today `OllamaEmbedder` raises raw `httpx.ConnectError` — `/api/ask` 500s instead of 503 when Ollama is down at index-build time. Move the exception to a neutral module (rag/ must not import assistant/) and map httpx errors.

**Files:**
- Create: `src/estatescout/errors.py`
- Modify: `src/estatescout/assistant/chat.py`, `src/estatescout/rag/embedder.py`
- Test: `tests/test_rag_embedder.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_rag_embedder.py`:

```python
def test_ollama_embedder_maps_connect_error_to_unavailable():
    from estatescout.errors import OllamaUnavailable

    def raise_connect(request):
        raise httpx.ConnectError("connection refused", request=request)

    client = httpx.Client(transport=httpx.MockTransport(raise_connect))
    with pytest.raises(OllamaUnavailable):
        OllamaEmbedder(client=client).embed(["hallo"])
```

(If `httpx`/`pytest` are not yet imported at the top of that test file, add the imports.)

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_rag_embedder.py -q`
Expected: FAIL — `ModuleNotFoundError: estatescout.errors`.

- [ ] **Step 3: Create `src/estatescout/errors.py`:**

```python
"""Shared error types (kept dependency-free so rag/ and assistant/ can both use them)."""


class OllamaUnavailable(RuntimeError):
    """Raised when the local Ollama server cannot be reached — callers degrade honestly."""
```

- [ ] **Step 4: In `src/estatescout/assistant/chat.py`**, delete the local `class OllamaUnavailable(RuntimeError): ...` definition and add near the top (the `as`-alias re-export keeps every existing `from estatescout.assistant.chat import OllamaUnavailable` working and silences ruff F401):

```python
from estatescout.errors import OllamaUnavailable as OllamaUnavailable
```

- [ ] **Step 5: In `src/estatescout/rag/embedder.py`**, add `from estatescout.errors import OllamaUnavailable` to the imports and wrap the POST inside `OllamaEmbedder.embed`:

```python
            for text in texts:
                try:
                    resp = client.post(
                        f"{self.host}/api/embeddings",
                        json={"model": self.model, "prompt": text},
                    )
                except httpx.HTTPError as e:  # ConnectError, timeout, etc.
                    raise OllamaUnavailable(f"Ollama not reachable at {self.host}: {e}") from e
                resp.raise_for_status()
                out.append(resp.json()["embedding"])
```

- [ ] **Step 6: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green (existing chat tests keep passing via the re-export).

- [ ] **Step 7: Commit**

```bash
git add src/estatescout/errors.py src/estatescout/assistant/chat.py \
  src/estatescout/rag/embedder.py tests/test_rag_embedder.py
git commit -m "fix(rag): map embedder network errors to OllamaUnavailable"
```

### Task 4: Retrieval similarity threshold + honest "no context" behavior

**Files:**
- Modify: `src/estatescout/rag/index.py`, `src/estatescout/assistant/assistant.py`
- Test: `tests/test_rag_index.py`, `tests/test_assistant_loop.py`

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_rag_index.py` — make sure the file imports `Chunk` (`from estatescout.rag.chunker import Chunk`) and `FakeEmbedder` (`from estatescout.rag.embedder import FakeEmbedder`); add whichever is missing:

```python
def test_retrieve_filters_hits_below_min_score():
    emb = FakeEmbedder()
    chunks = [
        Chunk(source="a.md", heading="h", text="Grunderwerbsteuer Niedersachsen Kaufnebenkosten"),
        Chunk(source="b.md", heading="h", text="Bananenbrot Rezept Zucker Backofen"),
    ]
    idx = RagIndex.build(chunks, emb)
    hits = idx.retrieve("Grunderwerbsteuer Niedersachsen Kaufnebenkosten", emb, k=2, min_score=0.5)
    assert [h.source for h in hits] == ["a.md"]
```

Append to `tests/test_assistant_loop.py`:

```python
def test_no_context_message_when_all_hits_below_threshold():
    chunks = [Chunk("a.md", "h", "Bananenbrot Rezept Zucker Backofen")]
    index = RagIndex.build(chunks, FakeEmbedder())
    model = FakeChat([_final("Dazu enthält die Wissensbasis nichts.")])
    resp = Assistant(model, index=index, embedder=FakeEmbedder(), min_score=0.5).ask(
        "Wie hoch ist die Grunderwerbsteuer?"
    )
    assert resp.sources == []
    sent = model.calls[0]["messages"]
    assert not any("Auszüge" in m.get("content", "") for m in sent)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_rag_index.py tests/test_assistant_loop.py -q`
Expected: FAIL — `retrieve() got an unexpected keyword argument 'min_score'` / `__init__() got an unexpected keyword argument 'min_score'`.

- [ ] **Step 3: Implement in `src/estatescout/rag/index.py`** — change the `retrieve` signature and return:

```python
    def retrieve(
        self, query: str, embedder: Embedder, k: int = 4, *, min_score: float = -1.0
    ) -> list[RetrievedChunk]:
        if k <= 0:
            raise ValueError("k must be > 0")
        qv = np.array(embedder.embed([query])[0], dtype=np.float32)
        norm = np.linalg.norm(qv) or 1.0
        sims = self.matrix @ (qv / norm)
        top = np.argsort(sims)[::-1][:k]
        return [
            RetrievedChunk(
                source=self.chunks[i].source,
                heading=self.chunks[i].heading,
                text=self.chunks[i].text,
                score=float(sims[i]),
            )
            for i in top
            if sims[i] >= min_score
        ]
```

(Default `-1.0` = no filtering — cosine similarity is bounded below by −1, so existing callers and golden tests are unaffected.)

- [ ] **Step 4: Implement in `src/estatescout/assistant/assistant.py`:**

Add a module-level constant below `DISCLAIMER`:

```python
# Conservative cosine threshold for real embedding models (nomic-embed-text): hits below this
# are treated as "no relevant context". Production callers (api/cli) pass this; tests with the
# FakeEmbedder pass explicit values. Tune after observing real retrieval scores.
MIN_RAG_SCORE = 0.35
```

Extend `Assistant.__init__` keyword-only params with `min_score: float = -1.0` and store `self.min_score = min_score`. In `_context_message`, change the retrieve call to:

```python
        hits = self.index.retrieve(question, self.embedder, k=self.k, min_score=self.min_score)
```

Replace rule 2 of `SYSTEM_PROMPT` with:

```python
    "2. Bei Wissensfragen nutzt du die bereitgestellten Auszüge und nennst die Quelle "
    "(Dateiname in Klammern). Gibt es keine passenden Auszüge, sagst du offen, dass die "
    "Wissensbasis dazu nichts enthält, statt zu spekulieren.\n"
```

- [ ] **Step 5: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green (honesty tests assert substrings that still exist).

- [ ] **Step 6: Commit**

```bash
git add src/estatescout/rag/index.py src/estatescout/assistant/assistant.py \
  tests/test_rag_index.py tests/test_assistant_loop.py
git commit -m "feat(rag): add retrieval similarity threshold with honest no-context path"
```

### Task 5: Use the disk cache — `load_or_build()` + per-process index in API/CLI

**Files:**
- Modify: `src/estatescout/rag/index.py`, `src/estatescout/api.py`, `src/estatescout/cli.py`
- Test: `tests/test_rag_index.py`, `tests/test_api.py`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_rag_index.py`:

```python
class CountingEmbedder(FakeEmbedder):
    def __init__(self):
        super().__init__()
        self.embed_calls = 0

    def embed(self, texts):
        self.embed_calls += 1
        return super().embed(texts)


def test_load_or_build_caches_and_skips_reembedding(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.md").write_text("# T\n\nGrunderwerbsteuer in Niedersachsen.", encoding="utf-8")
    emb = CountingEmbedder()
    idx_dir = tmp_path / "idx"
    load_or_build(emb, corpus_dir=corpus, index_dir=idx_dir)
    assert emb.embed_calls == 1
    load_or_build(emb, corpus_dir=corpus, index_dir=idx_dir)
    assert emb.embed_calls == 1  # cache hit — no re-embedding


def test_load_or_build_rebuilds_when_corpus_changes(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "a.md").write_text("# T\n\nAlter Inhalt.", encoding="utf-8")
    emb = CountingEmbedder()
    idx_dir = tmp_path / "idx"
    load_or_build(emb, corpus_dir=corpus, index_dir=idx_dir)
    (corpus / "a.md").write_text("# T\n\nNeuer Inhalt über Mietrendite.", encoding="utf-8")
    idx = load_or_build(emb, corpus_dir=corpus, index_dir=idx_dir)
    assert emb.embed_calls == 2
    assert "Neuer Inhalt" in idx.chunks[0].text
```

(Extend the file's import from `estatescout.rag.index` with `load_or_build`.)

Append to `tests/test_api.py`:

```python
def test_ask_returns_503_when_embedding_unavailable(monkeypatch):
    import estatescout.api as api_mod
    from estatescout.errors import OllamaUnavailable

    monkeypatch.setattr(api_mod, "_index_cache", None)

    def boom(embedder):
        raise OllamaUnavailable("down")

    monkeypatch.setattr(api_mod, "load_or_build", boom)
    assert client.post("/api/ask", json={"question": "hallo"}).status_code == 503
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_rag_index.py tests/test_api.py -q`
Expected: FAIL — `ImportError: cannot import name 'load_or_build'` / `AttributeError: _index_cache`.

- [ ] **Step 3: Implement in `src/estatescout/rag/index.py`** — add `import hashlib` to the imports and append at module level (below the `RagIndex` class):

```python
def _fingerprint(chunks: list[Chunk], embedder: Embedder) -> str:
    """Corpus+embedder identity; any content or model change invalidates the cache."""
    h = hashlib.sha256()
    h.update(getattr(embedder, "model", type(embedder).__name__).encode("utf-8"))
    for c in chunks:
        h.update(c.source.encode("utf-8"))
        h.update(c.heading.encode("utf-8"))
        h.update(c.text.encode("utf-8"))
    return h.hexdigest()


def load_or_build(
    embedder: Embedder,
    *,
    corpus_dir: Path | str = DEFAULT_CORPUS_DIR,
    index_dir: Path | str = DEFAULT_INDEX_DIR,
) -> RagIndex:
    """Load the cached index if the corpus is unchanged; otherwise build and cache it."""
    index_dir = Path(index_dir)
    chunks = load_corpus(corpus_dir)
    fp = _fingerprint(chunks, embedder)
    meta_path = index_dir / "meta.json"
    if meta_path.exists():
        try:
            if json.loads(meta_path.read_text(encoding="utf-8")).get("fingerprint") == fp:
                return RagIndex.load(index_dir)
        except (OSError, ValueError):
            pass  # unreadable/corrupt cache → rebuild below
    index = RagIndex.build(chunks, embedder)
    index.save(index_dir)
    meta_path.write_text(json.dumps({"fingerprint": fp}), encoding="utf-8")
    return index
```

- [ ] **Step 4: Implement in `src/estatescout/api.py`** — change the rag import to `from .rag.index import RagIndex, load_or_build` and replace `get_assistant()` with:

```python
# Built once per process, invalidated via the on-disk corpus fingerprint (rag.index).
_index_cache: RagIndex | None = None


def get_assistant() -> Assistant:
    """Build the live Ollama-backed assistant. Overridden in tests with a fake."""
    global _index_cache
    embedder = OllamaEmbedder()
    if _index_cache is None:
        try:
            _index_cache = load_or_build(embedder)
        except OllamaUnavailable as e:
            raise HTTPException(status_code=503, detail=str(e)) from None
    return Assistant(
        OllamaChat(), index=_index_cache, embedder=embedder, min_score=MIN_RAG_SCORE
    )
```

Extend the assistant import at the top to `from .assistant.assistant import DISCLAIMER, MIN_RAG_SCORE, Assistant`. Remove the now-unused `load_corpus` import.

- [ ] **Step 5: Implement in `src/estatescout/cli.py`** — inside `ask()`, replace the two lines building embedder+index with:

```python
        from .assistant.assistant import MIN_RAG_SCORE, Assistant
        from .rag.index import load_or_build

        embedder = OllamaEmbedder()
        index = load_or_build(embedder)
        resp = Assistant(
            OllamaChat(), index=index, embedder=embedder, min_score=MIN_RAG_SCORE
        ).ask(question)
```

(Adjust the local imports in `ask()` accordingly — `RagIndex, load_corpus` are no longer needed there.)

- [ ] **Step 6: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add src/estatescout/rag/index.py src/estatescout/api.py src/estatescout/cli.py \
  tests/test_rag_index.py tests/test_api.py
git commit -m "perf(rag): build the index once per process with a corpus-fingerprint cache"
```

---

## Part B — Finance depth (investor math)

### Task 6: Fraction sanity bounds on rates (defense-in-depth in the trust anchor)

**Files:**
- Modify: `src/estatescout/finance/annuity.py`, `src/estatescout/finance/affordability.py`
- Test: `tests/test_finance_annuity.py`, `tests/test_finance_affordability.py`

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_finance_annuity.py`:

```python
def test_percent_passed_as_fraction_is_rejected():
    with pytest.raises(ValueError, match="looks like percent"):
        annuity(principal=300_000, annual_rate=3.6, initial_repayment=0.02)
    with pytest.raises(ValueError, match="looks like percent"):
        annuity(principal=300_000, annual_rate=0.036, initial_repayment=2.0)
```

Append to `tests/test_finance_affordability.py`:

```python
def test_percent_passed_as_fraction_is_rejected():
    with pytest.raises(ValueError, match="looks like percent"):
        affordability(4_000, 60_000, 3.6, 0.02, "NI")
    with pytest.raises(ValueError, match="looks like percent"):
        affordability(4_000, 60_000, 0.036, 2.0, "NI")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_finance_annuity.py tests/test_finance_affordability.py -q`
Expected: new tests FAIL (`DID NOT RAISE`).

- [ ] **Step 3: Implement.** In `src/estatescout/finance/annuity.py` (`amortize`, directly after the existing four input checks) and in `src/estatescout/finance/affordability.py` (after the existing `initial_repayment` check), add the same two guards:

```python
    if annual_rate > 0.25:
        raise ValueError(
            "annual_rate is a fraction (0.036 = 3.6 %) — a value above 0.25 looks like percent"
        )
    if initial_repayment > 0.2:
        raise ValueError(
            "initial_repayment is a fraction (0.02 = 2 %) — a value above 0.2 looks like percent"
        )
```

(All existing tests use rates ≤ 0.05, verified at plan time — nothing else changes.)

- [ ] **Step 4: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/estatescout/finance/annuity.py src/estatescout/finance/affordability.py \
  tests/test_finance_annuity.py tests/test_finance_affordability.py
git commit -m "feat(finance): reject percent-looking rate fractions in the core"
```

### Task 7: `operating_costs` calculator + `bewirtschaftung` config; drop dead config

`yield_metrics.annual_operating_costs` is currently a blind guess for the user. Anchor it: a small config-driven estimator. Also remove the two config blocks nothing consumes (`affordability.management_cost_eur_per_sqm`, `reference_interest`) — verified unreferenced in src/ and tests/ at plan time.

**Files:**
- Create: `src/estatescout/finance/operating_costs.py`
- Modify: `config/rates.yaml`
- Test: create `tests/test_finance_operating_costs.py`

- [ ] **Step 1: Write the failing test** — create `tests/test_finance_operating_costs.py`:

```python
"""Tests for the config-anchored Bewirtschaftungskosten estimator."""

import pytest

from estatescout.finance.operating_costs import operating_costs


def test_worked_example_100sqm_1000eur_rent():
    # 100 m² × 12 €/m²/a = 1200; 1 unit × 350 €/a = 350; 12_000 € rent × 2 % = 240
    res = operating_costs(100.0, 1_000.0)
    assert res.instandhaltung == pytest.approx(1_200.0)
    assert res.verwaltung == pytest.approx(350.0)
    assert res.mietausfallwagnis == pytest.approx(240.0)
    assert res.total_annual == pytest.approx(1_790.0)


def test_units_scale_the_management_fee():
    res = operating_costs(200.0, 2_000.0, units=3)
    assert res.verwaltung == pytest.approx(1_050.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        operating_costs(0, 1_000.0)
    with pytest.raises(ValueError):
        operating_costs(100.0, 0)
    with pytest.raises(ValueError):
        operating_costs(100.0, 1_000.0, units=0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_finance_operating_costs.py -q`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Add the config block** to `config/rates.yaml` (append at the end) and delete both dead blocks — remove the `management_cost_eur_per_sqm` line (plus its comment line) from `affordability:` and remove the entire `reference_interest:` block:

```yaml
bewirtschaftung:
  as_of: "2026-07-07"
  source: "II. BV §§ 26-29 Pauschalen (indexiert) als Praxis-Anker; Faustregel ~1 EUR/m²/Monat Instandhaltung; verify current index level"
  # Annual operating-cost anchors for a landlord's calculation — estimates, not invoices.
  instandhaltung_eur_per_sqm_year: 12.0
  verwaltung_eur_per_unit_year: 350.0
  # Fraction of annual cold rent reserved for rent-loss risk (II. BV § 29: 2 %).
  mietausfallwagnis_rate: 0.02
```

- [ ] **Step 4: Create `src/estatescout/finance/operating_costs.py`:**

```python
"""Bewirtschaftungskosten — annual non-allocable operating costs of a rental unit.

    instandhaltung    = living_area_sqm · instandhaltung_eur_per_sqm_year
    verwaltung        = units · verwaltung_eur_per_unit_year
    mietausfallwagnis = annual cold rent · mietausfallwagnis_rate

Anchored on the II. BV (§§ 26-29) Pauschalen as practice values from ``config/rates.yaml``
(source + date there). An estimate anchor for the net-yield calculation, not an invoice.
Pure and deterministic.
"""

from dataclasses import dataclass

from .config import load_config


@dataclass(frozen=True)
class OperatingCosts:
    instandhaltung: float
    verwaltung: float
    mietausfallwagnis: float
    total_annual: float


def operating_costs(
    living_area_sqm: float,
    monthly_cold_rent: float,
    *,
    units: int = 1,
    config: dict | None = None,
) -> OperatingCosts:
    """Estimate annual operating costs from the config-anchored practice values.

    Args:
        living_area_sqm: living area in m² (> 0).
        monthly_cold_rent: monthly Kaltmiete in EUR (> 0).
        units: number of residential units (>= 1), scales the per-unit management fee.
    """
    if living_area_sqm <= 0:
        raise ValueError("living_area_sqm must be > 0")
    if monthly_cold_rent <= 0:
        raise ValueError("monthly_cold_rent must be > 0")
    if units < 1:
        raise ValueError("units must be >= 1")

    cfg = (config or load_config())["bewirtschaftung"]
    instandhaltung = living_area_sqm * cfg["instandhaltung_eur_per_sqm_year"]
    verwaltung = units * cfg["verwaltung_eur_per_unit_year"]
    mietausfallwagnis = monthly_cold_rent * 12.0 * cfg["mietausfallwagnis_rate"]
    return OperatingCosts(
        instandhaltung=instandhaltung,
        verwaltung=verwaltung,
        mietausfallwagnis=mietausfallwagnis,
        total_annual=instandhaltung + verwaltung + mietausfallwagnis,
    )
```

- [ ] **Step 5: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green (no test references the removed config keys — verified at plan time).

- [ ] **Step 6: Commit**

```bash
git add src/estatescout/finance/operating_costs.py config/rates.yaml \
  tests/test_finance_operating_costs.py
git commit -m "feat(finance): add config-anchored operating-costs estimator, drop dead config"
```

### Task 8: `equity_return` calculator (cash-on-cash)

**Files:**
- Create: `src/estatescout/finance/equity_return.py`
- Test: create `tests/test_finance_equity_return.py`

- [ ] **Step 1: Write the failing test** — create `tests/test_finance_equity_return.py`:

```python
"""Tests for the first-year Eigenkapitalrendite (cash-on-cash) calculator."""

import pytest

from estatescout.finance.equity_return import equity_return


def test_worked_example_positive_cashflow():
    # loan = 300k + 30k − 60k = 270k; debt service = 270k × 5.6 % = 15_120
    # NOI = 1_500 × 12 − 2_400 = 15_600; CF = 480; CoC = 480 / 60_000 = 0.8 %
    res = equity_return(
        300_000, 1_500.0, 60_000, 0.036, 0.02,
        ancillary_costs=30_000, annual_operating_costs=2_400,
    )
    assert res.loan == pytest.approx(270_000.0)
    assert res.annual_debt_service == pytest.approx(15_120.0)
    assert res.net_operating_income == pytest.approx(15_600.0)
    assert res.cashflow_before_tax == pytest.approx(480.0)
    assert res.cash_on_cash == pytest.approx(0.008)


def test_negative_cashflow_yields_negative_return():
    # same object, weaker rent: NOI = 12_000 − 2_400 = 9_600; CF = −5_520
    res = equity_return(
        300_000, 1_000.0, 60_000, 0.036, 0.02,
        ancillary_costs=30_000, annual_operating_costs=2_400,
    )
    assert res.cashflow_before_tax == pytest.approx(-5_520.0)
    assert res.cash_on_cash < 0


def test_full_equity_purchase_has_no_debt_service():
    res = equity_return(100_000, 500.0, 110_000, 0.036, 0.02, ancillary_costs=10_000)
    assert res.loan == pytest.approx(0.0)
    assert res.annual_debt_service == pytest.approx(0.0)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        equity_return(100_000, 500.0, 0, 0.036, 0.02)  # no equity
    with pytest.raises(ValueError):
        equity_return(100_000, 500.0, 200_000, 0.036, 0.02)  # equity > investment
    with pytest.raises(ValueError, match="looks like percent"):
        equity_return(100_000, 500.0, 20_000, 3.6, 0.02)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_finance_equity_return.py -q`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Create `src/estatescout/finance/equity_return.py`:**

```python
"""Eigenkapitalrendite — first-year cash-on-cash return of a financed buy-to-let.

    loan                 = purchase_price + ancillary_costs − equity
    annual_debt_service  = loan · (annual_rate + initial_repayment)
    net_operating_income = annual cold rent − annual operating costs
    cashflow_before_tax  = net_operating_income − annual_debt_service
    cash_on_cash         = cashflow_before_tax / equity

The unlevered net yield (``yield_metrics``) says what the object earns; cash-on-cash says
what the invested equity earns after debt service — the number a leveraged investor actually
optimizes. Year-1, before tax (the annuity payment is constant, its interest/principal split
shifts over time — see ``annuity``). Pure and deterministic.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EquityReturn:
    loan: float
    annual_debt_service: float
    net_operating_income: float
    cashflow_before_tax: float
    cash_on_cash: float


def equity_return(
    purchase_price: float,
    monthly_cold_rent: float,
    equity: float,
    annual_rate: float,
    initial_repayment: float,
    *,
    ancillary_costs: float = 0.0,
    annual_operating_costs: float = 0.0,
) -> EquityReturn:
    """First-year cash-on-cash return. Rates are fractions (0.036 = 3.6 %)."""
    if purchase_price <= 0:
        raise ValueError("purchase_price must be > 0")
    if monthly_cold_rent <= 0:
        raise ValueError("monthly_cold_rent must be > 0")
    if equity <= 0:
        raise ValueError("equity must be > 0 (cash-on-cash needs invested equity)")
    if ancillary_costs < 0:
        raise ValueError("ancillary_costs must be >= 0")
    if annual_operating_costs < 0:
        raise ValueError("annual_operating_costs must be >= 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")
    if annual_rate > 0.25:
        raise ValueError(
            "annual_rate is a fraction (0.036 = 3.6 %) — a value above 0.25 looks like percent"
        )
    if initial_repayment <= 0:
        raise ValueError("initial_repayment must be > 0")
    if initial_repayment > 0.2:
        raise ValueError(
            "initial_repayment is a fraction (0.02 = 2 %) — a value above 0.2 looks like percent"
        )

    total_investment = purchase_price + ancillary_costs
    if equity > total_investment:
        raise ValueError("equity exceeds the total investment — nothing to finance")

    loan = total_investment - equity
    annual_debt_service = loan * (annual_rate + initial_repayment)
    net_operating_income = monthly_cold_rent * 12.0 - annual_operating_costs
    cashflow_before_tax = net_operating_income - annual_debt_service
    return EquityReturn(
        loan=loan,
        annual_debt_service=annual_debt_service,
        net_operating_income=net_operating_income,
        cashflow_before_tax=cashflow_before_tax,
        cash_on_cash=cashflow_before_tax / equity,
    )
```

- [ ] **Step 4: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/estatescout/finance/equity_return.py tests/test_finance_equity_return.py
git commit -m "feat(finance): add first-year cash-on-cash equity-return calculator"
```

### Task 9: Expose both new calculators as tools + CLI commands

**Files:**
- Modify: `src/estatescout/assistant/tools.py`, `src/estatescout/cli.py`
- Test: `tests/test_assistant_tools.py`, `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests.** In `tests/test_assistant_tools.py`, UPDATE the existing name-set assertion in `test_tool_specs_cover_all_calculators` to:

```python
    assert names == {
        "annuity", "purchase_costs", "affordability", "yield_metrics",
        "operating_costs", "equity_return",
    }
```

and append:

```python
def test_dispatch_operating_costs():
    out = dispatch("operating_costs", {"living_area_sqm": 100, "monthly_cold_rent": 1_000})
    assert out["total_annual"] == pytest.approx(1_790.0)


def test_dispatch_equity_return_converts_percent():
    out = dispatch(
        "equity_return",
        {"purchase_price": 300_000, "monthly_cold_rent": 1_500, "equity": 60_000,
         "annual_rate_percent": 3.6, "initial_repayment_percent": 2.0,
         "ancillary_costs": 30_000, "annual_operating_costs": 2_400},
    )
    assert out["cashflow_before_tax"] == pytest.approx(480.0)
    assert out["cash_on_cash_percent"] == pytest.approx(0.8)
```

Append to `tests/test_cli.py`:

```python
def test_cli_opcosts():
    out = _run(["opcosts", "--area", "100", "--rent", "1000"])
    assert out["total_annual"] == pytest.approx(1_790.0)


def test_cli_equity_return():
    out = _run(
        ["equity", "--price", "300000", "--rent", "1500", "--equity", "60000",
         "--rate", "3.6", "--repayment", "2.0", "--ancillary", "30000",
         "--operating", "2400"]
    )
    assert out["cash_on_cash_percent"] == pytest.approx(0.8)
```

(`tests/test_cli.py` needs `import pytest` if not already present.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_assistant_tools.py tests/test_cli.py -q`
Expected: FAIL — unknown tool / name-set mismatch / unknown CLI command.

- [ ] **Step 3: Implement in `src/estatescout/assistant/tools.py`.** Add the imports:

```python
from estatescout.finance.equity_return import equity_return
from estatescout.finance.operating_costs import operating_costs
```

Add the two adapters (next to the existing `_run_*` functions):

```python
def _run_operating_costs(a: dict) -> dict:
    res = operating_costs(
        a["living_area_sqm"],
        a["monthly_cold_rent"],
        units=int(a.get("units", 1)),
    )
    return {
        "instandhaltung": _eur(res.instandhaltung),
        "verwaltung": _eur(res.verwaltung),
        "mietausfallwagnis": _eur(res.mietausfallwagnis),
        "total_annual": _eur(res.total_annual),
    }


def _run_equity_return(a: dict) -> dict:
    res = equity_return(
        a["purchase_price"],
        a["monthly_cold_rent"],
        a["equity"],
        a["annual_rate_percent"] / 100,
        a["initial_repayment_percent"] / 100,
        ancillary_costs=a.get("ancillary_costs", 0.0),
        annual_operating_costs=a.get("annual_operating_costs", 0.0),
    )
    return {
        "loan": _eur(res.loan),
        "annual_debt_service": _eur(res.annual_debt_service),
        "net_operating_income": _eur(res.net_operating_income),
        "cashflow_before_tax": _eur(res.cashflow_before_tax),
        "cash_on_cash_percent": _pct(res.cash_on_cash),
    }
```

Add both entries to the `TOOLS` dict:

```python
    "operating_costs": Tool(
        spec=_spec(
            "operating_costs",
            "Estimate a landlord's annual Bewirtschaftungskosten (Instandhaltung, Verwaltung, "
            "Mietausfallwagnis) from config-anchored practice values.",
            {
                "living_area_sqm": _p("living area in m²"),
                "monthly_cold_rent": _p("monthly Kaltmiete in EUR"),
                "units": _p("number of residential units, default 1"),
            },
            ["living_area_sqm", "monthly_cold_rent"],
        ),
        run=_run_operating_costs,
    ),
    "equity_return": Tool(
        spec=_spec(
            "equity_return",
            "First-year Eigenkapitalrendite (cash-on-cash) of a financed buy-to-let: cashflow "
            "after debt service relative to invested equity.",
            {
                "purchase_price": _p("property price in EUR"),
                "monthly_cold_rent": _p("monthly Kaltmiete in EUR"),
                "equity": _p("invested equity in EUR"),
                "annual_rate_percent": _p("nominal interest p.a. in %, e.g. 3.6"),
                "initial_repayment_percent": _p("anfängliche Tilgung in %, e.g. 2.0"),
                "ancillary_costs": _p("Kaufnebenkosten in EUR"),
                "annual_operating_costs": _p("Bewirtschaftungskosten EUR/year"),
            },
            [
                "purchase_price",
                "monthly_cold_rent",
                "equity",
                "annual_rate_percent",
                "initial_repayment_percent",
            ],
        ),
        run=_run_equity_return,
    ),
```

- [ ] **Step 4: Implement in `src/estatescout/cli.py`** — append to the `finance_app` commands:

```python
@finance_app.command()
def opcosts(
    area: float = typer.Option(..., help="living area in m²"),
    rent: float = typer.Option(..., help="monthly Kaltmiete in EUR"),
    units: int = typer.Option(1, help="number of residential units"),
) -> None:
    """Annual Bewirtschaftungskosten estimate (Instandhaltung, Verwaltung, Mietausfall)."""
    _echo(
        dispatch(
            "operating_costs",
            {"living_area_sqm": area, "monthly_cold_rent": rent, "units": units},
        )
    )


@finance_app.command(name="equity")
def equity_cmd(
    price: float = typer.Option(..., help="purchase price in EUR"),
    rent: float = typer.Option(..., help="monthly Kaltmiete in EUR"),
    equity: float = typer.Option(..., help="invested equity in EUR"),
    rate: float = typer.Option(..., help="nominal interest p.a. in %"),
    repayment: float = typer.Option(..., help="anfängliche Tilgung in %"),
    ancillary: float = typer.Option(0.0, help="Kaufnebenkosten in EUR"),
    operating: float = typer.Option(0.0, help="Bewirtschaftungskosten EUR/year"),
) -> None:
    """First-year Eigenkapitalrendite (cash-on-cash) of a financed buy-to-let."""
    _echo(
        dispatch(
            "equity_return",
            {
                "purchase_price": price,
                "monthly_cold_rent": rent,
                "equity": equity,
                "annual_rate_percent": rate,
                "initial_repayment_percent": repayment,
                "ancillary_costs": ancillary,
                "annual_operating_costs": operating,
            },
        )
    )
```

- [ ] **Step 5: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add src/estatescout/assistant/tools.py src/estatescout/cli.py \
  tests/test_assistant_tools.py tests/test_cli.py
git commit -m "feat(tools): expose operating-costs and equity-return as tools and CLI"
```

---

## Part C — Assistant ↔ Scout integration

### Task 10: Give the assistant access to saved listings (`extra_tools`)

Break the silo: a `list_listings` tool over the `ListingStore`, injected only where a store exists (api/cli) — NOT part of the static `TOOLS`, so `/api/finance/list_listings` stays a 400.

**Files:**
- Modify: `src/estatescout/assistant/tools.py`, `src/estatescout/assistant/assistant.py`, `src/estatescout/api.py`, `src/estatescout/cli.py`
- Test: `tests/test_assistant_loop.py`, `tests/test_api.py`

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_assistant_loop.py`:

```python
def test_assistant_lists_saved_listings_via_extra_tool():
    from estatescout.assistant.tools import listing_tools
    from estatescout.scout.model import Listing
    from estatescout.scout.store import ListingStore

    store = ListingStore(":memory:")
    store.add(Listing(price=300_000, living_area_sqm=100, bundesland="NI", ort="Lingen"))
    model = FakeChat(
        [
            {"role": "assistant", "content": "",
             "tool_calls": [{"function": {"name": "list_listings", "arguments": {}}}]},
            _final("Du hast 1 Objekt gespeichert: Lingen, 300.000 €."),
        ]
    )
    resp = Assistant(model, extra_tools=listing_tools(store)).ask("Welche Objekte habe ich?")
    assert resp.tool_calls[0]["result"]["count"] == 1
    assert resp.tool_calls[0]["result"]["listings"][0]["ort"] == "Lingen"
    sent_tools = model.calls[0]["tools"]
    assert any(t["function"]["name"] == "list_listings" for t in sent_tools)
```

Append to `tests/test_api.py` (guard: listing tool must NOT leak into the finance endpoint):

```python
def test_finance_endpoint_does_not_expose_listing_tools():
    assert client.post("/api/finance/list_listings", json={}).status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_assistant_loop.py tests/test_api.py -q`
Expected: FAIL — `ImportError: listing_tools` / unexpected keyword `extra_tools`.

- [ ] **Step 3: Implement in `src/estatescout/assistant/tools.py`.** Change the `dispatch` signature to accept an optional tools mapping (keeps the finance-only default for the API):

```python
def dispatch(name: str, args: dict, *, tools: dict[str, Tool] | None = None) -> dict:
    """Validate, type-coerce and run the named tool. Numbers come from finance/."""
    tools_map = tools if tools is not None else TOOLS
    if name not in tools_map:
        raise ValueError(f"unknown tool '{name}' (known: {', '.join(sorted(tools_map))})")
    tool = tools_map[name]
    cleaned = _clean_args(name, tool, args)
    required = tool.spec["function"]["parameters"]["required"]
    missing = [r for r in required if r not in cleaned]
    if missing:
        raise ValueError(f"tool '{name}' missing required args: {', '.join(missing)}")
    return tool.run(cleaned)
```

Append at the end of the file (import `ListingStore` lazily inside the function to avoid a hard scout dependency at import time is NOT needed — a top-level `from estatescout.scout.store import ListingStore` is fine and creates no cycle; scout never imports assistant):

```python
def listing_tools(store: "ListingStore") -> dict[str, Tool]:
    """Tools over the user's saved listings (Stage 2). Read-only for the model."""

    def _run_list(a: dict) -> dict:
        items = store.list()
        return {
            "count": len(items),
            "listings": [
                {
                    "id": it.id,
                    "ort": it.ort,
                    "bundesland": it.bundesland,
                    "object_type": it.object_type,
                    "price": _eur(it.price),
                    "living_area_sqm": it.living_area_sqm,
                    "price_per_sqm": _eur(it.price_per_sqm),
                    "rooms": it.rooms,
                    "year_built": it.year_built,
                }
                for it in items
            ],
        }

    return {
        "list_listings": Tool(
            spec=_spec(
                "list_listings",
                "List the property objects the user has saved (id, location, price, size, "
                "price per m²). Use for any question about the user's own objects "
                "('meine Objekte').",
                {},
                [],
            ),
            run=_run_list,
        )
    }
```

Add the import at the top: `from estatescout.scout.store import ListingStore`.

- [ ] **Step 4: Implement in `src/estatescout/assistant/assistant.py`.** Change the tools import to `from .tools import TOOLS, Tool, dispatch`. Extend `__init__` with `extra_tools: dict[str, Tool] | None = None` (keyword-only, after `min_score`) and set:

```python
        self._tools = {**TOOLS, **(extra_tools or {})}
```

In `ask()`, replace `specs = tool_specs()` with:

```python
        specs = [t.spec for t in self._tools.values()]
```

and change the dispatch call to `dispatch(name, args, tools=self._tools)`. Remove the now-unused `tool_specs` import.

Append a fifth rule to `SYSTEM_PROMPT` (before the final "Antworte auf Deutsch" line):

```python
    "5. Fragen zu den gespeicherten Objekten des Nutzers beantwortest du über das Tool "
    "list_listings — nie aus dem Gedächtnis.\n"
```

- [ ] **Step 5: Wire in `src/estatescout/api.py`** — turn `get_assistant` into a generator dependency that owns a store connection:

```python
def get_assistant() -> Iterator[Assistant]:
    """Build the live Ollama-backed assistant. Overridden in tests with a fake."""
    global _index_cache
    embedder = OllamaEmbedder()
    if _index_cache is None:
        try:
            _index_cache = load_or_build(embedder)
        except OllamaUnavailable as e:
            raise HTTPException(status_code=503, detail=str(e)) from None
    store = ListingStore(DEFAULT_DB)
    try:
        yield Assistant(
            OllamaChat(),
            index=_index_cache,
            embedder=embedder,
            min_score=MIN_RAG_SCORE,
            extra_tools=listing_tools(store),
        )
    finally:
        store.close()
```

Extend the tools import: `from .assistant.tools import dispatch, listing_tools`.

- [ ] **Step 6: Wire in `src/estatescout/cli.py`** — replace the body of `ask()` with:

```python
def ask(question: str) -> None:
    """Ask a real-estate question; the assistant uses RAG for knowledge and tools for numbers."""
    from .assistant.assistant import MIN_RAG_SCORE, Assistant
    from .assistant.chat import OllamaChat, OllamaUnavailable
    from .assistant.tools import listing_tools
    from .rag.embedder import OllamaEmbedder
    from .rag.index import load_or_build

    store = ListingStore(DEFAULT_DB)
    try:
        embedder = OllamaEmbedder()
        index = load_or_build(embedder)
        assistant = Assistant(
            OllamaChat(),
            index=index,
            embedder=embedder,
            min_score=MIN_RAG_SCORE,
            extra_tools=listing_tools(store),
        )
        resp = assistant.ask(question)
    except OllamaUnavailable:
        typer.echo(
            "Ollama ist nicht erreichbar. Starte 'ollama serve' und ziehe ein Modell "
            "(z.B. 'ollama pull qwen2.5:7b' + 'ollama pull nomic-embed-text').\n"
            "Die Rechner funktionieren ohne LLM: 'uv run python scripts/finance.py --help'."
        )
        raise typer.Exit(code=1) from None
    finally:
        store.close()
    typer.echo(render_response(resp))
```

- [ ] **Step 7: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green (honesty-prompt substring asserts unaffected).

- [ ] **Step 8: Commit**

```bash
git add src/estatescout/assistant/tools.py src/estatescout/assistant/assistant.py \
  src/estatescout/api.py src/estatescout/cli.py \
  tests/test_assistant_loop.py tests/test_api.py
git commit -m "feat(assistant): let the assistant read saved listings via extra tools"
```

### Task 11: DELETE listing (API + CLI)

**Files:**
- Modify: `src/estatescout/api.py`, `src/estatescout/cli.py`
- Test: `tests/test_api.py`, `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_api.py`:

```python
def test_listings_delete(tmp_path):
    app.dependency_overrides[get_store] = _override_store_to(str(tmp_path / "api.db"))
    try:
        created = client.post(
            "/api/listings",
            json={"price": 100_000, "living_area_sqm": 50, "bundesland": "NI"},
        ).json()
        assert client.delete(f"/api/listings/{created['id']}").status_code == 204
        assert client.delete(f"/api/listings/{created['id']}").status_code == 404
    finally:
        app.dependency_overrides.clear()
```

Append to `tests/test_cli.py`:

```python
def test_scout_delete_removes_listing(tmp_path):
    db = str(tmp_path / "cli.db")
    add = runner.invoke(
        scout_app,
        ["add", "--price", "100000", "--area", "50", "--bundesland", "NI", "--db", db],
    )
    assert add.exit_code == 0, add.stdout
    listing_id = json.loads(add.stdout)["id"]
    assert runner.invoke(scout_app, ["delete", str(listing_id), "--db", db]).exit_code == 0
    assert runner.invoke(scout_app, ["delete", str(listing_id), "--db", db]).exit_code == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_api.py tests/test_cli.py -q`
Expected: FAIL — 405 (no DELETE route) / CLI usage error.

- [ ] **Step 3: Implement.** In `src/estatescout/api.py`, below `list_listings`:

```python
@app.delete("/api/listings/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int, store: Annotated[ListingStore, Depends(get_store)]
) -> None:
    if not store.delete(listing_id):
        raise HTTPException(status_code=404, detail=f"listing {listing_id} not found")
```

In `src/estatescout/cli.py`, below the `scout_app` `list` command:

```python
@scout_app.command("delete")
def delete_listing_cmd(
    listing_id: int = typer.Argument(..., help="listing id (see 'scout list')"),
    db: str = typer.Option(str(DEFAULT_DB), help="SQLite path"),
) -> None:
    """Delete a saved object by id."""
    store = ListingStore(db)
    try:
        ok = store.delete(listing_id)
    finally:
        store.close()
    if not ok:
        typer.echo(f"Kein Objekt mit id {listing_id}.")
        raise typer.Exit(code=1)
    typer.echo(f"Objekt {listing_id} gelöscht.")
```

- [ ] **Step 4: Run the gate**

Run: `uv run pytest -q && uv run ruff check .`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add src/estatescout/api.py src/estatescout/cli.py tests/test_api.py tests/test_cli.py
git commit -m "feat(scout): add listing deletion via API and CLI"
```

---

## Part D — Frontend

All frontend commands run from `frontend/`: tests `npm test`, build `npm run build`. Use `fireEvent` from `@testing-library/react` (`user-event` is NOT installed — do not add dependencies).

### Task 12: `format.ts` + typed `api.ts` with one narrowing boundary and better errors

**Files:**
- Create: `frontend/src/format.ts`
- Modify: `frontend/src/api.ts` (rewrite), `frontend/src/AmortizationTable.tsx` (use format.ts)

- [ ] **Step 1: Create `frontend/src/format.ts`:**

```ts
// de-DE number formatting shared by all result cards and tables.

export const eur = (n: number) =>
  n.toLocaleString("de-DE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });

export const pct = (n: number) => `${n.toLocaleString("de-DE", { maximumFractionDigits: 2 })} %`;

export const num = (n: number, digits = 1) =>
  n.toLocaleString("de-DE", { maximumFractionDigits: digits });
```

- [ ] **Step 2: In `frontend/src/AmortizationTable.tsx`**, delete the local `const eur = ...` definition and add `import { eur } from "./format";` at the top.

- [ ] **Step 3: Rewrite `frontend/src/api.ts`:**

```ts
// Types mirror the FastAPI responses (src/estatescout/api.py) and the finance tool results
// (src/estatescout/assistant/tools.py). Narrowing wire data to typed results happens in
// exactly one place: toKnownCalc().

import { type AnnuityResult } from "./AmortizationTable";

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

export interface PurchaseCostsResult {
  bundesland: string;
  grunderwerbsteuer: number;
  notary: number;
  land_registry: number;
  makler: number;
  total_ancillary: number;
  total_investment: number;
  ancillary_quota_percent: number;
  min_equity: number;
}

export interface AffordabilityResult {
  max_monthly_payment: number;
  max_loan: number;
  max_purchase_price: number;
  ancillary_quota_percent: number;
  equity: number;
}

export interface YieldResult {
  annual_cold_rent: number;
  gross_yield_percent: number;
  net_yield_percent: number;
  kaufpreisfaktor: number;
}

export interface OperatingCostsResult {
  instandhaltung: number;
  verwaltung: number;
  mietausfallwagnis: number;
  total_annual: number;
}

export interface EquityReturnResult {
  loan: number;
  annual_debt_service: number;
  net_operating_income: number;
  cashflow_before_tax: number;
  cash_on_cash_percent: number;
}

export type KnownCalc =
  | { kind: "annuity"; result: AnnuityResult }
  | { kind: "purchase_costs"; result: PurchaseCostsResult }
  | { kind: "affordability"; result: AffordabilityResult }
  | { kind: "yield_metrics"; result: YieldResult }
  | { kind: "operating_costs"; result: OperatingCostsResult }
  | { kind: "equity_return"; result: EquityReturnResult };

// The single narrowing boundary between wire data and typed results. Failed tool calls
// ({error: ...}) and unknown tools return null — callers simply render no card.
export function toKnownCalc(name: string, result: Record<string, unknown>): KnownCalc | null {
  if ("error" in result) return null;
  switch (name) {
    case "annuity":
      return "remaining_debt_by_year" in result
        ? { kind: "annuity", result: result as unknown as AnnuityResult }
        : null;
    case "purchase_costs":
      return { kind: "purchase_costs", result: result as unknown as PurchaseCostsResult };
    case "affordability":
      return { kind: "affordability", result: result as unknown as AffordabilityResult };
    case "yield_metrics":
      return { kind: "yield_metrics", result: result as unknown as YieldResult };
    case "operating_costs":
      return { kind: "operating_costs", result: result as unknown as OperatingCostsResult };
    case "equity_return":
      return { kind: "equity_return", result: result as unknown as EquityReturnResult };
    default:
      return null;
  }
}

export interface Listing {
  id: number;
  price: number;
  living_area_sqm: number;
  bundesland: string;
  plz: string;
  ort: string;
  rooms: number | null;
  year_built: number | null;
  object_type: string;
  features: string[];
  source_url: string;
  price_per_sqm: number;
}

export interface NewListing {
  price: number;
  living_area_sqm: number;
  bundesland: string;
  ort?: string;
  rooms?: number;
  year_built?: number;
  object_type?: string;
  source_url?: string;
}

async function errorMessage(res: Response): Promise<string> {
  if (res.status === 503) {
    return "Ollama ist nicht erreichbar. Starte den lokalen Server (ollama serve) und ziehe ein Modell.";
  }
  try {
    const body: unknown = await res.json();
    if (
      body !== null &&
      typeof body === "object" &&
      typeof (body as { detail?: unknown }).detail === "string"
    ) {
      return (body as { detail: string }).detail;
    }
  } catch {
    // non-JSON error body — fall through to the generic message
  }
  return `Fehler ${res.status}`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url, init);
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err; // caller cancelled
    throw new Error("API nicht erreichbar — läuft der Server (uv run uvicorn estatescout.api:app)?");
  }
  if (!res.ok) throw new Error(await errorMessage(res));
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const asJson = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export function ask(question: string, signal?: AbortSignal): Promise<AskResponse> {
  return request<AskResponse>("/api/ask", { ...asJson({ question }), signal });
}

export function finance(
  calc: string,
  args: Record<string, unknown>,
): Promise<{ result: Record<string, unknown>; disclaimer: string }> {
  return request(`/api/finance/${calc}`, asJson(args));
}

export function listListings(): Promise<Listing[]> {
  return request("/api/listings");
}

export function createListing(data: NewListing): Promise<Listing> {
  return request("/api/listings", asJson(data));
}

export function deleteListing(id: number): Promise<void> {
  return request(`/api/listings/${id}`, { method: "DELETE" });
}
```

- [ ] **Step 4: Verify** — `App.tsx` still imports `ask`/`AskResponse`/`ToolCall`, which all still exist.

Run: `cd frontend && npm test && npm run build`
Expected: 3 existing tests pass, tsc + vite build green.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/format.ts frontend/src/api.ts frontend/src/AmortizationTable.tsx
git commit -m "refactor(frontend): typed API layer with single narrowing boundary"
```

### Task 13: `CalcResultCard` — render every calculator result

**Files:**
- Create: `frontend/src/CalcResultCard.tsx`
- Test: `frontend/src/App.test.tsx` (append)

- [ ] **Step 1: Write the failing test** — append to `frontend/src/App.test.tsx`:

```tsx
import { CalcResultCard } from "./CalcResultCard";

describe("CalcResultCard", () => {
  it("renders a purchase-costs breakdown", () => {
    render(
      <CalcResultCard
        calc={{
          kind: "purchase_costs",
          result: {
            bundesland: "NW",
            grunderwerbsteuer: 19500,
            notary: 4500,
            land_registry: 1500,
            makler: 10710,
            total_ancillary: 36210,
            total_investment: 336210,
            ancillary_quota_percent: 12.07,
            min_equity: 36210,
          },
        }}
      />,
    );
    expect(screen.getByText(/Kaufnebenkosten/)).toBeInTheDocument();
    expect(screen.getByText(/19\.500/)).toBeInTheDocument();
  });

  it("renders an equity-return card", () => {
    render(
      <CalcResultCard
        calc={{
          kind: "equity_return",
          result: {
            loan: 270000,
            annual_debt_service: 15120,
            net_operating_income: 15600,
            cashflow_before_tax: 480,
            cash_on_cash_percent: 0.8,
          },
        }}
      />,
    );
    expect(screen.getByText("Eigenkapitalrendite (Jahr 1)")).toBeInTheDocument();
    expect(screen.getByText("0,8 %")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm test`
Expected: FAIL — cannot resolve `./CalcResultCard`.

- [ ] **Step 3: Create `frontend/src/CalcResultCard.tsx`:**

```tsx
// One card per calculator result. All numbers come from the backend (finance/);
// this component only formats them.

import { type ReactNode } from "react";

import { AmortizationTable } from "./AmortizationTable";
import { type KnownCalc } from "./api";
import { eur, num, pct } from "./format";

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="calc">
      <h4>{title}</h4>
      <div className="grid">{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span>{label}</span>
      <span className="num">{value}</span>
    </>
  );
}

export function CalcResultCard({ calc }: { calc: KnownCalc }) {
  switch (calc.kind) {
    case "annuity":
      return <AmortizationTable result={calc.result} />;
    case "purchase_costs": {
      const r = calc.result;
      return (
        <Card title={`Kaufnebenkosten (${r.bundesland})`}>
          <Row label="Grunderwerbsteuer" value={eur(r.grunderwerbsteuer)} />
          <Row label="Notar" value={eur(r.notary)} />
          <Row label="Grundbuch" value={eur(r.land_registry)} />
          <Row label="Makler" value={eur(r.makler)} />
          <Row label="Nebenkosten gesamt" value={eur(r.total_ancillary)} />
          <Row label="Gesamtinvestition" value={eur(r.total_investment)} />
          <Row label="Nebenkostenquote" value={pct(r.ancillary_quota_percent)} />
          <Row label="Mindest-Eigenkapital" value={eur(r.min_equity)} />
        </Card>
      );
    }
    case "affordability": {
      const r = calc.result;
      return (
        <Card title="Leistbarkeit">
          <Row label="Max. Monatsrate" value={eur(r.max_monthly_payment)} />
          <Row label="Max. Darlehen" value={eur(r.max_loan)} />
          <Row label="Max. Kaufpreis" value={eur(r.max_purchase_price)} />
          <Row label="Nebenkostenquote" value={pct(r.ancillary_quota_percent)} />
          <Row label="Eigenkapital" value={eur(r.equity)} />
        </Card>
      );
    }
    case "yield_metrics": {
      const r = calc.result;
      return (
        <Card title="Mietrendite">
          <Row label="Jahreskaltmiete" value={eur(r.annual_cold_rent)} />
          <Row label="Bruttorendite" value={pct(r.gross_yield_percent)} />
          <Row label="Nettorendite" value={pct(r.net_yield_percent)} />
          <Row label="Kaufpreisfaktor" value={num(r.kaufpreisfaktor)} />
        </Card>
      );
    }
    case "operating_costs": {
      const r = calc.result;
      return (
        <Card title="Bewirtschaftungskosten (p.a.)">
          <Row label="Instandhaltung" value={eur(r.instandhaltung)} />
          <Row label="Verwaltung" value={eur(r.verwaltung)} />
          <Row label="Mietausfallwagnis" value={eur(r.mietausfallwagnis)} />
          <Row label="Gesamt" value={eur(r.total_annual)} />
        </Card>
      );
    }
    case "equity_return": {
      const r = calc.result;
      return (
        <Card title="Eigenkapitalrendite (Jahr 1)">
          <Row label="Darlehen" value={eur(r.loan)} />
          <Row label="Kapitaldienst p.a." value={eur(r.annual_debt_service)} />
          <Row label="Netto-Mietertrag p.a." value={eur(r.net_operating_income)} />
          <Row label="Cashflow vor Steuern" value={eur(r.cashflow_before_tax)} />
          <Row label="EK-Rendite" value={pct(r.cash_on_cash_percent)} />
        </Card>
      );
    }
  }
}
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npm test && npm run build`
Expected: all pass, build green.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/CalcResultCard.tsx frontend/src/App.test.tsx
git commit -m "feat(frontend): render every calculator result as a typed card"
```

### Task 14: Extract `Chat.tsx` with polish (all tool calls, thinking, auto-scroll, abort, aria)

**Files:**
- Create: `frontend/src/Chat.tsx`, `frontend/src/Chat.test.tsx`
- Modify: `frontend/src/App.tsx`, `frontend/src/index.css`

- [ ] **Step 1: Create `frontend/src/Chat.tsx`** (replaces the chat portion of App; new: renders ALL tool calls via `CalcResultCard`, thinking bubble, auto-scroll, abort button, `role="alert"`):

```tsx
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
```

- [ ] **Step 2: Slim `frontend/src/App.tsx`** down to layout + Chat (tabs come in Task 17):

```tsx
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
```

- [ ] **Step 3: Append the thinking-indicator styles to `frontend/src/index.css`:**

```css
.thinking {
  color: var(--muted);
}
.dots i {
  display: inline-block;
  width: 5px;
  height: 5px;
  margin-right: 3px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.2s infinite ease-in-out;
}
.dots i:nth-child(2) {
  animation-delay: 0.2s;
}
.dots i:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes pulse {
  0%,
  80%,
  100% {
    opacity: 0.25;
  }
  40% {
    opacity: 1;
  }
}
```

- [ ] **Step 4: Create `frontend/src/Chat.test.tsx`:**

```tsx
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Chat } from "./Chat";

const askResponse = {
  answer: "Deine Monatsrate liegt bei 1.400 €.",
  tool_calls: [
    {
      name: "annuity",
      args: {},
      result: {
        monthly_payment: 1400,
        total_interest: 181209.86,
        total_paid: 481209.86,
        years_to_payoff: 28.7,
        remaining_debt_by_year: [{ year: 1, remaining_debt: 293900 }],
      },
    },
  ],
  sources: [],
  disclaimer: "Hinweis: keine Steuer-, Anlage- oder Finanzierungsberatung.",
};

function stubFetch(body: unknown, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify(body), {
          status,
          headers: { "Content-Type": "application/json" },
        }),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

function submitQuestion(text: string) {
  fireEvent.change(screen.getByLabelText("Frage"), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Fragen" }));
}

describe("Chat", () => {
  it("renders the answer and the annuity card after a round-trip", async () => {
    stubFetch(askResponse);
    render(<Chat />);
    submitQuestion("Was zahle ich monatlich?");
    expect(await screen.findByText("Deine Monatsrate liegt bei 1.400 €.")).toBeInTheDocument();
    expect(screen.getByText("Annuitätendarlehen")).toBeInTheDocument();
  });

  it("shows the German Ollama hint on 503", async () => {
    stubFetch({ detail: "down" }, 503);
    render(<Chat />);
    submitQuestion("hallo?");
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/Ollama ist nicht erreichbar/),
    );
  });

  it("shows a thinking indicator while waiting", async () => {
    let resolve!: (r: Response) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>((res) => (resolve = res))),
    );
    render(<Chat />);
    submitQuestion("dauert das?");
    expect(await screen.findByText(/denkt nach/)).toBeInTheDocument();
    resolve(
      new Response(JSON.stringify(askResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await waitFor(() => expect(screen.queryByText(/denkt nach/)).not.toBeInTheDocument());
  });
});
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && npm test && npm run build`
Expected: all pass (existing App tests still pass — header, empty state and disclaimer are unchanged), build green.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/Chat.tsx frontend/src/Chat.test.tsx frontend/src/App.tsx frontend/src/index.css
git commit -m "feat(frontend): chat pane with full tool rendering, waiting feedback and abort"
```

### Task 15: `CalcForms` — direct calculator forms (no LLM)

**Files:**
- Create: `frontend/src/CalcForms.tsx`, `frontend/src/CalcForms.test.tsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Create `frontend/src/CalcForms.tsx`:**

```tsx
// Direct, deterministic calculator forms against /api/finance/{calc} — no LLM involved.
// German decimal commas are accepted ("3,6" → 3.6).

import { type FormEvent, useState } from "react";

import { finance, toKnownCalc } from "./api";
import { CalcResultCard } from "./CalcResultCard";

interface Field {
  key: string;
  label: string;
  required?: boolean;
  text?: boolean; // string field (default: number)
  placeholder?: string;
}

interface FormSpec {
  calc: string;
  title: string;
  fields: Field[];
}

const FORMS: FormSpec[] = [
  {
    calc: "annuity",
    title: "Annuitätendarlehen",
    fields: [
      { key: "principal", label: "Darlehensbetrag (€)", required: true, placeholder: "300000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, placeholder: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        placeholder: "2,0",
      },
      { key: "annual_sondertilgung", label: "Sondertilgung (€/Jahr, optional)" },
    ],
  },
  {
    calc: "purchase_costs",
    title: "Kaufnebenkosten",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, placeholder: "300000" },
      {
        key: "bundesland",
        label: "Bundesland",
        required: true,
        text: true,
        placeholder: "Niedersachsen",
      },
      { key: "makler_rate_percent", label: "Maklerprovision Käufer (%, optional)" },
    ],
  },
  {
    calc: "affordability",
    title: "Leistbarkeit",
    fields: [
      { key: "net_monthly_income", label: "Haushaltsnetto (€/Monat)", required: true, placeholder: "4000" },
      { key: "equity", label: "Eigenkapital (€)", required: true, placeholder: "60000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, placeholder: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        placeholder: "2,0",
      },
      { key: "bundesland", label: "Bundesland", required: true, text: true, placeholder: "NRW" },
      { key: "existing_obligations", label: "Bestehende Raten (€/Monat, optional)" },
      { key: "running_costs_monthly", label: "Laufende Kosten (€/Monat, optional)" },
    ],
  },
  {
    calc: "yield_metrics",
    title: "Mietrendite",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, placeholder: "300000" },
      { key: "monthly_cold_rent", label: "Kaltmiete (€/Monat)", required: true, placeholder: "1200" },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten (€/Jahr, optional)" },
      { key: "ancillary_costs", label: "Kaufnebenkosten (€, optional)" },
    ],
  },
  {
    calc: "operating_costs",
    title: "Bewirtschaftungskosten",
    fields: [
      { key: "living_area_sqm", label: "Wohnfläche (m²)", required: true, placeholder: "100" },
      { key: "monthly_cold_rent", label: "Kaltmiete (€/Monat)", required: true, placeholder: "1200" },
      { key: "units", label: "Wohneinheiten (optional)" },
    ],
  },
  {
    calc: "equity_return",
    title: "Eigenkapitalrendite",
    fields: [
      { key: "purchase_price", label: "Kaufpreis (€)", required: true, placeholder: "300000" },
      { key: "monthly_cold_rent", label: "Kaltmiete (€/Monat)", required: true, placeholder: "1500" },
      { key: "equity", label: "Eigenkapital (€)", required: true, placeholder: "60000" },
      { key: "annual_rate_percent", label: "Sollzins (% p.a.)", required: true, placeholder: "3,6" },
      {
        key: "initial_repayment_percent",
        label: "Anfängliche Tilgung (%)",
        required: true,
        placeholder: "2,0",
      },
      { key: "ancillary_costs", label: "Kaufnebenkosten (€, optional)" },
      { key: "annual_operating_costs", label: "Bewirtschaftungskosten (€/Jahr, optional)" },
    ],
  },
];

function CalcForm({ spec }: { spec: FormSpec }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const args: Record<string, unknown> = {};
    for (const f of spec.fields) {
      const raw = (values[f.key] ?? "").trim();
      if (!raw) {
        if (f.required) {
          setError(`${f.label} fehlt.`);
          return;
        }
        continue;
      }
      if (f.text) {
        args[f.key] = raw;
      } else {
        const n = Number(raw.replace(",", "."));
        if (Number.isNaN(n)) {
          setError(`${f.label}: keine gültige Zahl.`);
          return;
        }
        args[f.key] = n;
      }
    }
    setBusy(true);
    try {
      const resp = await finance(spec.calc, args);
      setResult(resp.result);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const known = result ? toKnownCalc(spec.calc, result) : null;

  return (
    <form className="card-form" onSubmit={onSubmit}>
      <h3>{spec.title}</h3>
      {spec.fields.map((f) => (
        <label key={f.key}>
          {f.label}
          <input
            value={values[f.key] ?? ""}
            onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
            placeholder={f.placeholder}
            inputMode={f.text ? undefined : "decimal"}
          />
        </label>
      ))}
      <button type="submit" disabled={busy}>
        {busy ? "Rechnet …" : "Berechnen"}
      </button>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {known && <CalcResultCard calc={known} />}
    </form>
  );
}

export function CalcForms() {
  return (
    <div className="cards">
      {FORMS.map((f) => (
        <CalcForm key={f.calc} spec={f} />
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Append the form styles to `frontend/src/index.css`:**

```css
.cards {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 14px;
  align-content: start;
}
.card-form {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 14px;
}
.card-form h3 {
  margin: 0 0 10px;
  font-size: 14px;
  color: var(--accent);
}
.card-form label {
  display: block;
  font-size: 12px;
  color: var(--muted);
  margin: 8px 0 2px;
}
.card-form input,
.card-form select {
  width: 100%;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  padding: 7px 10px;
  font-size: 13px;
}
.card-form input:focus,
.card-form select:focus {
  outline: none;
  border-color: var(--accent);
}
.card-form button {
  margin-top: 10px;
  background: var(--accent);
  color: #12161c;
  border: none;
  border-radius: 8px;
  padding: 7px 14px;
  font-weight: 600;
  cursor: pointer;
}
.card-form button:disabled {
  opacity: 0.5;
  cursor: default;
}
```

- [ ] **Step 3: Create `frontend/src/CalcForms.test.tsx`:**

```tsx
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CalcForms } from "./CalcForms";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CalcForms", () => {
  it("renders one form per calculator", () => {
    render(<CalcForms />);
    for (const title of [
      "Annuitätendarlehen",
      "Kaufnebenkosten",
      "Leistbarkeit",
      "Mietrendite",
      "Bewirtschaftungskosten",
      "Eigenkapitalrendite",
    ]) {
      expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    }
  });

  it("submits the Kaufnebenkosten form and renders the result card", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              result: {
                bundesland: "NW",
                grunderwerbsteuer: 19500,
                notary: 4500,
                land_registry: 1500,
                makler: 10710,
                total_ancillary: 36210,
                total_investment: 336210,
                ancillary_quota_percent: 12.07,
                min_equity: 36210,
              },
              disclaimer: "x",
            }),
            { status: 200, headers: { "Content-Type": "application/json" } },
          ),
      ),
    );
    render(<CalcForms />);
    const form = screen.getByRole("heading", { name: "Kaufnebenkosten" }).closest("form")!;
    fireEvent.change(within(form).getByLabelText(/Kaufpreis/), { target: { value: "300000" } });
    fireEvent.change(within(form).getByLabelText(/Bundesland/), { target: { value: "NRW" } });
    fireEvent.submit(form);
    await waitFor(() =>
      expect(within(form).getByText("Grunderwerbsteuer")).toBeInTheDocument(),
    );
  });

  it("rejects a non-numeric value with a German error", async () => {
    render(<CalcForms />);
    const form = screen.getByRole("heading", { name: "Mietrendite" }).closest("form")!;
    fireEvent.change(within(form).getByLabelText(/Kaufpreis/), { target: { value: "abc" } });
    fireEvent.change(within(form).getByLabelText(/Kaltmiete/), { target: { value: "1200" } });
    fireEvent.submit(form);
    await waitFor(() =>
      expect(within(form).getByRole("alert")).toHaveTextContent(/keine gültige Zahl/),
    );
  });
});
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npm test && npm run build`
Expected: all pass, build green.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/CalcForms.tsx frontend/src/CalcForms.test.tsx frontend/src/index.css
git commit -m "feat(frontend): direct calculator forms without the LLM"
```

### Task 16: `Listings` — table + intake form + delete

**Files:**
- Create: `frontend/src/Listings.tsx`, `frontend/src/Listings.test.tsx`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Create `frontend/src/Listings.tsx`:**

```tsx
// Saved property objects: intake form + table over /api/listings.
// Object attributes only — never seller contact data (ADR-0001 / DSGVO).

import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";

import { createListing, deleteListing, type Listing, listListings } from "./api";
import { eur, num } from "./format";

const EMPTY_FORM = { price: "", area: "", bundesland: "", ort: "", rooms: "", year: "" };

export function Listings() {
  const [items, setItems] = useState<Listing[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      setItems(await listListings());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const price = Number(form.price.replace(",", "."));
    const area = Number(form.area.replace(",", "."));
    if (Number.isNaN(price) || price <= 0) {
      setError("Kaufpreis: keine gültige Zahl.");
      return;
    }
    if (Number.isNaN(area) || area <= 0) {
      setError("Wohnfläche: keine gültige Zahl.");
      return;
    }
    if (!form.bundesland.trim()) {
      setError("Bundesland fehlt.");
      return;
    }
    setBusy(true);
    try {
      await createListing({
        price,
        living_area_sqm: area,
        bundesland: form.bundesland.trim(),
        ort: form.ort.trim(),
        rooms: form.rooms ? Number(form.rooms.replace(",", ".")) : undefined,
        year_built: form.year ? Number(form.year) : undefined,
      });
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: number) {
    try {
      await deleteListing(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const set =
    (key: keyof typeof EMPTY_FORM) => (e: ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <div className="pane-scroll">
      <form className="card-form" onSubmit={onSubmit}>
        <h3>Objekt erfassen</h3>
        <label>
          Kaufpreis (€)
          <input value={form.price} onChange={set("price")} inputMode="decimal" placeholder="300000" />
        </label>
        <label>
          Wohnfläche (m²)
          <input value={form.area} onChange={set("area")} inputMode="decimal" placeholder="100" />
        </label>
        <label>
          Bundesland
          <input value={form.bundesland} onChange={set("bundesland")} placeholder="Niedersachsen" />
        </label>
        <label>
          Ort (optional)
          <input value={form.ort} onChange={set("ort")} placeholder="Lingen" />
        </label>
        <label>
          Zimmer (optional)
          <input value={form.rooms} onChange={set("rooms")} inputMode="decimal" />
        </label>
        <label>
          Baujahr (optional)
          <input value={form.year} onChange={set("year")} inputMode="numeric" />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Speichert …" : "Speichern"}
        </button>
      </form>

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

      {items.length === 0 ? (
        <p className="empty">
          Noch keine Objekte gespeichert. Erfasse oben dein erstes Objekt — nur Objektdaten, keine
          Anbieterkontakte.
        </p>
      ) : (
        <table className="listing-table">
          <thead>
            <tr>
              <th>Ort</th>
              <th>BL</th>
              <th>Typ</th>
              <th>Preis</th>
              <th>m²</th>
              <th>€/m²</th>
              <th>Zimmer</th>
              <th>Baujahr</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id}>
                <td>{it.ort || "—"}</td>
                <td>{it.bundesland}</td>
                <td>{it.object_type}</td>
                <td className="num">{eur(it.price)}</td>
                <td className="num">{num(it.living_area_sqm)}</td>
                <td className="num">{eur(it.price_per_sqm)}</td>
                <td className="num">{it.rooms ?? "—"}</td>
                <td className="num">{it.year_built ?? "—"}</td>
                <td>
                  <button
                    type="button"
                    className="del"
                    onClick={() => void onDelete(it.id)}
                    aria-label={`Objekt ${it.id} löschen`}
                  >
                    Löschen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Append the listing styles to `frontend/src/index.css`:**

```css
.pane-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.empty {
  color: var(--muted);
  font-size: 13px;
}
.listing-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.listing-table th,
.listing-table td {
  text-align: right;
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
}
.listing-table th:first-child,
.listing-table td:first-child {
  text-align: left;
}
.listing-table td.num,
.listing-table th {
  font-family: var(--mono);
}
.listing-table .del {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  border-radius: 6px;
  padding: 2px 8px;
  cursor: pointer;
}
.listing-table .del:hover {
  border-color: #f2917a;
  color: #f2917a;
}
```

- [ ] **Step 3: Create `frontend/src/Listings.test.tsx`:**

```tsx
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Listings } from "./Listings";

afterEach(() => {
  vi.unstubAllGlobals();
});

const oneListing = [
  {
    id: 1,
    price: 300000,
    living_area_sqm: 100,
    bundesland: "NI",
    plz: "",
    ort: "Lingen",
    rooms: 3,
    year_built: 1995,
    object_type: "wohnung",
    features: [],
    source_url: "",
    price_per_sqm: 3000,
  },
];

describe("Listings", () => {
  it("renders fetched listings in the table", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify(oneListing), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    render(<Listings />);
    expect(await screen.findByText("Lingen")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Objekt 1 löschen" })).toBeInTheDocument();
  });

  it("shows the empty state when there are no listings", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
      ),
    );
    render(<Listings />);
    expect(await screen.findByText(/Noch keine Objekte gespeichert/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 4: Run tests**

Run: `cd frontend && npm test && npm run build`
Expected: all pass, build green.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/Listings.tsx frontend/src/Listings.test.tsx frontend/src/index.css
git commit -m "feat(frontend): listings tab with intake form and delete"
```

### Task 17: Tab navigation — Chat / Rechner / Objekte

**Files:**
- Modify: `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/src/App.test.tsx`

- [ ] **Step 1: Write the failing test** — append to `frontend/src/App.test.tsx` (add `fireEvent` to the testing-library import):

```tsx
describe("Tabs", () => {
  it("switches to the Rechner tab", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("tab", { name: "Rechner" }));
    expect(screen.getByRole("heading", { name: "Annuitätendarlehen" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify it fails**

Run: `cd frontend && npm test`
Expected: FAIL — no element with role `tab`.

- [ ] **Step 3: Rewrite `frontend/src/App.tsx`:**

```tsx
import { useState } from "react";

import { CalcForms } from "./CalcForms";
import { Chat } from "./Chat";
import { Listings } from "./Listings";

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
```

- [ ] **Step 4: Append the tab styles to `frontend/src/index.css`:**

```css
.tabs {
  display: flex;
  gap: 6px;
  margin-top: 12px;
}
.tab {
  background: transparent;
  border: 1px solid var(--border);
  border-bottom: none;
  border-radius: 8px 8px 0 0;
  color: var(--muted);
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
}
.tab.active {
  background: var(--panel);
  color: var(--text);
  border-color: var(--accent);
}
.pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.pane[hidden] {
  display: none;
}
```

- [ ] **Step 5: Run tests.** Note: the Listings pane mounts on first render and fires its initial `fetch` — in the existing App tests no fetch stub exists, so `refresh()` catches the error and shows it in the (hidden) pane; no test asserts against it, and nothing throws. If a test run shows unhandled-rejection noise, stub a default fetch in those App tests with `vi.stubGlobal("fetch", vi.fn(async () => new Response("[]", { status: 200 })))`.

Run: `cd frontend && npm test && npm run build`
Expected: all pass, build green.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/index.css
git commit -m "feat(frontend): tab navigation for chat, calculators and listings"
```

---

## Part E — Finalize

### Task 18: Full gate, docs, log

**Files:**
- Modify: `README.md`, `AUTOPILOT_LOG.md`, this plan file

- [ ] **Step 1: Run everything**

```bash
uv run pytest -q && uv run ruff check .
cd frontend && npm test && npm run build && cd ..
```

Expected: pytest all green (well above the 97 baseline), ruff clean, vitest green, build green.

- [ ] **Step 2: Update `README.md`:** document the three frontend tabs (Chat / Rechner / Objekte), the two new calculators (`operating_costs`, `equity_return`) with their CLI commands (`finance opcosts`, `finance equity`), `scout delete`, and the assistant's `list_listings` tool. Match the README's existing tone and structure — extend the relevant sections, do not restructure.

- [ ] **Step 3: Append one line to `AUTOPILOT_LOG.md`** following its existing format, e.g.:

```
- 2026-07-XX — Hardening+UX (plan 2026-07-07): typed dispatch, loop guards, RAG threshold+cache,
  rate bounds, operating_costs+equity_return (tools+CLI), assistant list_listings, listing DELETE,
  frontend tabs (Chat/Rechner/Objekte) with forms+listings view. Gate green.
```

- [ ] **Step 4: Append an Outcome section to THIS plan file** (`docs/superpowers/plans/2026-07-07-stage1-hardening-and-ux.md`): what was implemented, any deviations, open points.

- [ ] **Step 5: Optional live smoke (Needs Ollama — skip if not running):**

```bash
uv run uvicorn estatescout.api:app --port 8000
# → then open http://localhost:8000 : all three tabs, one form calculation,
#   one chat question, one listing add+delete. Ask "Welche Objekte habe ich gespeichert?"
#   and verify the assistant calls list_listings.
```

- [ ] **Step 6: Commit**

```bash
git add README.md AUTOPILOT_LOG.md docs/superpowers/plans/2026-07-07-stage1-hardening-and-ux.md
git commit -m "docs: record hardening+ux outcome"
```

---

## Outcome (2026-09-20)

**Status: complete — all 18 tasks implemented, 18 commits on `feat/stage1-hardening`
(branched off `autopilot/work`).**

Gate at completion of this plan: **130 pytest** (from 97 at plan time), ruff clean,
**14 vitest**, `npm run build` green. One commit per task, Conventional Commits.

### What was built

| Task | Result |
| ---- | ------ |
| 1 | `_clean_args()` in `assistant/tools.py`: explicit `null` = absent, numeric strings coerced, bools and non-coercible values rejected loudly. `/api/finance/{calc}` now answers 400 instead of 500 on a wrong type. |
| 2 | `_parse_tool_call()` in `assistant/assistant.py`: malformed tool calls are skipped with an error fed back, JSON-string arguments are parsed, `TypeError`/`KeyError` no longer escape the loop. |
| 3 | `estatescout/errors.py` holds `OllamaUnavailable`; `chat.py` re-exports it, `rag/embedder.py` maps `httpx.HTTPError` onto it → `/api/ask` returns 503, not 500, when Ollama is down at index-build time. |
| 4 | `RagIndex.retrieve(..., min_score=)` plus `MIN_RAG_SCORE = 0.35`; off-topic questions get no "Auszüge" block and the prompt tells the model to say the knowledge base has nothing. |
| 5 | `rag.index.load_or_build()` with a SHA-256 corpus+model fingerprint and a per-process cache in the API; the corpus is no longer re-embedded on every request. |
| 6 | Fraction sanity bounds (`annual_rate > 0.25`, `initial_repayment > 0.2`) in `annuity` and `affordability`. |
| 7 | `finance/operating_costs.py` + the `bewirtschaftung` config block; the two dead blocks (`management_cost_eur_per_sqm`, `reference_interest`) removed. |
| 8 | `finance/equity_return.py` — first-year cash-on-cash. |
| 9 | Both new calculators exposed as tools and as `finance opcosts` / `finance equity`. |
| 10 | `listing_tools(store)` + `Assistant(extra_tools=...)`; the assistant can read saved objects. `/api/finance/list_listings` stays a 400 (guard tested). |
| 11 | `DELETE /api/listings/{id}` (404 on unknown) + `scout delete`. |
| 12 | `frontend/src/format.ts` + rewritten `api.ts` with `toKnownCalc()` as the single narrowing boundary and German error messages. |
| 13 | `CalcResultCard` renders all six calculator results. |
| 14 | `Chat.tsx` extracted: all tool calls rendered, thinking indicator, auto-scroll, abort, `role="alert"`. |
| 15 | `CalcForms.tsx` — six direct forms against `/api/finance/{calc}`, German decimal commas accepted, no LLM. |
| 16 | `Listings.tsx` — intake form, table, delete. |
| 17 | Tab navigation (Chat / Rechner / Objekte); panes stay mounted so tab state survives. |
| 18 | Full gate, README, `AUTOPILOT_LOG.md`, this section. |

### Deviations from the plan

1. **Task 4, test assertion corrected.** The plan's `test_no_context_message_when_all_hits_below_threshold`
   asserts `not any("Auszüge" in m["content"] ...)`, but `SYSTEM_PROMPT` rule 2 itself contains
   the word "Auszüge" — the test could never pass. Tightened to the context block's own prefix
   `"Auszüge aus der Wissensbasis"`, and the pre-existing positive test at
   `test_assistant_loop.py:53` was tightened the same way (it was matching the system prompt).
2. **Task 1, `isinstance(value, int | float)`** instead of the plan's `(int, float)` tuple — ruff's
   `UP` ruleset rejects the tuple form. Same semantics.
3. **Task 17, App tests made async.** Mounting the Listings pane fires a fetch on first render,
   which produced React `act()` warnings in the App tests. Rather than leave the noise, the three
   App tests await the settled empty state via a `renderApp()` helper.
4. **README quickstart corrected.** The plan did not mention it, but the existing README's first
   example (`finance.py annuity --price ... --equity ...`) used flags the CLI does not have. The
   documented commands are now the real ones and were executed to verify.

### Live verification (Ollama, 2026-09-20)

Real `qwen2.5:7b` via `OllamaChat`, no fakes — both new integration points exercised:

```
### Was zahle ich monatlich für 300.000 Euro Darlehen bei 3,6 % Zins und 2 % Tilgung?
TOOLS:  [{"name": "annuity", "args": {"principal": 300000, "annual_rate_percent": 3.6,
          "initial_repayment_percent": 2}}]
RESULT: {"monthly_payment": 1400.0, "total_interest": 181209.86, ...}
ANSWER: Die monatliche Kreditrate beträgt 1400 EUR. ...

### Welche Objekte habe ich gespeichert?
TOOLS:  [{"name": "list_listings", "args": {}}]
RESULT: {"count": 1, "listings": [{"id": 1, "ort": "Lingen", "bundesland": "NI",
          "price": 300000.0, "living_area_sqm": 100.0, "price_per_sqm": 3000.0, ...}]}
ANSWER: Sie haben ein Objekt in Lingen (Niedersachsen) gespeichert. ...
```

The monthly payment is the tested `finance/` number, not the model's arithmetic, and the new
`list_listings` extra tool works against a real model.

**Finding worth keeping:** in the first answer the model rendered the tool's `181209.86` as
"181.210,86 EUR" — it garbled a number it was only supposed to quote. Prompt-only honesty does not
bind free text (explicitly out of scope for this plan). The Stage-2 tool-trace panel makes exactly
this inspectable; a code-level check that free-text numbers match tool results remains open.

### Not verified

The RAG half could not be exercised live: this machine's Ollama answers
`/api/embeddings` with *"This server does not support embeddings. Start it with `--embeddings`"*,
and `nomic-embed-text` is not pulled. → Needs Nico (see `PLAN.md`).
