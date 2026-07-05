#!/usr/bin/env python
"""Ask the local real-estate assistant. Run: uv run python scripts/ask.py "deine Frage"

Needs Ollama running with a tool-calling model + an embedding model, e.g.:
    ollama serve & ollama pull qwen2.5:7b && ollama pull nomic-embed-text
"""

import typer

from estatescout.cli import ask

if __name__ == "__main__":
    typer.run(ask)
