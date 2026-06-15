"""Ingest documents into the vector store: chunk, embed, write.

Kept decoupled from the generation spec: callers pass ``DocInput`` records (the
build script derives them from the document set).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.app.core.logging import get_logger
from backend.app.retrieval.chunking import chunk_document
from backend.app.retrieval.embeddings import Embedder
from backend.app.retrieval.vector_store import VectorStore

log = get_logger(__name__)


@dataclass
class DocInput:
    path: Path
    doc_id: str
    doc_type: str          # manual | sop | failure_report | fault_catalog
    source: str            # relative path for citation, e.g. "manuals/HSM-F3-GBX_manual.md"
    equipment_id: str | None  # asset id, "shared" for SOPs, or None for fault catalog


def ingest_documents(
    store: VectorStore, embedder: Embedder, doc_inputs: list[DocInput]
) -> int:
    """Rebuild the collection from scratch and return the chunk count."""

    store.reset()
    chunks = []
    for di in doc_inputs:
        text = di.path.read_text()
        chunks.extend(chunk_document(
            text, doc_id=di.doc_id, doc_type=di.doc_type,
            source=di.source, equipment_id=di.equipment_id,
        ))
    if not chunks:
        return 0

    embeddings = embedder.embed_documents([c.text for c in chunks])
    store.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[c.to_metadata() for c in chunks],
    )
    log.info("ingest_complete", chunks=len(chunks))
    return len(chunks)
