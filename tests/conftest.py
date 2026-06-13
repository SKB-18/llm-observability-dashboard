"""
Shared test infrastructure.

All test modules share a single in-memory SQLite engine so that
app.dependency_overrides[get_db] is set exactly once and never conflicts.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import get_db
from backend.models import Base

# Single shared in-memory engine for the entire test session
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=_engine)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


# Set override once, at import time
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def db():
    """Yield a fresh session; each test gets a clean schema."""
    Base.metadata.create_all(bind=_engine)
    session = _Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def reset_db():
    """Autouse-compatible fixture: create tables before test, drop after."""
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)
