"""
Load documents from the knowledge base folder.

Supported formats: .txt, .md, .pdf
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
SKIP_FILES = {"result.txt"}


def load_documents(documents_dir: Path) -> list[Document]:
    """Load all supported documents from a directory (recursive)."""
    if not documents_dir.exists():
        return []

    docs: list[Document] = []
    for file_path in sorted(documents_dir.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name in SKIP_FILES:
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        docs.extend(_load_single_file(file_path))

    return docs


def _load_single_file(file_path: Path) -> list[Document]:
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()
        for page in pages:
            page.metadata["source"] = str(file_path)
        return pages

    loader = TextLoader(str(file_path), encoding="utf-8")
    loaded = loader.load()
    for doc in loaded:
        doc.metadata["source"] = str(file_path)
    return loaded
