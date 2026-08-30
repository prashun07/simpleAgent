"""
Enterprise Knowledge Assistant — RAG agent with citations.

Supports local (Ollama) and cloud (Gemini, Groq) open-source-friendly models.
"""

import time
from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel

from config.providers import describe_active_models, get_embeddings, get_llm
from config.settings import Settings, load_settings, validate_settings
from knowledge.indexer import KnowledgeIndexer
from observability.tracer import ChunkTrace, RequestTrace, Timer, log_trace, new_trace_id


RAG_PROMPT = """You are an Enterprise Knowledge Assistant for a company knowledge base.
Answer the user's question using ONLY the context below.

Rules:
- If the context does not contain enough information, say so clearly.
- Be concise and professional.
- Do not invent facts not present in the context.

--- CONTEXT ---
{context}
--- END CONTEXT ---

Question: {question}

Answer:"""


@dataclass
class Citation:
    source: str
    excerpt: str
    score: float | None = None


@dataclass
class AssistantResponse:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    provider_info: dict[str, str] = field(default_factory=dict)
    trace_id: str | None = None
    retrieval_ms: float | None = None
    generation_ms: float | None = None
    total_ms: float | None = None

    def format(self) -> str:
        """Human-readable answer with numbered sources."""
        lines = [self.answer, ""]
        if self.citations:
            lines.append("Sources:")
            for i, cite in enumerate(self.citations, start=1):
                score = f" (relevance: {cite.score:.2f})" if cite.score is not None else ""
                lines.append(f"  [{i}] {cite.source}{score}")
                lines.append(f"      \"{cite.excerpt[:120]}...\"")
        if self.trace_id:
            retrieval = f"{self.retrieval_ms:.0f}ms" if self.retrieval_ms is not None else "n/a"
            generation = f"{self.generation_ms:.0f}ms" if self.generation_ms is not None else "n/a"
            lines.append(f"\n[trace: {self.trace_id} | retrieval: {retrieval} | generation: {generation}]")
        return "\n".join(lines)


class EnterpriseKnowledgeAssistant:
    """
    Production-style RAG assistant with pluggable model providers.

    Pipeline:
      1. Index documents into Chroma (persistent)
      2. Retrieve relevant chunks per question
      3. Augment prompt with context + citations
      4. Generate answer via configured LLM
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        validate_settings(self.settings)

        self.embeddings = get_embeddings(self.settings)
        self.llm: BaseChatModel = get_llm(self.settings)
        self.indexer = KnowledgeIndexer(self.settings, self.embeddings)
        self.provider_info = describe_active_models(self.settings)

    def index(self, force_rebuild: bool = False) -> dict[str, int | str]:
        """Index (or re-index) all documents in the knowledge base."""
        trace_id = new_trace_id()
        timer = Timer()

        try:
            result = self.indexer.index_documents(force_rebuild=force_rebuild)
            log_trace(
                RequestTrace(
                    trace_id=trace_id,
                    operation="index",
                    total_ms=timer.stop(),
                    status=str(result.get("status", "ok")),
                    provider_info=self.provider_info,
                )
            )
            result["trace_id"] = trace_id
            return result
        except Exception as exc:
            log_trace(
                RequestTrace(
                    trace_id=trace_id,
                    operation="index",
                    total_ms=timer.stop(),
                    status="error",
                    error=str(exc),
                    provider_info=self.provider_info,
                )
            )
            raise

    def ask(self, question: str, trace_id: str | None = None) -> AssistantResponse:
        """Full RAG pipeline: retrieve -> augment -> generate."""
        trace_id = trace_id or new_trace_id()
        total_timer = Timer()
        question = question.strip()

        if not question:
            return AssistantResponse(
                answer="Please provide a question.",
                provider_info=self.provider_info,
                trace_id=trace_id,
            )

        retrieval_timer = Timer()
        docs_with_scores = self._retrieve(question)
        retrieval_ms = retrieval_timer.stop()

        if not docs_with_scores:
            response = AssistantResponse(
                answer=(
                    "No knowledge base found. Add documents to "
                    f"{self.settings.documents_dir} and run: python main.py index"
                ),
                provider_info=self.provider_info,
                trace_id=trace_id,
                retrieval_ms=retrieval_ms,
                total_ms=total_timer.stop(),
            )
            log_trace(self._build_ask_trace(trace_id, question, response, docs_with_scores, retrieval_ms, 0.0))
            return response

        citations = self._build_citations(docs_with_scores)
        prompt = self._build_prompt(question, docs_with_scores)

        generation_timer = Timer()
        llm_response = self.llm.invoke(prompt)
        generation_ms = generation_timer.stop()

        response = AssistantResponse(
            answer=llm_response.content,
            citations=citations,
            provider_info=self.provider_info,
            trace_id=trace_id,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            total_ms=total_timer.stop(),
        )
        log_trace(self._build_ask_trace(trace_id, question, response, docs_with_scores, retrieval_ms, generation_ms))
        return response

    def _build_ask_trace(
        self,
        trace_id: str,
        question: str,
        response: AssistantResponse,
        docs_with_scores: list[tuple[Document, float]],
        retrieval_ms: float,
        generation_ms: float,
    ) -> RequestTrace:
        return RequestTrace(
            trace_id=trace_id,
            operation="ask",
            question=question,
            answer_preview=response.answer[:200],
            retrieval_ms=round(retrieval_ms, 1),
            generation_ms=round(generation_ms, 1),
            total_ms=round(response.total_ms or 0, 1),
            chunks_retrieved=len(docs_with_scores),
            chunks=[
                ChunkTrace(
                    source=doc.metadata.get("source", "unknown"),
                    score=round(float(score), 3),
                    excerpt=doc.page_content[:120].replace("\n", " "),
                )
                for doc, score in docs_with_scores
            ],
            cited_sources=[c.source for c in response.citations],
            provider_info=response.provider_info,
        )

    def _retrieve(self, question: str) -> list[tuple[Document, float]]:
        vector_store = self.indexer.get_vector_store()
        try:
            return vector_store.similarity_search_with_score(
                question, k=self.settings.top_k
            )
        except Exception:
            return []

    def _build_citations(
        self, docs_with_scores: list[tuple[Document, float]]
    ) -> list[Citation]:
        citations: list[Citation] = []
        seen_sources: set[str] = set()

        for doc, score in docs_with_scores:
            source = doc.metadata.get("source", "unknown")
            if source in seen_sources:
                continue
            seen_sources.add(source)
            citations.append(
                Citation(
                    source=source,
                    excerpt=doc.page_content.strip().replace("\n", " "),
                    score=round(float(score), 3),
                )
            )
        return citations

    def _build_prompt(
        self, question: str, docs_with_scores: list[tuple[Document, float]]
    ) -> str:
        context_parts = []
        for i, (doc, _) in enumerate(docs_with_scores, start=1):
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"[{i}] Source: {source}\n{doc.page_content}")

        context = "\n\n---\n\n".join(context_parts)
        return RAG_PROMPT.format(context=context, question=question)
