"""
Index documents into a persistent Chroma vector database.
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Settings
from knowledge.loader import load_documents


class KnowledgeIndexer:
    """Manages document ingestion and Chroma vector store lifecycle."""

    def __init__(self, settings: Settings, embeddings: Embeddings):
        self.settings = settings
        self.embeddings = embeddings
        self._vector_store: VectorStore | None = None

    def document_count(self) -> int:
        """Return how many chunks are currently stored in Chroma."""
        store = self._get_or_create_store()
        return store._collection.count()

    def index_documents(self, force_rebuild: bool = False) -> dict[str, int | str]:
        """
        Load documents, split into chunks, and store in Chroma.

        If force_rebuild=True, wipes the collection and re-indexes from scratch.
        If the index already has data and force_rebuild=False, skips re-indexing.
        """
        docs = load_documents(self.settings.documents_dir)
        if not docs:
            return {
                "status": "empty",
                "files": 0,
                "chunks": 0,
                "message": (
                    f"No documents found in {self.settings.documents_dir}. "
                    "Add .txt, .md, or .pdf files and run again."
                ),
            }

        if not force_rebuild and self.document_count() > 0:
            return {
                "status": "skipped",
                "files": 0,
                "chunks": self.document_count(),
                "message": (
                    f"Index already has {self.document_count()} chunk(s). "
                    "Use 'python main.py index --rebuild' to re-index."
                ),
            }

        if force_rebuild:
            self._clear_collection()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        vector_store = self._get_or_create_store()
        vector_store.add_documents(chunks)
        self._vector_store = vector_store

        file_count = len({doc.metadata.get("source", "") for doc in docs})
        return {
            "status": "indexed",
            "files": file_count,
            "chunks": len(chunks),
            "message": f"Indexed {file_count} file(s) into {len(chunks)} chunk(s).",
        }

    def get_vector_store(self) -> VectorStore:
        """Return the Chroma store (creates an empty one if needed)."""
        if self._vector_store is None:
            self._vector_store = self._get_or_create_store()
        return self._vector_store

    def _get_or_create_store(self) -> Chroma:
        return Chroma(
            collection_name=self.settings.chroma_collection,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_dir),
        )

    def _clear_collection(self) -> None:
        """Remove persisted Chroma data for a clean rebuild."""
        import shutil

        chroma_path = self.settings.chroma_dir
        if chroma_path.exists():
            shutil.rmtree(chroma_path)
        chroma_path.mkdir(parents=True, exist_ok=True)
        self._vector_store = None
