"""
Application settings loaded from environment variables (.env).

Switch between local (Ollama) and cloud (Gemini, Groq) by changing
LLM_PROVIDER and EMBEDDING_PROVIDER — no code changes needed.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SUPPORTED_LLM_PROVIDERS = ("ollama", "gemini", "groq")
SUPPORTED_EMBEDDING_PROVIDERS = ("ollama", "gemini")

PLACEHOLDER_API_KEYS = {
    "your-gemini-api-key-here",
    "your-groq-api-key-here",
    "your-api-key-here",
    "changeme",
}


def _clean_api_key(key: str | None) -> str | None:
    """Strip whitespace and quotes from API keys loaded from .env."""
    if key is None:
        return None
    cleaned = key.strip().strip('"').strip("'")
    return cleaned or None


def _is_placeholder_api_key(key: str | None) -> bool:
    if not key:
        return True
    return key.strip().lower() in PLACEHOLDER_API_KEYS or key.lower().startswith(
        "your-"
    )


@dataclass(frozen=True)
class Settings:
    # --- Provider selection ---
    llm_provider: str
    embedding_provider: str

    # --- Ollama (local open-source models) ---
    ollama_base_url: str
    ollama_llm_model: str
    ollama_embedding_model: str

    # --- Google Gemini (cloud) ---
    gemini_api_key: str | None
    gemini_llm_model: str
    gemini_embedding_model: str

    # --- Groq (cloud, hosts open-source models like Llama) ---
    groq_api_key: str | None
    groq_llm_model: str

    # --- Knowledge base paths ---
    documents_dir: Path
    chroma_dir: Path
    chroma_collection: str

    # --- RAG tuning ---
    chunk_size: int
    chunk_overlap: int
    top_k: int


def load_settings() -> Settings:
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()

    if llm_provider not in SUPPORTED_LLM_PROVIDERS:
        raise ValueError(
            f"LLM_PROVIDER must be one of {SUPPORTED_LLM_PROVIDERS}, got '{llm_provider}'"
        )
    if embedding_provider not in SUPPORTED_EMBEDDING_PROVIDERS:
        raise ValueError(
            f"EMBEDDING_PROVIDER must be one of {SUPPORTED_EMBEDDING_PROVIDERS}, "
            f"got '{embedding_provider}'"
        )

    project_root = Path(__file__).resolve().parent.parent

    return Settings(
        llm_provider=llm_provider,
        embedding_provider=embedding_provider,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_llm_model=os.getenv("OLLAMA_LLM_MODEL", "llama3.2:3b"),
        ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        gemini_api_key=_clean_api_key(os.getenv("GEMINI_API_KEY")),
        gemini_llm_model=os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash"),
        gemini_embedding_model=os.getenv(
            "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-2"
        ),
        groq_api_key=_clean_api_key(os.getenv("GROQ_API_KEY")),
        groq_llm_model=os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile"),
        documents_dir=project_root / os.getenv("DOCUMENTS_DIR", "data/documents"),
        chroma_dir=project_root / os.getenv("CHROMA_DIR", "chroma_db"),
        chroma_collection=os.getenv("CHROMA_COLLECTION", "enterprise_knowledge"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        top_k=int(os.getenv("TOP_K", "4")),
    )


def validate_settings(settings: Settings) -> None:
    """Fail fast with clear errors if required API keys or paths are missing."""
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        if _is_placeholder_api_key(settings.gemini_api_key):
            raise ValueError(
                "GEMINI_API_KEY is still a placeholder. "
                "Set a real key from https://aistudio.google.com/apikey"
            )

    if settings.embedding_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        if _is_placeholder_api_key(settings.gemini_api_key):
            raise ValueError(
                "GEMINI_API_KEY is still a placeholder. "
                "Set a real key from https://aistudio.google.com/apikey"
            )

    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        if _is_placeholder_api_key(settings.groq_api_key):
            raise ValueError(
                "GROQ_API_KEY is still a placeholder. "
                "Set a real key from https://console.groq.com"
            )

    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
