"""
A fake Gemini client used ONLY for local verification of the agent loop
(tool whitelisting, MAX_STEPS, grounding) without a real GEMINI_API_KEY or
network access. Not used by the running application — main.py always uses
the real GeminiClient from services/gemini_service.py.
"""

import json


class FakeGeminiClient:
    """Scripted responses: pass a list of dicts, one per expected call."""

    def __init__(self, scripted_steps):
        self._steps = list(scripted_steps)
        self.calls = 0

    def propose_step(self, message, history, tools_description):
        self.calls += 1
        if not self._steps:
            return {"final_answer": "(fake client ran out of scripted steps)"}
        return self._steps.pop(0)

    def analyze_document(self, content):
        return json.loads(self._steps.pop(0)) if self._steps else {}
