from fastapi import APIRouter

from src.api.v1.ingest import router as ingest_router

router = APIRouter(prefix="/v1")

router.include_router(ingest_router)
