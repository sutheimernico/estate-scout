"""Heading-aware Markdown chunking for the knowledge corpus.

Splits a Markdown document into retrieval chunks at heading boundaries; a section longer
than ``max_chars`` is split further at paragraph boundaries. Each chunk carries its source
doc name and nearest heading so retrieval results can be cited.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^#{1,6}\s+(.*)$")


@dataclass(frozen=True)
class Chunk:
    source: str  # corpus doc filename, e.g. "03-finanzierung.md"
    heading: str  # nearest heading text
    text: str  # chunk text, prefixed with the heading for context


def _split_paragraphs(body: str, max_chars: int) -> list[str]:
    """Greedily pack blank-line-separated paragraphs into <= max_chars parts."""
    parts: list[str] = []
    cur = ""
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if not para:
            continue
        if cur and len(cur) + len(para) + 2 > max_chars:
            parts.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur:
        parts.append(cur)
    return parts


def chunk_markdown(text: str, source: str, *, max_chars: int = 1000) -> list[Chunk]:
    """Split a Markdown document into heading-aware chunks."""
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")

    sections: list[tuple[str, str]] = []
    heading = ""
    buf: list[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            sections.append((heading, body))

    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            flush()
            buf = []
            heading = m.group(1).strip()
        else:
            buf.append(line)
    flush()

    chunks: list[Chunk] = []
    for head, body in sections:
        for part in _split_paragraphs(body, max_chars):
            chunk_text = f"{head}\n\n{part}" if head else part
            chunks.append(Chunk(source=source, heading=head, text=chunk_text))
    return chunks
