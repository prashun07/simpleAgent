"""
RAG Agent — Retrieval-Augmented Generation in three steps.

    User question
         |
         v
    [RETRIEVE]  Search vector store for relevant text chunks
         |
         v
    [AUGMENT]   Build a prompt: context + question
         |
         v
    [GENERATE]  Gemini answers using the provided context
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.vectorstores import InMemoryVectorStore

from tool.langchainloader import build_vector_store


# How many document chunks to fetch per question
TOP_K = 3

# Prompt template: tells the LLM to answer ONLY from the retrieved context
RAG_PROMPT = """You are a helpful assistant. Answer the question using ONLY the context below.
If the context does not contain enough information, say "I don't have that information in my knowledge base."

--- CONTEXT ---
{context}
--- END CONTEXT ---

Question: {question}

Answer:"""


class RAGAgent:
    """Simple RAG agent: retrieve relevant docs, then ask Gemini."""

    def __init__(self, api_key: str, data_dir: str = "data"):
        self.api_key = api_key

        # Step 0 (setup): index documents into a searchable vector store
        self.vector_store: InMemoryVectorStore = build_vector_store(
            api_key=api_key,
            data_dir=data_dir,
        )

        # LLM for the final answer (Generation step)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
        )

    def _retrieve(self, question: str) -> list[str]:
        """RETRIEVE: find the most relevant document chunks for this question."""
        results = self.vector_store.similarity_search(question, k=TOP_K)
        return [doc.page_content for doc in results]

    def _build_prompt(self, question: str, chunks: list[str]) -> str:
        """AUGMENT: combine retrieved chunks and the user question into one prompt."""
        context = "\n\n---\n\n".join(chunks)
        return RAG_PROMPT.format(context=context, question=question)

    def process_input(self, user_input: str) -> str:
        """Full RAG pipeline: Retrieve -> Augment -> Generate."""
        question = user_input.strip()
        if not question:
            return "Please ask a question."

        # 1. RETRIEVE
        chunks = self._retrieve(question)

        # 2. AUGMENT
        prompt = self._build_prompt(question, chunks)

        # 3. GENERATE
        response = self.llm.invoke(prompt)
        return response.content
