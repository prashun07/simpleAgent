"""
Document loading and indexing utilities for RAG.

RAG Step 1 (Indexing): Load documents -> split into chunks -> embed -> store in vector DB.
This happens once when the agent starts.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_local_documents(data_dir: str = "data") -> list[Document]:
    """Load all .txt files from the data folder as LangChain Documents."""
    data_path = Path(data_dir)
    if not data_path.exists():
        return []

    docs: list[Document] = []
    for file_path in sorted(data_path.glob("*.txt")):
        # Skip result.txt — that is agent output, not knowledge
        if file_path.name == "result.txt":
            continue
        text = file_path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": str(file_path)},
            )
        )
    return docs


def build_vector_store(
    api_key: str,
    data_dir: str = "data",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> InMemoryVectorStore:
    """
    Build an in-memory vector store from local text files.

    Pipeline:
      1. Load documents from data/
      2. Split into overlapping chunks (easier to search precisely)
      3. Embed each chunk with Gemini
      4. Store vectors for similarity search
    """
    docs = load_local_documents(data_dir)
    if not docs:
        raise FileNotFoundError(
            f"No .txt knowledge files found in '{data_dir}/'. "
            "Add at least one file (e.g. data/knowledge.txt)."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(docs)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=api_key,
    )
    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_documents(chunks)

    print(f"RAG index ready: {len(docs)} file(s), {len(chunks)} chunk(s).")
    return vector_store
