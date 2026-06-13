"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class EvalType(str, Enum):
    llm_judge = "llm_judge"
    bleu = "bleu"
    rouge = "rouge"
    rules = "rules"
    human_preference = "human_preference"
    human = "human"


# ---------------------------------------------------------------------------
# Core domain schemas
# ---------------------------------------------------------------------------

class CompletionLog(BaseModel):
    """Payload for logging a single LLM completion."""

    prompt: str
    response: str
    model: str
    tokens_in: int = Field(..., gt=0, description="Input token count, must be > 0")
    tokens_out: int = Field(..., gt=0, description="Output token count, must be > 0")
    latency_ms: float = Field(..., gt=0, description="End-to-end latency in ms, must be > 0")
    cost_usd: float = Field(..., ge=0, description="Cost in USD, must be >= 0")
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None


class CompletionLogResponse(BaseModel):
    """Read schema for a stored completion — no gt/gt constraints (data may be seeded)."""

    id: int
    prompt: str
    response: str
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: float
    cost_usd: float
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class EvalResult(BaseModel):
    """Evaluation score attached to a completion."""

    completion_id: int
    eval_type: EvalType
    score: float = Field(..., ge=0, le=1, description="Score in [0, 1]")
    criteria: Optional[str] = None
    explanation: Optional[str] = None


class MetricsQuery(BaseModel):
    """Query parameters for metrics endpoints."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    model: Optional[str] = None
    user_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Batch ingestion
# ---------------------------------------------------------------------------

class BatchIngestionError(BaseModel):
    index: int
    reason: str


class BatchIngestionResponse(BaseModel):
    status: str
    ingested_count: int
    failed_count: int
    errors: List[BatchIngestionError] = []


# ---------------------------------------------------------------------------
# Single log response
# ---------------------------------------------------------------------------

class LogResponse(BaseModel):
    status: str
    log_id: int
    timestamp: datetime


# ---------------------------------------------------------------------------
# Legacy schemas kept for backward compatibility
# ---------------------------------------------------------------------------

class LLMRequestCreate(BaseModel):
    user_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cost_usd: float
    temperature: float
    max_tokens: int
    success: bool = True
    error_message: Optional[str] = None


class LLMRequestResponse(LLMRequestCreate):
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
