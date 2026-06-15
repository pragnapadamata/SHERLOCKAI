"""Local embeddings behind a swappable protocol (fastembed / ONNX by default)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger

log = get_logger(__name__)

# A safe fallback that ships in fastembed if the configured model is unavailable.
_FALLBACK_EMBEDDING = "BAAI/bge-small-en-v1.5"


@runtime_checkable
class Embedder(Protocol):
    """Turns text into vectors. Documents and queries may embed differently."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedEmbedder:
    """ONNX embeddings via fastembed (no PyTorch)."""

    def __init__(self, model_name: str) -> None:
        from fastembed import TextEmbedding

        supported = {m["model"] for m in TextEmbedding.list_supported_models()}
        if model_name not in supported:
            log.warning("embedding_model_unsupported", requested=model_name,
                        fallback=_FALLBACK_EMBEDDING)
            model_name = _FALLBACK_EMBEDDING
        self.model_name = model_name
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [list(map(float, v)) for v in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return list(map(float, next(iter(self._model.query_embed(text)))))


def build_embedder(settings: Settings | None = None) -> Embedder:
    settings = settings or get_settings()
    return FastEmbedEmbedder(settings.embedding_model)
