"""
Database configuration, engine, and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from backend.config import settings
from backend.models import Base

logger = logging.getLogger(__name__)

_DATABASE_URL = settings.DATABASE_URL

# SQLite needs special args; PostgreSQL uses pool settings from config
if "sqlite" in _DATABASE_URL:
    engine = create_engine(
        _DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DB_ECHO,
    )
else:  # pragma: no cover  — PostgreSQL path, requires a live PG server
    engine = create_engine(
        _DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,
        echo=settings.DB_ECHO,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables (idempotent)."""
    logger.info("Creating database tables…")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready.")


def drop_tables() -> None:
    """Drop all tables. Development use only."""
    Base.metadata.drop_all(bind=engine)
