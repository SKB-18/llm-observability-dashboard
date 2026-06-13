"""
SQLAlchemy ORM models.
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Completion(Base):
    """Logged LLM completion."""

    __tablename__ = "completions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    model = Column(String(100), nullable=False, index=True)
    tokens_in = Column(Integer, nullable=False)
    tokens_out = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    cost_usd = Column(Float, nullable=False)
    user_id = Column(String(255), nullable=True, index=True)
    conversation_id = Column(String(255), nullable=True, index=True)
    # 'lmsys' = real production data from Chatbot Arena
    # 'evals_benchmark' = quality benchmark with real prompt/response text
    # 'production_log' = simulated production logs
    source = Column(String(50), nullable=False, default="lmsys", index=True)

    __table_args__ = (
        Index("ix_completions_model_timestamp", "model", "timestamp"),
    )


class EvalResult(Base):
    """Evaluation result linked to a completion."""

    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, index=True)
    completion_id = Column(Integer, ForeignKey("completions.id"), nullable=False, index=True)
    eval_type = Column(String(50), nullable=False)  # llm_judge, bleu, rouge, rules, human_preference
    score = Column(Float, nullable=False)
    criteria = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # 'human_preference' = from LMSYS winner field, 'computed' = BLEU/ROUGE/LLM, 'benchmark' = evals_dataset
    source = Column(String(50), nullable=False, default="computed", index=True)


class Model(Base):
    """Registry of known LLM models."""

    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    provider = Column(String(100), nullable=True)
    cost_per_input_token = Column(Float, nullable=True)
    cost_per_output_token = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    """Dashboard users."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


# ---------------------------------------------------------------------------
# Legacy model kept for backward compat with existing seed/migration scripts
# ---------------------------------------------------------------------------

class Upload(Base):
    """Metadata for a user-uploaded CSV dataset."""

    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(50), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    has_quality_rating = Column(Boolean, nullable=False, default=False)
    has_model_column = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LLMRequest(Base):
    __tablename__ = "llm_requests"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String, index=True)
    model = Column(String, index=True)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    latency_ms = Column(Float)
    cost_usd = Column(Float)
    temperature = Column(Float)
    max_tokens = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
