"""Chunk substrate documents by Markdown section, capturing provenance metadata.

Manuals, SOPs, and failure reports split on ``##`` sections; the fault catalog
splits per fault entry (``###``). Each chunk records the section heading, the
``[[TYPE:id]]`` reference tokens it contains, and the equipment it pertains to
(the document's asset, ``"shared"`` for SOPs, or, for the fault catalog, the
asset named in the entry).
"""

from __future__ import annotations

import re

from backend.app.retrieval.schemas import Chunk

REF_RE = re.compile(r"\[\[([A-Z]+:[^\]]+)\]\]")
ASSET_REF_RE = re.compile(r"\[\[ASSET:([^\]]+)\]\]")


def _slug(text: str, limit: int = 40) -> str:
    text = re.sub(r"\[\[[A-Z]+:([^\]]+)\]\]", r"\1", text)  # unwrap tokens
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:limit] or "section"


def _split_long(body: str, max_chars: int, overlap: int) -> list[str]:
    if len(body) <= max_chars:
        return [body]
    pieces: list[str] = []
    start = 0
    while start < len(body):
        end = min(start + max_chars, len(body))
        if end < len(body):
            space = body.rfind(" ", start + max_chars - overlap, end)
            if space > start:
                end = space
        pieces.append(body[start:end].strip())
        if end >= len(body):
            break
        start = max(end - overlap, start + 1)
    return [p for p in pieces if p]


def chunk_document(
    text: str,
    *,
    doc_id: str,
    doc_type: str,
    source: str,
    equipment_id: str | None,
    title: str | None = None,
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[Chunk]:
    """Split one document into provenance-tagged chunks."""

    split_prefixes = ("## ", "### ") if doc_type == "fault_catalog" else ("## ",)
    lines = text.splitlines()

    doc_title = title
    sections: list[tuple[str, list[str]]] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    def flush() -> None:
        if any(line.strip() for line in current_lines):
            sections.append((current_heading, current_lines.copy()))

    for line in lines:
        if doc_title is None and line.startswith("# ") and not line.startswith("## "):
            doc_title = line[2:].strip()
            continue
        if line.lstrip().startswith(">"):  # prototype banner / blockquotes
            continue
        if any(line.startswith(p) for p in split_prefixes):
            flush()
            current_heading = line.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    doc_title = doc_title or doc_id
    chunks: list[Chunk] = []
    for sec_ord, (heading, body_lines) in enumerate(sections):
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        for sub, piece in enumerate(_split_long(body, max_chars, overlap)):
            refs = [f"[[{m}]]" for m in REF_RE.findall(piece)]
            if equipment_id is not None:
                eid = equipment_id
            else:  # fault catalog: take the asset named in the entry heading/body
                m = ASSET_REF_RE.search(heading) or ASSET_REF_RE.search(piece)
                eid = m.group(1) if m else "shared"
            suffix = f"::{sub}" if sub else ""
            chunk_id = f"{doc_id}::{sec_ord:02d}-{_slug(heading)}{suffix}"
            fault_code = None
            if doc_type == "fault_catalog":
                fm = re.search(r"\[\[FAULT:([^\]]+)\]\]", heading)
                fault_code = fm.group(1) if fm else None
            chunks.append(Chunk(
                chunk_id=chunk_id, doc_id=doc_id, doc_type=doc_type, equipment_id=eid,
                source=source, section=heading, title=doc_title, chunk_index=sec_ord,
                text=piece, fault_code=fault_code, refs=refs,
            ))
    return chunks
