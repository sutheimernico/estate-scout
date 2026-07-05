"""Tests for the heading-aware Markdown chunker."""

from estatescout.rag.chunker import chunk_markdown

DOC = """# Title

Intro line under the title.

## Section A

Alpha paragraph one.

Alpha paragraph two.

## Section B

Beta content.
"""


def test_splits_by_heading_and_tags_source():
    chunks = chunk_markdown(DOC, "sample.md", max_chars=1000)
    headings = [c.heading for c in chunks]
    assert "Section A" in headings
    assert "Section B" in headings
    assert all(c.source == "sample.md" for c in chunks)


def test_chunk_text_carries_its_heading():
    chunks = chunk_markdown(DOC, "sample.md", max_chars=1000)
    section_a = next(c for c in chunks if c.heading == "Section A")
    assert section_a.text.startswith("Section A")
    assert "Alpha paragraph" in section_a.text


def test_large_section_splits_into_multiple_chunks():
    big = "# T\n\n## Big\n\n" + "\n\n".join(f"Paragraph number {i} with words." for i in range(50))
    chunks = chunk_markdown(big, "big.md", max_chars=200)
    big_chunks = [c for c in chunks if c.heading == "Big"]
    assert len(big_chunks) > 1
    # each chunk's paragraph body stays near the bound (heading prefix adds a little)
    assert all(len(c.text) <= 200 + len("Big") + 4 for c in big_chunks)


def test_invalid_max_chars_raises():
    import pytest

    with pytest.raises(ValueError):
        chunk_markdown(DOC, "sample.md", max_chars=0)
