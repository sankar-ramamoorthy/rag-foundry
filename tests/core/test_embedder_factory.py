# tests/core/test_embedder_factory.py - SIMPLE & BULLETPROOF
import os
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.config import reset_settings_cache


def test_factory_ollama_explicit():
    """get_embedder("ollama") → returns OllamaEmbedder instance."""
    reset_settings_cache()
    embedder = get_embedder("ollama")
    assert embedder.name == "ollama"


def test_factory_mock_explicit():
    """get_embedder("mock") → returns MockEmbedder instance."""
    reset_settings_cache()
    embedder = get_embedder("mock")
    assert embedder.name == "mock"


def test_factory_config_fallback():
    """No param → uses EMBEDDING_PROVIDER from .env/config."""
    reset_settings_cache()
    os.environ["EMBEDDING_PROVIDER"] = "mock"
    embedder = get_embedder()  # Uses config
    assert embedder.name == "mock"
