"""Chunking: section splitting, ref extraction, equipment scoping, stable ids."""

from __future__ import annotations

from backend.app.core.config import RAW_DOCS
from backend.app.retrieval.chunking import chunk_document


def _read(rel: str) -> str:
    return (RAW_DOCS / rel).read_text()


def test_manual_chunks_carry_asset_sections_and_refs():
    rel = "manuals/HSM-F3-GBX_manual.md"
    chunks = chunk_document(
        _read(rel), doc_id="HSM-F3-GBX_manual", doc_type="manual",
        source=rel, equipment_id="HSM-F3-GBX",
    )
    assert len(chunks) >= 3
    assert all(c.equipment_id == "HSM-F3-GBX" for c in chunks)
    assert "Troubleshooting" in {c.section for c in chunks}
    assert any("[[FAULT:F3-GBX-002]]" in c.refs for c in chunks)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_sop_chunks_are_shared():
    rel = "sops/SOP-GBX-001_gear_inspection.md"
    chunks = chunk_document(
        _read(rel), doc_id="SOP-GBX-001", doc_type="sop", source=rel, equipment_id="shared"
    )
    assert chunks
    assert all(c.equipment_id == "shared" for c in chunks)


def test_fault_catalog_splits_per_entry_with_derived_asset():
    rel = "fault_catalog/fault_codes.md"
    chunks = chunk_document(
        _read(rel), doc_id="fault_codes", doc_type="fault_catalog", source=rel, equipment_id=None
    )
    entries = [c for c in chunks if c.fault_code]
    assert len(entries) >= 20
    f3 = next(c for c in entries if c.fault_code == "F3-GBX-002")
    assert f3.equipment_id == "HSM-F3-GBX"
