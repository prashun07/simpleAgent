"""
Model provider factories.

Each function returns a LangChain-compatible model so the rest of the app
does not care whether you run locally (Ollama) or in the cloud (Gemini/Groq).
"""

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from config.settings import Settings


def get_llm(settings: Settings) -> BaseChatModel:
    """Create the chat model based on LLM_PROVIDER."""
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
        )

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.gemini_llm_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.2,
        )

    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.groq_llm_model,
            api_key=settings.groq_api_key,
            temperature=0.2,
        )

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def get_embeddings(settings: Settings) -> Embeddings:
    """Create the embedding model based on EMBEDDING_PROVIDER."""
    if settings.embedding_provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )

    if settings.embedding_provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.gemini_api_key,
        )

    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def describe_active_models(settings: Settings) -> dict[str, str]:
    """Return a safe summary of active providers (no secrets)."""
    llm_model = {
        "ollama": settings.ollama_llm_model,
        "gemini": settings.gemini_llm_model,
        "groq": settings.groq_llm_model,
    }[settings.llm_provider]

    embedding_model = {
        "ollama": settings.ollama_embedding_model,
        "gemini": settings.gemini_embedding_model,
    }[settings.embedding_provider]

    return {
        "llm_provider": settings.llm_provider,
        "llm_model": llm_model,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": embedding_model,
        "mode": "local" if _is_fully_local(settings) else "hybrid/cloud",
    }


def _is_fully_local(settings: Settings) -> bool:
    return settings.llm_provider == "ollama" and settings.embedding_provider == "ollama"
