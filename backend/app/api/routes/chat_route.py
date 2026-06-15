from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import io
import pypdf
from app.agents.multi_agent import run_multi_agent

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
    """Process a chat message through the multi-agent system."""
    # Build context-aware query
    query = request.message
    if request.plant_id and request.plant_id != "ALL":
        if request.plant_id.lower() not in query.lower():
            query = f"{query} [Context: {request.plant_id}]"

    result = run_multi_agent(query=query, plant_id=request.plant_id)

    return ChatResponse(
        agent=result["agent"],
        response=result["response"],
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        impact=result["impact"],
        routing_scores=result["routing_scores"],
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
