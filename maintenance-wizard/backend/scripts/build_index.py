"""Build the runtime stores: load CSVs into SQLite and ingest documents into Chroma.

Both targets are gitignored and rebuilt from the committed substrate. First run
downloads the local embedding model (cached afterwards).

    uv run python -m backend.scripts.build_index
"""

from __future__ import annotations

from backend.app.core.config import RAW_DOCS, get_settings
from backend.app.core.logging import configure_logging
from backend.app.data_access import loader
from backend.app.retrieval.embeddings import build_embedder
from backend.app.retrieval.ingest import DocInput, ingest_documents
from backend.app.retrieval.vector_store import VectorStore


def build_doc_inputs() -> list[DocInput]:
    from backend.scripts.data_substrate import spec

    inputs: list[DocInput] = []
    for ds in spec.DOCS:
        doc_type = ds.doc_type.value
        if doc_type == "sop":
            equipment_id: str | None = "shared"
        elif doc_type == "fault_catalog":
            equipment_id = None  # derived per fault entry during chunking
        else:
            equipment_id = ds.equipment_id
        inputs.append(DocInput(
            path=RAW_DOCS / ds.rel_path, doc_id=ds.doc_id, doc_type=doc_type,
            source=ds.rel_path, equipment_id=equipment_id,
        ))
    return inputs


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, dev=settings.app_env != "prod")

    print("== SQLite ==")
    for table, count in loader.build_database(settings).items():
        print(f"  {table}: {count} rows")

    print("== Vector store (Chroma) ==")
    store = VectorStore.persistent(settings.vector_store_path, settings.kb_collection)
    embedder = build_embedder(settings)
    n_chunks = ingest_documents(store, embedder, build_doc_inputs())
    print(f"  embedded {n_chunks} chunks into '{settings.kb_collection}' "
          f"at {settings.vector_store_path}")
    print(f"  collection count: {store.count()}")


if __name__ == "__main__":
    main()
