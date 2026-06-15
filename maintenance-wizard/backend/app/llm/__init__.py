"""Provider-agnostic, tiered LLM client.

Public surface for the rest of the app. Submodules import each other by full
path (never from this package) to keep import order acyclic.
"""

from __future__ import annotations

from backend.app.llm.base import LLMClient
from backend.app.llm.messages import (
    ChatResult,
    Message,
    Provenance,
    ToolCall,
    ToolSpec,
)
from backend.app.llm.providers import build_client, get_provider_class
from backend.app.llm.tiers import LLMRegistry, get_llm_registry

__all__ = [
    "LLMClient",
    "Message",
    "ToolSpec",
    "ToolCall",
    "ChatResult",
    "Provenance",
    "build_client",
    "get_provider_class",
    "LLMRegistry",
    "get_llm_registry",
]
