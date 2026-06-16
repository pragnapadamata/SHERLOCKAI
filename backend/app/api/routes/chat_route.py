from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import io
import os
import pypdf
import httpx
import json
from app.agents.multi_agent import run_multi_agent


def _derive_confidence(*, grounded: bool, specialists: list, stop_reason: str) -> float:
    """Honest confidence derived from the wizard run, not a hardcoded constant."""
    if stop_reason == "llm_error":
        return 0.55
    base = 0.78
    if grounded:
        base += 0.12
    if specialists and "reporting" in specialists:
        base += 0.05
    if stop_reason == "max_iters":
        base -= 0.10
    return round(min(0.96, max(0.40, base)), 2)


def _derive_impact(findings: list) -> str:
    """Build the 'Expected Impact' line from the specialists' actual key facts."""
    severities: list[str] = []
    rul = None
    for f in findings or []:
        if not isinstance(f, dict):
            continue
        kf = f.get("key_facts") or {}
        sev = str(kf.get("severity") or "").lower()
        if sev:
            severities.append(sev)
        for k in ("rul_weeks", "rul", "remaining_useful_life_weeks"):
            if kf.get(k) is not None:
                rul = kf.get(k)
    if "critical" in severities:
        return ("Critical condition flagged — acting now prevents an imminent unplanned "
                "failure and the associated production loss.")
    if "high" in severities:
        return ("High-severity degradation — planned intervention avoids escalation to an "
                "unplanned breakdown.")
    if rul is not None:
        return (f"Predicted remaining useful life ≈ {rul} weeks — schedule the repair within "
                "that window to avoid unplanned downtime.")
    return ("Grounded predictive diagnosis enables planned intervention before failure, "
            "reducing unplanned downtime.")


def extract_cells(row: str) -> list[str]:
    r = row.strip()
    if r.startswith('|'):
        r = r[1:]
    if r.endswith('|'):
        r = r[:-1]
    return [cell.strip() for cell in r.split('|')]

def parse_separator(sep_row: str) -> list[str]:
    cells = extract_cells(sep_row)
    aligns = []
    for cell in cells:
        c = cell.strip()
        if c.startswith(':') and c.endswith(':'):
            aligns.append('center')
        elif c.endswith(':'):
            aligns.append('right')
        else:
            aligns.append('left')
    return aligns

def wrap_text(text: str, width: int) -> list[str]:
    if not text:
        return [""]
    if len(text) <= width:
        return [text]
        
    words = text.split(' ')
    lines = []
    current_line = []
    current_len = 0
    
    for word in words:
        if len(word) > width:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = []
                current_len = 0
            for k in range(0, len(word), width):
                lines.append(word[k:k+width])
            continue
            
        space_len = 1 if current_line else 0
        if current_len + len(word) + space_len <= width:
            current_line.append(word)
            current_len += len(word) + space_len
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_len = len(word)
            
    if current_line:
        lines.append(' '.join(current_line))
        
    return lines if lines else [""]

def allocate_column_widths(num_cols: int, max_content_widths: list[int]) -> list[int]:
    if num_cols <= 1:
        limits = [80]
    elif num_cols == 2:
        limits = [35, 45]
    elif num_cols == 3:
        limits = [20, 30, 35]
    elif num_cols == 4:
        limits = [15, 25, 35, 12]
    else:
        limits = [12, 18, 25, 18, 12] + [12] * (num_cols - 5)
        
    if len(limits) < num_cols:
        limits += [15] * (num_cols - len(limits))
        
    widths = []
    for j in range(num_cols):
        w = min(max_content_widths[j], limits[j])
        widths.append(max(w, 1))
    return widths

