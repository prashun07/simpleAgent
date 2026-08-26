"""
FastAPI server for the Enterprise Knowledge Assistant.

Run: uvicorn api.server:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from assistant.agent import EnterpriseKnowledgeAssistant, AssistantResponse

app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="RAG API with local (Ollama) and cloud (Gemini/Groq) model support",
    version="1.0.0",
)

_assistant: EnterpriseKnowledgeAssistant | None = None


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


class IndexResponse(BaseModel):
    status: str
    files: int
    chunks: int
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    assistant = get_assistant()
    return assistant.provider_info


@app.post("/index", response_model=IndexResponse)
def index_documents(rebuild: bool = False):
    assistant = get_assistant()
    result = assistant.index(force_rebuild=rebuild)
    return IndexResponse(
        status=str(result.get("status", "unknown")),
        files=int(result.get("files", 0)),
        chunks=int(result.get("chunks", 0)),
        message=str(result.get("message", "")),
    )


@app.post("/ask", response_model=AskResponse)
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
    )
