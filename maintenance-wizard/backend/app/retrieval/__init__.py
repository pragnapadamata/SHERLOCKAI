"""Knowledge retrieval: local ONNX embeddings + reranker over a Chroma store.

The pipeline is provider-free at query time (no LLM API). Documents are chunked
with provenance metadata, embedded locally, stored in a single Chroma collection
with per-equipment scoping via metadata filters, and retrieved with a
retrieve-then-rerank flow. Embedder and reranker sit behind protocols so tests
inject deterministic fakes and the models stay swappable.
"""