def format_table(header_row: str, sep_row: str, data_rows: list[str]) -> str:
    headers = extract_cells(header_row)
    alignments = parse_separator(sep_row)
    
    if len(alignments) < len(headers):
        alignments += ['left'] * (len(headers) - len(alignments))
    else:
        alignments = alignments[:len(headers)]
        
    num_cols = len(headers)
    
    cleaned_data_rows = []
    for row in data_rows:
        cells = extract_cells(row)
        if len(cells) < num_cols:
            cells += [''] * (num_cols - len(cells))
        else:
            cells = cells[:num_cols]
        cleaned_cells = [cell.replace('*', '').replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ').strip() for cell in cells]
        cleaned_data_rows.append(cleaned_cells)
        
    cleaned_headers = [h.replace('*', '').strip() for h in headers]
    
    max_content_widths = [0] * num_cols
    for j in range(num_cols):
        max_content_widths[j] = len(cleaned_headers[j])
        for row in cleaned_data_rows:
            max_content_widths[j] = max(max_content_widths[j], len(row[j]))
            
    col_widths = allocate_column_widths(num_cols, max_content_widths)
        
    def format_cell(text: str, width: int, align: str) -> str:
        if align == 'right':
            return text.rjust(width)
        elif align == 'center':
            return text.center(width)
        else:
            return text.ljust(width)
            
    lines = []
    top_border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
    lines.append(top_border)
    
    wrapped_headers = [wrap_text(cleaned_headers[j], col_widths[j]) for j in range(num_cols)]
    header_lines_cnt = max(len(col_lines) for col_lines in wrapped_headers)
    for j in range(num_cols):
        if len(wrapped_headers[j]) < header_lines_cnt:
            wrapped_headers[j] += [""] * (header_lines_cnt - len(wrapped_headers[j]))
            
    for line_idx in range(header_lines_cnt):
        header_cells = [f" {format_cell(wrapped_headers[j][line_idx], col_widths[j], alignments[j])} " for j in range(num_cols)]
        lines.append("│" + "│".join(header_cells) + "│")
    
    header_sep = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
    lines.append(header_sep)
    
    for row in cleaned_data_rows:
        wrapped_row = [wrap_text(row[j], col_widths[j]) for j in range(num_cols)]
        row_lines_cnt = max(len(col_lines) for col_lines in wrapped_row)
        for j in range(num_cols):
            if len(wrapped_row[j]) < row_lines_cnt:
                wrapped_row[j] += [""] * (row_lines_cnt - len(wrapped_row[j]))
                
        for line_idx in range(row_lines_cnt):
            data_cells = [f" {format_cell(wrapped_row[j][line_idx], col_widths[j], alignments[j])} " for j in range(num_cols)]
            lines.append("│" + "│".join(data_cells) + "│")
        
    bottom_border = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"
    lines.append(bottom_border)
    
    return "\n".join(lines)

def is_separator_line(line: str) -> bool:
    stripped = line.strip()
    return '|' in line and '-' in line and set(stripped) <= {'|', '-', ':', ' '}

def parse_and_replace_tables(text: str) -> str:
    lines = text.splitlines()
    num_lines = len(lines)
    
    new_lines = []
    i = 0
    while i < num_lines:
        line = lines[i]
        if i > 0 and is_separator_line(line):
            header = lines[i - 1]
            separator = line
            data_rows = []
            
            j = i + 1
            while j < num_lines:
                next_line = lines[j]
                if '|' in next_line and not is_separator_line(next_line):
                    data_rows.append(next_line)
                    j += 1
                else:
                    break
            
            unicode_table = format_table(header, separator, data_rows)
            
            if new_lines:
                new_lines.pop()  # Remove header
                
            new_lines.extend(unicode_table.splitlines())
            i = j
        else:
            new_lines.append(line)
            i += 1
            
    return "\n".join(new_lines)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    plant_id: Optional[str] = "ALL"
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    agent: str
    response: str
    confidence: float
    reasoning: str
    impact: str
    routing_scores: dict


SUGGESTED_QUERIES = [
    "Analyze gearbox vibration trend for wear prediction.",
    "Identify safety risks on Blast Furnace Hearth #2.",
    "Generate energy efficiency recommendations.",
]


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(request: ChatRequest):
    """Process a chat message through the multi-agent system, calling the maintenance-wizard service."""
    # Build context-aware query
    query = request.message
    if request.plant_id and request.plant_id != "ALL":
        if request.plant_id.lower() not in query.lower():
            query = f"{query} [Context: {request.plant_id}]"

    # Try communicating with maintenance-wizard assistant backend
    import os
    url = os.getenv("MAINTENANCE_WIZARD_URL", "http://127.0.0.1:8002/api/chat")
    session_id = f"chat-sherlock-{request.plant_id}"
    payload = {"query": query, "session_id": session_id}

    agent = "MAINTENANCE"
    response = ""
    confidence = 0.95
    reasoning = "Orchestrated maintenance specialists through the Maintenance Wizard engine."
    impact = "Predictive, grounded diagnosis enables planned intervention before failure."
    routing_scores = {"MAINTENANCE": 1, "SAFETY": 0, "ENERGY": 0, "PRODUCTION": 0, "REPORTING": 0}
    success = False
    stream_error: Optional[str] = None

    try:
        # The timeout matches the wizard's own LLM budget (LLM_REQUEST_TIMEOUT=180s) plus
        # headroom for a full multi-specialist run, so a good live answer is never cut off
        # at 45s and silently replaced by the weaker local fallback.
        timeout = httpx.Timeout(210.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code == 200:
                    current_event_type = None
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("event:"):
                            current_event_type = line.split("event:", 1)[1].strip()
                        elif line.startswith("data:"):
                            data_json = line.split("data:", 1)[1].strip()
                            if current_event_type == "final":
                                try:
                                    data = json.loads(data_json)
                                except json.JSONDecodeError:
                                    continue
                                response = (data.get("answer") or "").strip()
                                specialists = data.get("specialists_used", []) or []
                                provenance = data.get("provenance", []) or []
                                findings = data.get("findings", []) or []
                                iterations = int(data.get("iterations") or 0)
                                stop_reason = data.get("stop_reason", "completed")

                                # Real, derived metadata instead of a hardcoded 0.95.
                                if specialists:
                                    pretty = " → ".join(s.replace("_", " ") for s in specialists)
                                    reasoning = (
                                        f"Planned and delegated to {len(specialists)} specialist "
                                        f"step(s): {pretty}. {iterations} reasoning iteration(s); "
                                        f"{len(provenance)} grounded source(s) cited."
                                    )
                                impact = _derive_impact(findings)
                                confidence = _derive_confidence(
                                    grounded=bool(provenance), specialists=specialists,
                                    stop_reason=stop_reason,
                                )
                                if response:
                                    success = True
                                break
                            elif current_event_type == "error":
                                try:
                                    stream_error = json.loads(data_json).get("message")
                                except json.JSONDecodeError:
                                    stream_error = data_json
                                break
                else:
                    stream_error = f"wizard returned HTTP {resp.status_code}"
    except Exception as exc:
        # Network/timeout: degrade to the local orchestrator below.
        stream_error = str(exc)

    if not success:
        result = run_multi_agent(query=query, plant_id=request.plant_id)
        agent = result["agent"]
        response = result["response"]
        confidence = result["confidence"]
        reasoning = result["reasoning"]
        impact = result["impact"]
        routing_scores = result["routing_scores"]

    # Let raw markdown tables pass through so the Next.js frontend can parse and render them natively
    # if response:
    #     response = parse_and_replace_tables(response)

    return ChatResponse(
        agent=agent,
        response=response,
        confidence=confidence,
        reasoning=reasoning,
        impact=impact,
        routing_scores=routing_scores,
    )


@router.get("/suggestions")
async def get_suggested_queries():
    """Return suggested queries for the chat interface."""
    return {"suggestions": SUGGESTED_QUERIES}


@router.get("/agents")
async def get_agent_descriptions():
    """Return information about available agents."""
    return {
        "agents": [
            {
                "id": "SUPERVISOR",
                "name": "Sherlock Lead Orchestrator",
                "description": "Orchestrates all specialists and routes queries intelligently",
                "color": "#6366f1",
            },
            {
                "id": "MAINTENANCE",
                "name": "Predictive Reliability Specialist",
                "description": "Predictive failure analysis and machine reliability scheduling",
                "color": "#f59e0b",
            },
            {
                "id": "SAFETY",
                "name": "HSE Risk Analyst",
                "description": "Incident monitoring, risk scoring, and preventive compliance actions",
                "color": "#ef4444",
            },
            {
                "id": "ENERGY",
                "name": "Energy Systems Optimizer",
                "description": "Consumption analysis and energy optimization recommendations",
                "color": "#10b981",
            },
            {
                "id": "PRODUCTION",
                "name": "Operations Flow Engineer",
                "description": "Operations scheduling and production optimization analysis",
                "color": "#3b82f6",
            },
            {
                "id": "REPORTING",
                "name": "Executive Systems Reporter",
                "description": "Executive summaries and comprehensive reports",
                "color": "#8b5cf6",
            },
        ]
    }


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and extract text context from a PDF, TXT, or doc/docx document."""
    content_type = file.content_type
    filename = file.filename or ""
    
    try:
        contents = await file.read()
        
        if filename.endswith(".pdf") or content_type == "application/pdf":
            # Extract PDF text using pypdf
            pdf_file = io.BytesIO(contents)
            reader = pypdf.PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            extracted_text = "\n".join(text_parts)
            if not extracted_text.strip():
                raise HTTPException(status_code=400, detail="PDF is empty or has no readable text")
            return {
                "filename": filename,
                "text": extracted_text,
                "length": len(extracted_text),
                "summary": f"Extracted {len(reader.pages)} pages of text from PDF."
            }
            
        elif filename.endswith(".txt") or content_type.startswith("text/"):
            text = contents.decode("utf-8", errors="ignore")
            return {
                "filename": filename,
                "text": text,
                "length": len(text),
                "summary": "Extracted text file content."
            }
            
        elif filename.endswith((".doc", ".docx")):
            # Basic fallback text recovery
            text = contents.decode("utf-8", errors="ignore")
            text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")
            return {
                "filename": filename,
                "text": text[:5000],
                "length": len(text),
                "summary": "Extracted doc/docx content."
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(exc)}")
