"""Retrieve-then-rerank flow and per-equipment scoping (deterministic fakes)."""

from __future__ import annotations


def test_search_returns_relevant_scoped_chunks(fake_retriever):
    results = fake_retriever.search("gear pitting", equipment_id="HSM-F3-GBX")
    assert results
    # scoping: only the asset's chunks or shared SOPs
    assert all(r.chunk.equipment_id in ("HSM-F3-GBX", "shared") for r in results)
    # the asset's own content is surfaced
    assert any(r.chunk.equipment_id == "HSM-F3-GBX" for r in results)


def test_scoping_excludes_other_assets(fake_retriever):
    results = fake_retriever.search("bearing replacement", equipment_id="HSM-F3-GBX", top_n=20)
    assert results
    assert all(r.chunk.equipment_id in ("HSM-F3-GBX", "shared") for r in results)
    assert all(r.chunk.equipment_id != "HSM-F2-WRB" for r in results)


def test_doc_type_filter(fake_retriever):
    results = fake_retriever.search("gear", doc_type="fault_catalog", top_n=10)
    assert results
    assert all(r.chunk.doc_type == "fault_catalog" for r in results)


def test_results_are_rerank_ordered(fake_retriever):
    results = fake_retriever.search("oil iron particle gear mesh sidebands", equipment_id="HSM-F3-GBX")
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
