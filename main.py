from fastapi import FastAPI

from routes.ai import router as ai_router
from routes.documents import router as documents_router

app = FastAPI(
    title="SmartDoc AI",
    description=(
        "Documents API (Lecture 4/5 foundation) with Gemini-powered structured "
        "analysis and a read-only, whitelisted tool-calling agent."
    ),
    version="1.0.0",
)


@app.get("/health", tags=["health"], summary="Service health check")
def health():
    return {"status": "ok"}


app.include_router(documents_router)
app.include_router(ai_router)
