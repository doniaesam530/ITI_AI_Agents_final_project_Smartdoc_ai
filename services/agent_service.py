"""
Read-only, tool-calling document agent.

Architecture (per Lab 6 spec):
    User -> /agent/ask -> this service -> Gemini proposes a tool call
    -> Python validates + executes the whitelisted tool -> result fed back
    to Gemini -> repeat until Gemini returns a final answer, or MAX_STEPS
    is reached.

Gemini NEVER executes anything itself. It only ever returns text that this
module parses, validates, and — only if the tool name is whitelisted —
turns into a real function call.
"""

import logging

from sqlalchemy.orm import Session

from database import engine
from models import Document
from services.gemini_service import GeminiClient, GeminiError

logger = logging.getLogger(__name__)

MAX_STEPS = 5


# ---------------------------------------------------------------------
# Whitelisted, read-only tools. Each takes a dict of arguments (already
# parsed from Gemini's proposed JSON) and returns plain dict/list data —
# never a SQLAlchemy object, never a raw exception.
# ---------------------------------------------------------------------

def list_documents_tool(_arguments: dict) -> list[dict]:
    with Session(engine) as db:
        docs = db.query(Document).all()
        return [{"id": d.id, "title": d.title, "priority": d.priority} for d in docs]


def get_document_tool(arguments: dict) -> dict:
    document_id = arguments.get("document_id")
    if not isinstance(document_id, int) or document_id <= 0:
        raise ValueError("document_id must be a positive integer")

    with Session(engine) as db:
        doc = db.get(Document, document_id)
        if doc is None:
            return {"found": False}
        return {
            "found": True,
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "description": doc.description,
            "priority": doc.priority,
            "ai_summary": doc.ai_summary,
        }


def search_documents_tool(arguments: dict) -> list[dict]:
    query = arguments.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")

    like = f"%{query.strip()}%"
    with Session(engine) as db:
        docs = (
            db.query(Document)
            .filter((Document.title.ilike(like)) | (Document.content.ilike(like)))
            .all()
        )
        return [{"id": d.id, "title": d.title} for d in docs]


TOOLS = {
    "list_documents": list_documents_tool,
    "get_document": get_document_tool,
    "search_documents": search_documents_tool,
}

TOOLS_DESCRIPTION = (
    "- list_documents(): no arguments. Returns id, title, priority for every document.\n"
    "- get_document(document_id: int > 0): returns full fields for one document, "
    "or {\"found\": false} if it doesn't exist.\n"
    "- search_documents(query: str): returns id/title of documents whose title "
    "or content matches the query."
)


def run_agent(message: str, gemini_client: "GeminiClient | None" = None) -> tuple[str, int]:
    """Runs the agent loop and returns (final_answer, steps_used)."""
    client = gemini_client or GeminiClient()
    history: list[str] = []

    for step in range(1, MAX_STEPS + 1):
        try:
            decision = client.propose_step(message, history, TOOLS_DESCRIPTION)
        except GeminiError as exc:
            logger.error("agent step=%s gemini_error=%s", step, exc)
            return "Sorry, the AI agent is temporarily unavailable.", step

        if "final_answer" in decision:
            logger.info("agent step=%s result=final_answer", step)
            return str(decision["final_answer"]), step

        tool_call = decision.get("tool_call") or {}
        name = tool_call.get("name")
        arguments = tool_call.get("arguments") or {}

        if name not in TOOLS:
            logger.warning("agent step=%s tool=%s result=rejected_not_whitelisted", step, name)
            observation = {"error": "That action isn't available to this agent."}
        else:
            try:
                result = TOOLS[name](arguments)
                observation = {"result": result}
                logger.info("agent step=%s tool=%s result=success", step, name)
            except Exception as exc:
                # Never leak the raw exception (could contain SQL/db internals).
                logger.warning("agent step=%s tool=%s result=failed error=%s", step, name, exc)
                observation = {"error": "That tool call failed."}

        history.append(f"tool_call: {name}({arguments})")
        history.append(f"tool_observation: {observation}")

    logger.warning("agent reached MAX_STEPS=%s without a final answer", MAX_STEPS)
    return "I couldn't find a grounded answer within the allowed number of steps.", MAX_STEPS
