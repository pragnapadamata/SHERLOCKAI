"""Draft the prose documents once with the LLM, then freeze them.

Each prose document (manuals, SOPs, failure reports) is drafted by the large-tier
model from a spec slice. Cross-references use a strict ``[[TYPE:id]]`` grammar:
the model is given the exact set of fully-wrapped tokens it may use (a whitelist)
and the subset it must include, and is forbidden from writing any other token.
After drafting, the document is checked; if a required reference is missing or an
unknown token slipped in, it is re-drafted with corrective feedback.

The fault catalog is tabular, not prose, so it is rendered programmatically from
the spec (guaranteeing every fault reference resolves).

Because LLM inference is not reliably byte-deterministic, the prose documents are
NOT part of the reproducibility gate: they are generated once, validated,
committed, and skipped on later runs unless ``force=True``. Their correctness
gate is validate_coherence.py.
"""

from __future__ import annotations

import json
import re

from backend.app.llm.messages import Message
from backend.app.llm.tiers import LLMRegistry
from backend.scripts.data_substrate import round1, spec

TOKEN_RE = re.compile(r"\[\[([A-Z]+:[^\]]+)\]\]")
MAX_ATTEMPTS = 4

SYSTEM_PROMPT = (
    "You are a senior reliability engineer writing internal maintenance "
    "documentation for a steel Hot Strip Mill, as a prototype for the Tata Steel "
    "AI Hackathon. Write in plain engineering English. Output GitHub-flavored "
    "Markdown for the BODY of the document only: do not repeat the document title "
    "and do not write any banner line (those are added separately).\n\n"
    "Structure rules:\n"
    "- Use exactly the second-level (##) section headings in `required_sections`, "
    "in the given order.\n"
    "- Keep the document concise (roughly 300-700 words).\n"
    "- Do not fabricate numeric specifications beyond those in the context; you may "
    "add qualitative engineering detail.\n\n"
    "Cross-reference rules (strict):\n"
    "- A reference token looks EXACTLY like [[ASSET:HSM-F3-GBX]] or "
    "[[FAULT:F3-GBX-002]] -- an uppercase type, a colon, then a real id.\n"
    "- Include every string in `required_references` verbatim, at least once, in a "
    "natural place.\n"
    "- You may additionally use tokens from `allowed_references`, copied verbatim.\n"
    "- NEVER write a [[...]] token that is not in those two lists. In particular "
    "never write descriptive tokens such as [[FAULT:fault code]] or "
    "[[ASSET:equipment]], and never double a prefix such as "
    "[[FAULT:FAULT:F3-GBX-002]]. When unsure, write plain text instead of a token.\n"
    "- If `must_cite_coil_ids` is present, mention at least three of those Coil IDs "
    "verbatim as plain text (they are data values, not reference tokens)."
)


def _allowed_tokens(doc: spec.DocSpec) -> list[str]:
    tokens: set[str] = set()
    if doc.equipment_id:
        tokens.add(f"[[ASSET:{doc.equipment_id}]]")
        if doc.doc_type is spec.DocType.MANUAL:
            tokens.add(f"[[MANUAL:{doc.equipment_id}]]")
    for code in doc.context_faults:
        tokens.add(f"[[FAULT:{code}]]")
    for sop in doc.context_sops:
        tokens.add(f"[[SOP:{sop}]]")
    for part in doc.context_spares:
        tokens.add(f"[[PART:{part}]]")
    if doc.doc_type is spec.DocType.SOP:
        tokens.add(f"[[SOP:{doc.doc_id}]]")
    if doc.doc_type is spec.DocType.FAILURE_REPORT:
        tokens.add(f"[[FR:{doc.doc_id}]]")
    for ref in doc.required_refs:
        tokens.add(f"[[{ref}]]")
    return sorted(tokens)


def _build_context(doc: spec.DocSpec) -> dict:
    ctx: dict = {
        "document_id": doc.doc_id,
        "title": doc.title,
        "type": doc.doc_type.value,
        "required_sections": doc.required_sections,
        "required_references": [f"[[{r}]]" for r in doc.required_refs],
        "allowed_references": _allowed_tokens(doc),
    }
    if doc.equipment_id:
        ctx["asset"] = spec.ASSETS_BY_ID[doc.equipment_id].model_dump(mode="json")
    if doc.context_faults:
        ctx["fault_codes"] = [
            spec.FAULTS_BY_CODE[c].model_dump(mode="json") for c in doc.context_faults
        ]
    if doc.context_sops:
        ctx["sops"] = [{"id": s, "title": spec.DOCS_BY_ID[s].title} for s in doc.context_sops]
    if doc.context_spares:
        ctx["spare_parts"] = [
            spec.SPARES_BY_ID[p].model_dump(mode="json") for p in doc.context_spares
        ]
    if doc.extra_brief:
        ctx["brief"] = doc.extra_brief
    if doc.inject_positive_coils:
        ctx["must_cite_coil_ids"] = round1.positive_coil_ids(6)
    return ctx


