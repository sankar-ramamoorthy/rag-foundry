# sample_test.py
from ingestion_service.src.core.headless_ingest import HeadlessIngestor
from ingestion_service.src.core.pipeline import IngestionPipeline
from ingestion_service.src.core.validation import MockValidator
from ingestion_service.shared.embedders.mock import MockEmbedder
from ingestion_service.src.core.vectorstore.memory import MemoryVectorStore


def main():
    # Initialize pipeline with real components
    pipeline = IngestionPipeline(
        validator=MockValidator(),
        embedder=MockEmbedder(),
        vector_store=MemoryVectorStore(),
    )

    # Create headless ingestor WITH ingestion context
    ingestor = HeadlessIngestor(
        pipeline=pipeline,
        source_type="text",
        provider="mock",
    )

    # 1–2 five-word sentences
    texts = ["Apples grow on tall trees.", "Dogs bark loudly at night."]

    # Ingest texts
    for idx, text in enumerate(texts, start=1):
        print(f"\n[TEST {idx}] Ingesting: {text}")
        ingestor.ingest_text(
            text=text,
            ingestion_id=f"test_{idx}",
        )

    # Final results
    total = len(pipeline._vector_store._vectors)
    print(f"\n[RESULT] Total records in vector store: {total}")


if __name__ == "__main__":
    main()
