#!/usr/bin/env bash
# Repeatable live verification against a real local Ollama.
#
#   ./scripts/verify_live.sh
#
# Exits 0 when every check passes AND when Ollama is simply not running (honest degradation
# is not a failure); exits 1 when a check actually fails. Override the per-call client
# timeout with VERIFY_TIMEOUT (seconds, default 900 — a 7B model on CPU is slow).
set -euo pipefail

cd "$(dirname "$0")/.."

OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"

if ! curl -sf -m 5 "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then
  echo "Ollama is not reachable at ${OLLAMA_HOST} — skipping the live verification."
  echo "Start it with 'ollama serve', then: ollama pull qwen2.5:7b && ollama pull nomic-embed-text"
  exit 0
fi

exec uv run python scripts/verify_live.py
