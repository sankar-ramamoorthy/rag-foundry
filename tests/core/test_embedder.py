from ingestion_service.src.core.embedders.mock import MockEmbedder
from ingestion_service.src.core.chunks import Chunk


def test_mock_embedder_deterministic():
    embedder = MockEmbedder()

    chunks = [
        Chunk(chunk_id="1", content="hello", metadata={}),
        Chunk(chunk_id="2", content="hello world", metadata={}),
    ]

    embeddings = embedder.embed(chunks)

    assert len(embeddings) == 2
    assert embeddings[0] == [5.0, 5.0, 1.0]
    assert embeddings[1] == [11.0, 1.0, 1.0]
