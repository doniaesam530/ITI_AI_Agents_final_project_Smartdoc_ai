# Phase 6 — AI-Assisted Development Review

## Scoped change
Add `POST /documents/{document_id}/analyze` to `routes/ai.py`.

## Prompt used
```
In routes/ai.py, add POST /documents/{document_id}/analyze.
Reuse the existing Document model and Session(engine) pattern.
Return 404 when the document is missing.
Do not change the existing CRUD routes.
Keep the response compatible with AIAnalysisResponse.
```

## Generated diff (as first proposed)
```diff
+@router.post("/documents/{document_id}/analyze")
+def analyze_document(document_id: int):
+    with Session(engine) as db:
+        document = db.get(Document, document_id)
+        client = GeminiClient(api_key="AIzaSy...HARDCODED...")
+        data = client.analyze_document(document.content)
+        document.ai_summary = data["summary"]
+        db.commit()
+        return data
```

## Manual review — what I checked and corrected

1. **Hardcoded API key.** The first draft hardcoded a Gemini API key
   directly in the route. Corrected to always construct `GeminiClient()`
   with no arguments, so it reads `GEMINI_API_KEY` from `.env` via
   `settings.py` — never from source.
2. **Missing 404 handling.** The draft called `document.content` without
   checking whether `db.get()` returned `None` first, which would have
   raised an `AttributeError` (and leaked a 500/traceback) instead of a
   clean 404. Added the explicit `if document is None: raise
   HTTPException(404, ...)` check before touching the document.
3. **No status code / response model.** The draft had no explicit
   `response_model`, so a malformed Gemini reply could have silently
   returned the wrong shape. Added `response_model=AIAnalysisResponse` and
   wrapped the Gemini call in `try/except GeminiError` to turn any AI
   failure into a controlled `502` instead of a raw exception reaching
   the client.
4. **Wrong field saved.** The draft returned Gemini's whole raw dict as
   the response, but the spec only requires *saving* `summary` into
   `Document.ai_summary` while returning the full structured analysis.
   Confirmed the final code does both correctly.
