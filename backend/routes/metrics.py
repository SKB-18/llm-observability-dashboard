"""
Analytics / metrics query endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.utils.metrics_queries import (
    query_summary,
    query_by_model,
    query_by_hour,
    query_percentiles,
    query_cost_breakdown,
    query_eval_analytics,
    query_model_comparison,
    query_by_source,
    query_eval_summary,
)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


def _parse_dates(
    start_date: Optional[str] = Query(None, description="ISO-8601 start datetime"),
    end_date: Optional[str] = Query(None, description="ISO-8601 end datetime"),
):
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    return start, end


@router.get("/summary")
def get_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Aggregate summary for a time period."""
    start, end = _parse_dates(start_date, end_date)
    return query_summary(db, start, end)


@router.get("/by-model")
def get_by_model(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Per-model stats sorted by request count DESC."""
    start, end = _parse_dates(start_date, end_date)
    return query_by_model(db, start, end)


@router.get("/by-hour")
def get_by_hour(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Hourly time-series data for charting."""
    start, end = _parse_dates(start_date, end_date)
    return query_by_hour(db, start, end)


@router.get("/latency-percentiles")
def get_latency_percentiles(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Latency percentiles (p50/p75/p90/p95/p99), optionally filtered by model."""
    start, end = _parse_dates(start_date, end_date)
    return query_percentiles(db, start, end, model)


@router.get("/cost-breakdown")
def get_cost_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Total cost broken down by model and by hour."""
    start, end = _parse_dates(start_date, end_date)
    return query_cost_breakdown(db, start, end)


@router.get("/evals")
def get_eval_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Eval score analytics: per-type averages, score distribution, trend over time."""
    start, end = _parse_dates(start_date, end_date)
    return query_eval_analytics(db, start, end)


@router.get("/model-comparison")
def get_model_comparison(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Per-model win rates from LMSYS human-judged arena battles."""
    start, end = _parse_dates(start_date, end_date)
    return query_model_comparison(db, start, end)


@router.get("/source/{source}")
def get_metrics_by_source(
    source: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Metrics scoped to a single data source.
    source: 'lmsys' for production metrics, 'evals_benchmark' for quality metrics.
    """
    start, end = _parse_dates(start_date, end_date)
    return query_by_source(db, source, start, end)


@router.get("/eval-summary")
def get_eval_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Side-by-side summary of LMSYS production data vs evals_benchmark quality scores."""
    start, end = _parse_dates(start_date, end_date)
    return query_eval_summary(db, start, end)
