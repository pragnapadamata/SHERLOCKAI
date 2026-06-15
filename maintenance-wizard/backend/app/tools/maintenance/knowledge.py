"""search_knowledge -- reranked passages from the document KB, with citations."""

from __future__ import annotations

from typing import Any, ClassVar

from backend.app.retrieval.retriever import KnowledgeRetriever
from backend.app.tools.results import DataTool, ExpectedToolError, SourceRef, ToolResult

_DOC_TYPES = ["manual", "sop", "failure_report", "fault_catalog"]


class SearchKnowledgeTool(DataTool):
    name: ClassVar[str] = "search_knowledge"
    description: ClassVar[str] = (
        "Search equipment manuals, SOPs, failure reports, and the fault catalog. "
        "Returns reranked passages with document citations (doc id + section). "
        "Optionally scope to one equipment_id or one doc_type."
    )
    parameters: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural-language search query."},
            "equipment_id": {"type": "string", "description": "Scope to one asset (plus shared SOPs)."},
            "doc_type": {"type": "string", "enum": _DOC_TYPES, "description": "Restrict to a document type."},
            "top_n": {"type": "integer", "description": "Number of passages to return."},
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def __init__(self, retriever: KnowledgeRetriever) -> None:
        self._retriever = retriever

    def execute(self, query: str, equipment_id: str | None = None,
                doc_type: str | None = None, top_n: int | None = None) -> ToolResult:
        if doc_type is not None and doc_type not in _DOC_TYPES:
            raise ExpectedToolError(f"Unknown doc_type {doc_type!r}; expected one of {_DOC_TYPES}.")

        results = self._retriever.search(
            query, equipment_id=equipment_id, doc_type=doc_type, top_n=top_n
        )
        if not results:
            scope = f" for equipment {equipment_id}" if equipment_id else ""
            raise ExpectedToolError(f"No knowledge passages found for {query!r}{scope}.")

        data = [
            {
                "text": r.chunk.text,
                "doc_id": r.chunk.doc_id,
                "doc_type": r.chunk.doc_type,
                "section": r.chunk.section,
                "equipment_id": r.chunk.equipment_id,
                "source": r.chunk.source,
                "score": round(r.score, 4),
                "refs": r.chunk.refs,
            }
            for r in results
        ]
        sources = [
            SourceRef.document(
                doc_id=r.chunk.doc_id, source=r.chunk.source, section=r.chunk.section,
                equipment_id=r.chunk.equipment_id, doc_type=r.chunk.doc_type,
                score=round(r.score, 4),
            )
            for r in results
        ]
        top = data[0]
        summary = f"{len(data)} passage(s); top: {top['doc_id']} / {top['section']}"
        return ToolResult(tool=self.name, data=data, sources=sources, summary=summary)
