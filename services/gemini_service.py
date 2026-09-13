"""
Thin wrapper around the Gemini API.

Design note: both public methods return a dict/step decision rather than
raw model text, and every call site (routes/ai.py, services/agent_service.py)
only ever sees GeminiClient — never the SDK directly. That makes it possible
to swap in a fake client for tests (see tests/fakes.py) without touching any
network or secrets.
"""

import json
import logging
import re

from settings import settings

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Raised whenever Gemini can't be reached or returns something unusable.

    Never let this exception's message leak an API key or a raw traceback —
    callers turn it into a generic 502 for the client.
    """


def _extract_json(text: str) -> str:
    """Strip ``` fences and grab the first {...} block, in case the model
    wraps its JSON in prose or markdown."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return brace.group(0)
    return text


class GeminiClient:
    """Real Gemini client. Requires GEMINI_API_KEY to be set in the environment."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        self._model = None

    def _get_model(self):
        if self._model is None:
            if not self.api_key:
                raise GeminiError("GEMINI_API_KEY is not configured.")
            import google.generativeai as genai  # imported lazily so the

            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def analyze_document(self, content: str) -> dict:
        """R-T-C-F structured analysis. Returns a dict matching AIAnalysisResponse."""
        prompt = f"""Role: You are a careful document analyst.
Task: Summarize and classify the supplied document.
Context: Use only the provided document content below. Do not invent missing facts.
Format: Return ONLY a valid JSON object (no markdown, no commentary) with exactly
these keys: "summary" (string), "key_points" (array of strings),
"category" (one of "technical", "business", "general"),
"suggested_priority" (integer).

Document content:
\"\"\"{content}\"\"\"
"""
        try:
            response = self._get_model().generate_content(prompt)
            raw_text = response.text
        except GeminiError:
            raise
        except Exception as exc:
            logger.error("Gemini analyze_document call failed: %s", exc)
            raise GeminiError("AI analysis is currently unavailable.") from exc

        try:
            return json.loads(_extract_json(raw_text))
        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            logger.error("Gemini returned non-JSON analysis output: %s", exc)
            raise GeminiError("AI analysis returned an unexpected format.") from exc

    def propose_step(self, message: str, history: list[str], tools_description: str) -> dict:
        """One step of the agent loop. Returns either
        {"tool_call": {"name": ..., "arguments": {...}}} or {"final_answer": "..."}.
        """
        transcript = "\n".join(history) if history else "(no tool calls yet)"
        prompt = f"""Role: You are a read-only document assistant.
Task: Answer the user's question using ONLY the tools below when you need
document data. Never claim to know document contents you have not retrieved
through a tool.
Available tools:
{tools_description}
Context: You have no access to the database except through these tools.
Do not invent document titles, ids, or content.
Format: Reply with ONLY one JSON object and nothing else, either:
{{"tool_call": {{"name": "<tool_name>", "arguments": {{...}}}}}}
or
{{"final_answer": "<your answer, grounded only in tool results>"}}

User question: {message}

Tool call history so far:
{transcript}

Respond with the single JSON object now.
"""
        try:
            response = self._get_model().generate_content(prompt)
            raw_text = response.text
        except GeminiError:
            raise
        except Exception as exc:
            logger.error("Gemini propose_step call failed: %s", exc)
            raise GeminiError("The AI agent is currently unavailable.") from exc

        try:
            return json.loads(_extract_json(raw_text))
        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            logger.error("Gemini returned a non-JSON agent step: %s", exc)
            raise GeminiError("The AI agent returned an unexpected format.") from exc
