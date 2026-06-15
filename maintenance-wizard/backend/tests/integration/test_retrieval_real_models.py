"""Real local models end-to-end (slow; deselected by default).

Run with: uv run pytest -m slow
Downloads the bge-small embedder and the MiniLM reranker on first run.
"""

from __future__ import annotations

import pytest

from backend.app.retrieval.embeddings import build_embedder
from backend.app.retrieval.ingest import ingest_documents
from backend.app.retrieval.reranker import build_reranker
from backend.app.retrieval.retriever import KnowledgeRetriever
from backend.app.retrieval.vector_store import VectorStore
from backend.scripts.build_index import build_doc_inputs


@pytest.mark.slow
def test_real_pipeline_finds_f3_gearbox_sources():
    store = VectorStore.ephemeral("rt_real_test")
    embedder = build_embedder()
    ingest_documents(store, embedder, build_doc_inputs())
    retriever = KnowledgeRetriever(store, embedder, build_reranker(), top_k=20, top_n=5)

    results = retriever.search(
        "gear tooth pitting with rising oil iron particles", equipment_id="HSM-F3-GBX"
    )
    assert results
    assert all(r.chunk.equipment_id in ("HSM-F3-GBX", "shared") for r in results)
    doc_ids = {r.chunk.doc_id for r in results}
    assert any("GBX" in d or "F3" in d for d in doc_ids)