def _check(doc: spec.DocSpec, full_text: str) -> list[str]:
    """Return a list of coherence problems for a drafted document (empty == ok)."""

    problems: list[str] = []
    for ref in doc.required_refs:
        if f"[[{ref}]]" not in full_text:
            problems.append(f"missing required reference [[{ref}]]")
    for token in TOKEN_RE.findall(full_text):
        if not spec.resolve_reference(token):
            problems.append(f"unresolved reference [[{token}]]")
    for heading in doc.required_sections:
        if f"## {heading}" not in full_text:
            problems.append(f"missing section heading '## {heading}'")
    if doc.inject_positive_coils:
        coil_ids = round1.positive_coil_ids(6)
        present = [c for c in coil_ids if c in full_text]
        if len(present) < 3:
            problems.append(
                f"must cite at least 3 defect-positive Coil IDs from {coil_ids}; found {present}"
            )
    return problems


def _draft_body(llm, context: dict, correction: str | None) -> str:
    user = (
        "Document context (JSON):\n```json\n"
        + json.dumps(context, indent=2)
        + "\n```\n\nWrite the document body now."
    )
    if correction:
        user += "\n\n" + correction
    result = llm.chat(
        [Message(role="system", content=SYSTEM_PROMPT), Message(role="user", content=user)],
        temperature=0.0,
        max_tokens=2400,
    )
    return (result.content or "").strip()


def _compose(doc: spec.DocSpec, body: str) -> str:
    return f"{spec.PROTOTYPE_HEADER}\n\n# {doc.title}\n\n{body}\n"


def render_fault_catalog() -> str:
    """Render the fault catalog document programmatically from the spec."""

    doc = spec.DOCS_BY_ID["fault_codes"]
    lines = [
        spec.PROTOTYPE_HEADER, "", f"# {doc.title}", "",
        "## Overview", "",
        "This catalog lists every fault/error code in the prototype, with its "
        "meaning, likely cause, recommended action, and cross-links to the relevant "
        "equipment, standard operating procedures, and spare parts. It mirrors "
        "`data/raw/structured/fault_catalog.csv`.", "",
        "## Catalog", "",
    ]
    for f in spec.FAULTS:
        sops = ", ".join(f"[[SOP:{s}]]" for s in f.related_sops) or "none"
        spares = ", ".join(f"[[PART:{p}]]" for p in f.related_spares) or "none"
        lines += [
            f"### [[FAULT:{f.fault_code}]] - {f.title}", "",
            f"- Equipment: [[ASSET:{f.equipment_id}]]",
            f"- Severity: {f.severity.value}",
            f"- Meaning: {f.meaning}",
            f"- Likely cause: {f.likely_cause}",
            f"- Recommended action: {f.recommended_action}",
            f"- Related SOPs: {sops}",
            f"- Related spares: {spares}", "",
        ]
    text = "\n".join(lines) + "\n"
    out_path = spec.RAW_DOCS / doc.rel_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    return "rendered"


def generate_all(force: bool = False) -> dict[str, str]:
    """Draft every prose document. Returns {doc_id: status}: ok|skipped|FAILED."""

    llm = LLMRegistry().get("large")
    statuses: dict[str, str] = {}

    for doc in spec.DOCS:
        if doc.doc_type is spec.DocType.FAULT_CATALOG:
            continue  # rendered programmatically by render_fault_catalog()

        out_path = spec.RAW_DOCS / doc.rel_path
        if out_path.exists() and not force:
            statuses[doc.doc_id] = "skipped"
            continue

        context = _build_context(doc)
        correction: str | None = None
        problems: list[str] = []
        full_text = ""
        for _ in range(MAX_ATTEMPTS):
            body = _draft_body(llm, context, correction)
            full_text = _compose(doc, body)
            problems = _check(doc, full_text)
            if not problems:
                break
            correction = (
                "The previous attempt had these problems; fix them and keep "
                "everything else correct: " + "; ".join(problems)
            )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(full_text)
        statuses[doc.doc_id] = "ok" if not problems else "FAILED: " + "; ".join(problems)

    return statuses


if __name__ == "__main__":
    print(f"fault_codes (programmatic): {render_fault_catalog()}")
    for doc_id, status in generate_all().items():
        print(f"{doc_id}: {status}")
