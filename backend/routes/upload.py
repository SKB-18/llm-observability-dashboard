"""
CSV dataset upload endpoint.

Accepted CSV columns
--------------------
Required:
  prompt        – the input text
  response      – the model output text

Optional:
  model         – model name (default: "uploaded")
  tokens_in     – input token count  (estimated from word count if absent)
  tokens_out    – output token count (estimated from word count if absent)
  latency_ms    – response latency   (default: 0)
  cost_usd      – USD cost           (default: 0)
  quality_rating– 0–10 human quality score (stored as eval score 0–1)
  criteria      – evaluation criteria text
"""
from __future__ import annotations

import csv
import io
import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Completion, EvalResult, Upload
from backend.evals.text_metrics import TextMetrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/upload", tags=["upload"])

_REQUIRED = {"prompt", "response"}
_OPTIONAL = {"model", "tokens_in", "tokens_out", "latency_ms", "cost_usd",
             "quality_rating", "criteria"}
MAX_ROWS = 10_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Rough word-based token estimate (1 word ≈ 1.3 tokens)."""
    return max(1, int(len(text.split()) * 1.3))


def _parse_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val) if val.strip() else default
    except (ValueError, AttributeError):  # pragma: no cover
        return default


def _parse_int(val: str, default: int = 0) -> int:
    try:
        return int(float(val)) if val.strip() else default
    except (ValueError, AttributeError):  # pragma: no cover
        return default


def _parse_csv(content: bytes) -> tuple[list[dict], list[str]]:
    """
    Parse CSV bytes and return (rows, header).
    Raises ValueError on format errors.
    """
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    header = [c.strip().lower() for c in (reader.fieldnames or [])]

    missing = _REQUIRED - set(header)
    if missing:
        raise ValueError(
            f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
            f"Required: prompt, response. "
            f"Optional: model, tokens_in, tokens_out, latency_ms, cost_usd, quality_rating, criteria."
        )

    rows = []
    for i, row in enumerate(reader):
        if i >= MAX_ROWS:  # pragma: no cover
            break
        # Normalise keys to lowercase/stripped
        rows.append({k.strip().lower(): v for k, v in row.items()})

    if not rows:
        raise ValueError("CSV file contains no data rows.")

    return rows, header


def _compute_evals(
    db: Session,
    completion_id: int,
    prompt: str,
    response: str,
    quality_rating: Optional[float],
    criteria: str,
) -> None:
    """Compute and store BLEU, ROUGE, and human rating for one row."""
    evals: list[EvalResult] = []

    try:
        bleu = TextMetrics.bleu_score(prompt, response)
        evals.append(EvalResult(
            completion_id=completion_id,
            eval_type="bleu",
            score=bleu,
            criteria=criteria or None,
            source="computed",
        ))
    except Exception:  # pragma: no cover
        pass

    try:
        rouge = TextMetrics.rouge_score(prompt, response)
        score = (rouge["rouge1"] + rouge["rougeL"]) / 2
        evals.append(EvalResult(
            completion_id=completion_id,
            eval_type="rouge",
            score=score,
            criteria=criteria or None,
            source="computed",
        ))
    except Exception:  # pragma: no cover
        pass

    if quality_rating is not None:
        # Normalise to 0-1: accept 0-10 or 0-1
        normalised = quality_rating / 10.0 if quality_rating > 1.0 else quality_rating
        normalised = max(0.0, min(1.0, normalised))
        evals.append(EvalResult(
            completion_id=completion_id,
            eval_type="human",
            score=normalised,
            source="benchmark",
        ))

    if evals:
        db.add_all(evals)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/csv", status_code=status.HTTP_201_CREATED)
def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV dataset and receive metrics immediately.

    The response contains per-column averages (BLEU, ROUGE, human rating)
    plus a `source_id` you can use to query `/api/v1/metrics/source/{source_id}`.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    content = file.file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB hard cap
        raise HTTPException(status_code=413, detail="File too large (max 50 MB).")

    try:
        rows, header = _parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    has_quality = "quality_rating" in header
    has_model   = "model" in header

    source_id = "upload_" + uuid.uuid4().hex[:8]
    now = datetime.utcnow()

    # Parse rows into (Completion, quality_rating, criteria) triples
    parsed: list[tuple[Completion, Optional[float], str]] = []

    for row in rows:
        prompt   = row.get("prompt", "").strip()
        response = row.get("response", "").strip()
        if not prompt or not response:
            continue

        model      = row.get("model", "").strip() or "uploaded"
        criteria   = row.get("criteria", "").strip()
        tokens_in  = _parse_int(row.get("tokens_in", ""), _estimate_tokens(prompt))
        tokens_out = _parse_int(row.get("tokens_out", ""), _estimate_tokens(response))
        latency_ms = _parse_float(row.get("latency_ms", ""), 0.0)
        cost_usd   = _parse_float(row.get("cost_usd", ""), 0.0)

        raw_rating = row.get("quality_rating", "").strip()
        quality_rating: Optional[float] = None
        if raw_rating:
            try:
                quality_rating = float(raw_rating)
            except ValueError:
                pass

        comp = Completion(
            prompt=prompt,
            response=response,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            source=source_id,
            timestamp=now,
        )
        parsed.append((comp, quality_rating, criteria))

    if not parsed:
        raise HTTPException(status_code=422, detail="No valid rows found (prompt and response must be non-empty).")

    completions = [c for c, _, _ in parsed]

    # Bulk insert, populate PKs
    db.add_all(completions)
    db.flush()

    # Compute evals for every row in one pass
    for comp, quality_rating, criteria in parsed:
        _compute_evals(db, comp.id, comp.prompt, comp.response, quality_rating, criteria)

    # Store upload metadata
    upload = Upload(
        source_id=source_id,
        filename=file.filename,
        row_count=len(completions),
        has_quality_rating=has_quality,
        has_model_column=has_model,
    )
    db.add(upload)
    db.commit()

    # Build summary metrics from what was just inserted
    eval_rows = (
        db.query(EvalResult.eval_type, func.avg(EvalResult.score).label("avg"))
        .join(Completion, EvalResult.completion_id == Completion.id)
        .filter(Completion.source == source_id)
        .group_by(EvalResult.eval_type)
        .all()
    )
    scores = {r.eval_type: round(r.avg, 4) for r in eval_rows}

    models_in_upload = (
        db.query(Completion.model, func.count(Completion.id).label("n"))
        .filter(Completion.source == source_id)
        .group_by(Completion.model)
        .all()
    )

    return {
        "source_id": source_id,
        "filename": file.filename,
        "row_count": len(completions),
        "columns_detected": header,
        "scores": scores,
        "models": [{"model": r.model, "count": r.n} for r in models_in_upload],
        "metrics_url": f"/api/v1/metrics/source/{source_id}",
    }


@router.get("/datasets")
def list_uploads(db: Session = Depends(get_db)):
    """List all uploaded datasets with their computed metrics."""
    uploads = db.query(Upload).order_by(Upload.created_at.desc()).all()

    result = []
    for u in uploads:
        eval_rows = (
            db.query(EvalResult.eval_type, func.avg(EvalResult.score).label("avg"))
            .join(Completion, EvalResult.completion_id == Completion.id)
            .filter(Completion.source == u.source_id)
            .group_by(EvalResult.eval_type)
            .all()
        )
        scores = {r.eval_type: round(r.avg, 4) for r in eval_rows}

        result.append({
            "id": u.id,
            "source_id": u.source_id,
            "filename": u.filename,
            "row_count": u.row_count,
            "has_quality_rating": u.has_quality_rating,
            "has_model_column": u.has_model_column,
            "created_at": u.created_at.isoformat(),
            "scores": scores,
            "metrics_url": f"/api/v1/metrics/source/{u.source_id}",
        })

    return result


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(upload_id: int, db: Session = Depends(get_db)):
    """Remove an uploaded dataset and all its completions/evals."""
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found.")

    # Delete evals first (FK constraint)
    comp_ids = [
        c.id for c in db.query(Completion.id)
        .filter(Completion.source == upload.source_id).all()
    ]
    if comp_ids:
        db.query(EvalResult).filter(EvalResult.completion_id.in_(comp_ids)).delete(
            synchronize_session=False
        )
        db.query(Completion).filter(Completion.source == upload.source_id).delete(
            synchronize_session=False
        )

    db.delete(upload)
    db.commit()
