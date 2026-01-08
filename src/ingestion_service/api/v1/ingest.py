# src/ingestion_service/api/v1/ingest.py
from uuid import uuid4
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status

from ingestion_service.api.v1.models import IngestRequest, IngestResponse
from ingestion_service.core.database_session import get_sessionmaker
from ingestion_service.core.models import IngestionRequest
from ingestion_service.core.pipeline import IngestionPipeline
from ingestion_service.core.status_manager import StatusManager
from ingestion_service.core.vectorstore.pgvector_store import PgVectorStore
from ingestion_service.core.config import get_settings
from ingestion_service.core.embedders.factory import get_embedder

router = APIRouter(tags=["ingestion"])
SessionLocal = get_sessionmaker()


class NoOpValidator:
    """Synchronous no-op validator."""

    def validate(self, text: str) -> None:
        return None


def _build_pipeline() -> IngestionPipeline:
    settings = get_settings()
    embedder = get_embedder(settings.EMBEDDING_PROVIDER)

    vector_store = PgVectorStore(
        dsn=settings.DATABASE_URL,
        dimension=getattr(embedder, "dimension", 3),
        provider=settings.EMBEDDING_PROVIDER,
    )

    return IngestionPipeline(
        validator=NoOpValidator(),
        embedder=embedder,
        vector_store=vector_store,
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit content for ingestion",
)
def ingest_json(request: IngestRequest) -> IngestResponse:
    ingestion_id = uuid4()

    with SessionLocal() as session:
        manager = StatusManager(session)

        manager.create_request(
            ingestion_id=ingestion_id,
            source_type=request.source_type,
            metadata=request.metadata,
        )
        manager.mark_running(ingestion_id)

        pipeline = _build_pipeline()
        try:
            pipeline.run(
                text="placeholder ingestion content",
                ingestion_id=str(ingestion_id),
            )
            manager.mark_completed(ingestion_id)
        except Exception as exc:
            manager.mark_failed(ingestion_id, error=str(exc))
            raise HTTPException(
                status_code=500, detail="Ingestion pipeline failed"
            ) from exc

    return IngestResponse(ingestion_id=ingestion_id, status="accepted")


@router.post(
    "/ingest/file",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False,
)
def ingest_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(default=None),
) -> IngestResponse:
    try:
        parsed_metadata = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON") from exc

    ingestion_id = uuid4()

    try:
        text = file.file.read().decode("utf-8")
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="Unable to read uploaded file"
        ) from exc

    with SessionLocal() as session:
        manager = StatusManager(session)

        manager.create_request(
            ingestion_id=ingestion_id,
            source_type="file",
            metadata={**parsed_metadata, "filename": file.filename},
        )
        manager.mark_running(ingestion_id)

        pipeline = _build_pipeline()
        try:
            pipeline.run(text=text, ingestion_id=str(ingestion_id))
            manager.mark_completed(ingestion_id)
        except Exception as exc:
            manager.mark_failed(ingestion_id, error=str(exc))
            raise HTTPException(
                status_code=500, detail="Ingestion pipeline failed"
            ) from exc

    return IngestResponse(ingestion_id=ingestion_id, status="accepted")


@router.get(
    "/ingest/{ingestion_id}",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ingestion status",
)
def ingest_status(ingestion_id: str) -> IngestResponse:
    from uuid import UUID

    try:
        ingestion_uuid = UUID(ingestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ingestion ID format")

    with SessionLocal() as session:
        request = (
            session.query(IngestionRequest)
            .filter_by(ingestion_id=ingestion_uuid)
            .first()
        )
        if request is None:
            raise HTTPException(status_code=404, detail="Ingestion ID not found")

        return IngestResponse(ingestion_id=request.ingestion_id, status=request.status)
