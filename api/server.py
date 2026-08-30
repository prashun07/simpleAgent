"""
FastAPI server for the Enterprise Knowledge Assistant.

Run: uvicorn api.server:app --reload

Authentication:
  curl -H "X-API-Key: your-read-key" http://localhost:8000/ask ...
  curl -H "X-API-Key: your-admin-key" -X POST http://localhost:8000/index
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from api.auth import require_admin_key, require_read_key
from assistant.agent import EnterpriseKnowledgeAssistant, AssistantResponse
from config.settings import load_settings
from observability.tracer import setup_logging

_assistant: EnterpriseKnowledgeAssistant | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    setup_logging(settings.log_level)
    yield


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="RAG API with local (Ollama) and cloud (Gemini/Groq) model support",
    version="1.1.0",
    lifespan=lifespan,
)


def get_assistant() -> EnterpriseKnowledgeAssistant:
    global _assistant
    if _assistant is None:
        _assistant = EnterpriseKnowledgeAssistant()
    return _assistant


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["What is our refund policy?"])


class AskResponse(BaseModel):
    answer: str
    citations: list[dict]
    provider_info: dict[str, str]
    trace_id: str | None = None
    retrieval_ms: float | None = None
    generation_ms: float | None = None
    total_ms: float | None = None


class IndexResponse(BaseModel):
    status: str
    files: int
    chunks: int
    message: str
    trace_id: str | None = None


@app.get("/health")
def health():
    """Public health check — no auth required."""
    return {"status": "ok"}


@app.get("/config", dependencies=[Depends(require_read_key)])
def config():
    assistant = get_assistant()
    return assistant.provider_info


@app.post("/index", response_model=IndexResponse, dependencies=[Depends(require_admin_key)])
def index_documents(rebuild: bool = False):
    assistant = get_assistant()
    result = assistant.index(force_rebuild=rebuild)
    return IndexResponse(
        status=str(result.get("status", "unknown")),
        files=int(result.get("files", 0)),
        chunks=int(result.get("chunks", 0)),
        message=str(result.get("message", "")),
        trace_id=str(result.get("trace_id", "")) or None,
    )


@app.post("/ask", response_model=AskResponse, dependencies=[Depends(require_read_key)])
def ask(request: AskRequest):
    try:
        assistant = get_assistant()
        response: AssistantResponse = assistant.ask(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AskResponse(
        answer=response.answer,
        citations=[
            {"source": c.source, "excerpt": c.excerpt, "score": c.score}
            for c in response.citations
        ],
        provider_info=response.provider_info,
        trace_id=response.trace_id,
        retrieval_ms=response.retrieval_ms,
        generation_ms=response.generation_ms,
        total_ms=response.total_ms,
    )
