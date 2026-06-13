"""
Log ingestion endpoints: single, batch, and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
import logging

from backend.database import get_db
from backend.models import Completion
from backend.schemas import (
    CompletionLog,
    CompletionLogResponse,
    LogResponse,
    BatchIngestionResponse,
    BatchIngestionError,
)
from backend.utils.db import insert_completion, batch_insert_completions, get_completion_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get("", status_code=status.HTTP_200_OK)
def list_logs(
    page: int = Query(1, ge=1, description="1-based page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page (max 200)"),
    model: Optional[str] = Query(None),
    source: Optional[str] = Query(None, description="Filter by source: 'lmsys' or 'evals_benchmark'"),
    db: Session = Depends(get_db),
):
    """List completion logs with pagination, newest first."""
    offset = (page - 1) * limit
    q = db.query(Completion)
    if model:
        q = q.filter(Completion.model == model)
    if source:
        q = q.filter(Completion.source == source)
    total = q.count()
    rows = q.order_by(Completion.timestamp.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": max(1, -(-total // limit)),
        "items": [
            {
                "id": r.id,
                "prompt": r.prompt[:120] + ("…" if len(r.prompt) > 120 else ""),
                "response": r.response[:120] + ("…" if len(r.response) > 120 else ""),
                "model": r.model,
                "tokens_in": r.tokens_in,
                "tokens_out": r.tokens_out,
                "latency_ms": r.latency_ms,
                "cost_usd": r.cost_usd,
                "user_id": r.user_id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in rows
        ],
    }


@router.post("", response_model=LogResponse, status_code=status.HTTP_201_CREATED)
def ingest_log(log: CompletionLog, db: Session = Depends(get_db)) -> LogResponse:
    """
    Ingest a single LLM completion log.

    Returns the assigned log ID and server timestamp.
    """
    logger.info("POST /api/v1/logs model=%s user=%s", log.model, log.user_id)
    try:
        obj = insert_completion(db, log)
    except Exception as exc:
        logger.error("Failed to store log: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )

    return LogResponse(
        status="logged",
        log_id=obj.id,
        timestamp=obj.timestamp,
    )


@router.post("/batch", response_model=BatchIngestionResponse, status_code=status.HTTP_200_OK)
def ingest_batch(
    logs: List[CompletionLog], db: Session = Depends(get_db)
) -> BatchIngestionResponse:
    """
    Ingest up to 1 000 completions in a single transactional batch.

    If more than 50 individual items fail, the entire batch is rolled back.
    """
    if len(logs) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size exceeds maximum of 1000 items.",
        )

    logger.info("POST /api/v1/logs/batch count=%d", len(logs))
    inserted, raw_errors = batch_insert_completions(db, logs)

    errors = [BatchIngestionError(index=i, reason=r) for i, r in raw_errors]

    return BatchIngestionResponse(
        status="success" if not errors or len(errors) <= 50 else "rollback",
        ingested_count=len(inserted),
        failed_count=len(errors),
        errors=errors,
    )


@router.get("/{log_id}", response_model=CompletionLogResponse, status_code=status.HTTP_200_OK)
def get_log(log_id: int, db: Session = Depends(get_db)) -> CompletionLogResponse:
    """Retrieve a single completion log by ID."""
    obj = get_completion_by_id(db, log_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log {log_id} not found.",
        )
    return obj
