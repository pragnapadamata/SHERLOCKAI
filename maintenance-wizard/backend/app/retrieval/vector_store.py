"""Thin Chroma wrapper: one collection, cosine space, telemetry off.

We pass precomputed embeddings in and out, so Chroma's own embedding function is
never used and the embedder stays our swappable component. A persistent store
backs the runtime; an ephemeral store backs tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Hit:
    id: str
    document: str
    metadata: dict
    distance: float


class VectorStore:
    def __init__(self, client: Any, collection_name: str) -> None:
        self._client = client
        self.collection_name = collection_name
        self._collection = client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    @classmethod
    def persistent(cls, path: str, collection_name: str = "maintenance_kb") -> VectorStore:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.PersistentClient(
            path=path, settings=ChromaSettings(anonymized_telemetry=False)
        )
        return cls(client, collection_name)

    @classmethod
    def ephemeral(cls, collection_name: str = "maintenance_kb") -> VectorStore:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        client = chromadb.EphemeralClient(settings=ChromaSettings(anonymized_telemetry=False))
        return cls(client, collection_name)

    def reset(self) -> None:
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:  # noqa: BLE001 -- absent collection is fine
            pass
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        if not ids:
            return
        self._collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def count(self) -> int:
        return self._collection.count()

    def query(
        self, embedding: list[float], n_results: int, where: dict | None = None
    ) -> list[Hit]:
        res = self._collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        return [
            Hit(id=i, document=d, metadata=dict(m), distance=float(x))
            for i, d, m, x in zip(ids, docs, metas, dists, strict=True)
        ]
