from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from database import engine
from models import Document
from schemas import AgentAskRequest, AgentAskResponse, AIAnalysisResponse
from services.agent_service import run_agent
from services.gemini_service import GeminiClient, GeminiError

router = APIRouter(tags=["ai"])


@router.post(
    "/documents/{document_id}/analyze",
    response_model=AIAnalysisResponse,
    summary="Generate a structured Gemini analysis of a document",
    responses={
        404: {"description": "Document not found"},
        502: {"description": "AI analysis failed"},
    },
)
def analyze_document(document_id: int):
    with Session(engine) as db:
        document = db.get(Document, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")

        client = GeminiClient()
        try:
            data = client.analyze_document(document.content)
        except GeminiError as exc:
            # Controlled application error — never expose the raw traceback.
            raise HTTPException(status_code=502, detail=str(exc))

        document.ai_summary = data.get("summary")
        db.commit()

        return AIAnalysisResponse(**data)


@router.post(
    "/agent/ask",
    response_model=AgentAskResponse,
    summary="Ask the read-only document agent a question",
)
def agent_ask(payload: AgentAskRequest):
    answer, steps_used = run_agent(payload.message)
    return AgentAskResponse(answer=answer, steps_used=steps_used)
