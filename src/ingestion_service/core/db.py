# src/ingestion_service/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ingestion_service.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, echo=True)

# SQLAlchemy 1.4: sessionmaker is a factory returning Session objects
SessionLocal: sessionmaker = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
