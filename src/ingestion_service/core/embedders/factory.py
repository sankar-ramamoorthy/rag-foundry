# src/ingestion_service/core/embedders/factory.py
from ingestion_service.core.embedders.mock import MockEmbedder
from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.core.config import get_settings


def get_embedder(provider: str | None = None):
    """
    Return an embedder based on provider name.

    - If provider is "ollama", returns OllamaEmbedder
    - Otherwise, returns MockEmbedder
    """
    settings = get_settings()
    # Ensure provider is a string
    provider_str: str = (
        provider if provider is not None else settings.EMBEDDING_PROVIDER
    )

    if provider_str == "ollama":
        return OllamaEmbedder(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_EMBED_MODEL,
            batch_size=settings.OLLAMA_BATCH_SIZE,
        )
    else:
        return MockEmbedder()
