import os
import pytest
from typing import List, cast

from ingestion_service.core.config import reset_settings_cache
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.validation import MockValidator
from ingestion_service.core.embedders.factory import get_embedder
from ingestion_service.core.embedders.ollama import OllamaEmbedder
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore


# ------------------------------------------------------------------
# HARD SKIP: Docker-only (requires Postgres + Ollama)
# ------------------------------------------------------------------
if "DATABASE_URL" not in os.environ:
    pytest.skip(
        "Docker-only embedding correctness test (requires Ollama + pgvector)",
        allow_module_level=True,
    )


@pytest.mark.integration
@pytest.mark.docker
class TestOllamaEmbeddingCorrectness:
    """MS3-tight correctness checks for real Ollama embeddings."""

    @pytest.fixture(autouse=True)
    def setup(self, clean_vectors_table, test_database_url):
        reset_settings_cache()

        embedder = cast(OllamaEmbedder, get_embedder("ollama"))
        assert embedder.dimension == 768

        vector_store = PgVectorStore(
            dsn=test_database_url,
            dimension=embedder.dimension,
            provider="ollama",
        )

        self.pipeline = IngestionPipeline(
            validator=MockValidator(),
            chunker=None,  # auto-select
            embedder=embedder,
            vector_store=vector_store,
        )

    def test_ollama_produces_768d_vectors(self):
        chunks = self.pipeline._chunk("test document content")
        embeddings: List[List[float]] = self.pipeline._embed(chunks)

        assert len(embeddings) == len(chunks)
        assert all(len(vec) == 768 for vec in embeddings)

    def test_identical_texts_are_retrievable(self):
        self.pipeline.run(text="hello world", ingestion_id="a")
        self.pipeline.run(text="hello world", ingestion_id="b")

        query_chunks = self.pipeline._chunk("hello world")
        query_vec = self.pipeline._embed(query_chunks)[0]

        results = self.pipeline._vector_store.similarity_search(query_vec, k=5)
        ingestion_ids = {r.metadata.ingestion_id for r in results}

        assert {"a", "b"} & ingestion_ids

    def test_semantic_match_is_present(self):
        self.pipeline.run(text="The cat sat on the mat", ingestion_id="corpus")
        self.pipeline.run(text="A feline rested upon a rug", ingestion_id="corpus")
        self.pipeline.run(text="The quick brown fox jumps", ingestion_id="corpus")

        query_chunks = self.pipeline._chunk("cat sitting on rug")
        query_vec = self.pipeline._embed(query_chunks)[0]

        results = self.pipeline._vector_store.similarity_search(query_vec, k=3)
        texts = [r.metadata.chunk_text.lower() for r in results]

        assert any(
            phrase in text
            for text in texts
            for phrase in ("cat", "feline", "rug", "mat")
        )
