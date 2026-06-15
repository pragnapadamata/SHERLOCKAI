"""Retrieve-then-rerank over the Chroma store.

Vector search pulls ``top_k`` candidates (optionally scoped to an equipment via
the ``equipment_id``/``"shared"`` metadata filter), then the cross-encoder
reranks them and the best ``top_n`` are returned with their provenance metadata.
"""

from __future__ import annotations

from backend.app.retrieval.embeddings import Embedder
from backend.app.retrieval.reranker import Reranker
from backend.app.retrieval.schemas import Chunk, RetrievedChunk
from backend.app.retrieval.vector_store import VectorStore


def _build_where(equipment_id: str | None, doc_type: str | None) -> dict | None:
    clauses: list[dict] = []
    if equipment_id:
        clauses.append({"equipment_id": {"$in": [equipment_id, "shared"]}})
    if doc_type:
        clauses.append({"doc_type": {"$eq": doc_type}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


class KnowledgeRetriever:
    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        reranker: Reranker,
        *,
        top_k: int = 20,
        top_n: int = 5,
    ) -> None:
        self._store = store
        self._embedder = embedder
        self._reranker = reranker
        self._top_k = top_k
        self._top_n = top_n

    def search(
        self,
        query: str,
        *,
        equipment_id: str | None = None,
        doc_type: str | None = None,
        top_k: int | None = None,
        top_n: int | None = None,
    ) -> list[RetrievedChunk]:
        top_k = top_k or self._top_k
        top_n = top_n or self._top_n

        query_vec = self._embedder.embed_query(query)
        where = _build_where(equipment_id, doc_type)
        hits = self._store.query(query_vec, n_results=top_k, where=where)
        if not hits:
            return []

        scores = self._reranker.rerank(query, [h.document for h in hits])
        ranked = sorted(zip(hits, scores, strict=True), key=lambda hs: hs[1], reverse=True)

        results: list[RetrievedChunk] = []
        for hit, score in ranked[:top_n]:
            results.append(
                RetrievedChunk(chunk=Chunk.from_metadata(hit.metadata, hit.document), score=score)
            )
        return results
