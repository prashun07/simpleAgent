"""
Enterprise Knowledge Assistant — RAG agent with citations.

Supports local (Ollama) and cloud (Gemini, Groq) open-source-friendly models.
"""

from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel

from config.providers import describe_active_models, get_embeddings, get_llm
from config.settings import Settings, load_settings, validate_settings
from knowledge.indexer import KnowledgeIndexer


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

    def format(self) -> str:
        """Human-readable answer with numbered sources."""
        lines = [self.answer, ""]
        if self.citations:
            lines.append("Sources:")
            for i, cite in enumerate(self.citations, start=1):
                score = f" (relevance: {cite.score:.2f})" if cite.score is not None else ""
                lines.append(f"  [{i}] {cite.source}{score}")
                lines.append(f"      \"{cite.excerpt[:120]}...\"")
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
        return self.indexer.index_documents(force_rebuild=force_rebuild)

    def ask(self, question: str) -> AssistantResponse:
        """Full RAG pipeline: retrieve -> augment -> generate."""
        question = question.strip()
        if not question:
            return AssistantResponse(
                answer="Please provide a question.",
                provider_info=self.provider_info,
            )

        docs_with_scores = self._retrieve(question)
        if not docs_with_scores:
            return AssistantResponse(
                answer=(
                    "No knowledge base found. Add documents to "
                    f"{self.settings.documents_dir} and run: python main.py index"
                ),
                provider_info=self.provider_info,
            )

        citations = self._build_citations(docs_with_scores)
        prompt = self._build_prompt(question, docs_with_scores)
        response = self.llm.invoke(prompt)

        return AssistantResponse(
            answer=response.content,
            citations=citations,
            provider_info=self.provider_info,
        )

    def _retrieve(self, question: str) -> list[tuple[Document, float]]:
        vector_store = self.indexer.get_vector_store()
        try:
            return vector_store.similarity_search_with_score(
                question, k=self.settings.top_k
            )
        except Exception:
            # Empty collection — no documents indexed yet
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
