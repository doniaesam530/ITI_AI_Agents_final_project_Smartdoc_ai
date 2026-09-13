from pydantic import BaseModel, ConfigDict, Field


# ---------- Documents ----------

class DocumentBase(BaseModel):
    title: str
    content: str
    description: str | None = None
    priority: int | None = 1


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    ai_summary: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------- AI analysis (Phase 4) ----------

class AIAnalysisResponse(BaseModel):
    summary: str
    key_points: list[str]
    category: str = Field(description="technical | business | general")
    suggested_priority: int


# ---------- Agent (Phase 5) ----------

class AgentAskRequest(BaseModel):
    message: str


class AgentAskResponse(BaseModel):
    answer: str
    steps_used: int
