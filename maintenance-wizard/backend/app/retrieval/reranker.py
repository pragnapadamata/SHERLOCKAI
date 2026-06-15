"""Local cross-encoder reranker behind a swappable protocol (fastembed / ONNX).

Per the Phase 2 decision the default is the small ms-marco MiniLM cross-encoder;
``BAAI/bge-reranker-base`` is a config-only swap. The configured name is verified
against fastembed's supported list at build time and falls back if unavailable.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import get_logger

log = get_logger(__name__)

_FALLBACK_RERANKER = "Xenova/ms-marco-MiniLM-L-6-v2"


@runtime_checkable
class Reranker(Protocol):
    """Scores each document for relevance to the query (higher == better)."""

    def rerank(self, query: str, documents: list[str]) -> list[float]: ...


class FastEmbedReranker:
    """ONNX cross-encoder reranker via fastembed."""

    def __init__(self, model_name: str) -> None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        supported = {m["model"] for m in TextCrossEncoder.list_supported_models()}
        if model_name not in supported:
            chosen = _FALLBACK_RERANKER if _FALLBACK_RERANKER in supported else sorted(supported)[0]
            log.warning("reranker_model_unsupported", requested=model_name, fallback=chosen)
            model_name = chosen
        self.model_name = model_name
        self._model = TextCrossEncoder(model_name=model_name)

    def rerank(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
        return [float(s) for s in self._model.rerank(query, documents)]


def build_reranker(settings: Settings | None = None) -> Reranker:
    settings = settings or get_settings()
    return FastEmbedReranker(settings.reranker_model)
