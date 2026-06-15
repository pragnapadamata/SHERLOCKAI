"""Retrieval data types: chunks and retrieved (reranked) chunks."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A retrievable piece of a document, carrying provenance metadata."""

    chunk_id: str
    doc_id: str
    doc_type: str
    equipment_id: str  # the asset it pertains to, or "shared"
    source: str        # relative filename, for citation
    section: str       # heading, for citation
    title: str
    chunk_index: int
    text: str
    fault_code: str | None = None
    refs: list[str] = field(default_factory=list)  # [[TYPE:id]] tokens in the chunk

    def to_metadata(self) -> dict:
        """Chroma metadata: scalar values only, no None (refs joined with '|')."""

        meta: dict[str, str | int] = {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "equipment_id": self.equipment_id,
            "source": self.source,
            "section": self.section,
            "title": self.title,
            "chunk_index": self.chunk_index,
            "refs": "|".join(self.refs),
        }
        if self.fault_code:
            meta["fault_code"] = self.fault_code
        return meta

    @classmethod
    def from_metadata(cls, metadata: dict, text: str) -> Chunk:
        refs = [r for r in str(metadata.get("refs", "")).split("|") if r]
        return cls(
            chunk_id=str(metadata["chunk_id"]),
            doc_id=str(metadata["doc_id"]),
            doc_type=str(metadata["doc_type"]),
            equipment_id=str(metadata["equipment_id"]),
            source=str(metadata["source"]),
            section=str(metadata["section"]),
            title=str(metadata.get("title", "")),
            chunk_index=int(metadata.get("chunk_index", 0)),
            text=text,
            fault_code=(str(metadata["fault_code"]) if metadata.get("fault_code") else None),
            refs=refs,
        )


@dataclass
class RetrievedChunk:
    """A chunk returned by the retriever, with its rerank score."""

    chunk: Chunk
    score: float
